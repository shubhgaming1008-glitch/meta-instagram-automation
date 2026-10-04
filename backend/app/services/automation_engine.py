"""
AutomationEngine — executes automation flows node by node.

Entry point: execute_job(job_id)
The engine loads the job, resolves the automation flow graph,
and walks through nodes from the trigger, executing each one.
"""
import random
from datetime import datetime, timedelta, timezone
from typing import Optional

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.automation import Automation
from app.models.job import Job, JobAttempt
from app.models.log import ExecutionLog
from app.models.workflow import WorkflowEdge, WorkflowNode
from app.services.condition_engine import ConditionEngine
from app.services.keyword_engine import match_trigger_config

log = structlog.get_logger()


class AutomationEngine:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def execute_job(self, job_id: str):
        """Main entry point for executing an automation job."""
        job = await self._get_job(job_id)
        if not job:
            log.error("Job not found", job_id=job_id)
            return

        if job.status not in ("pending", "retrying"):
            log.warning("Job not in executable state", job_id=job_id, status=job.status)
            return

        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        await self.db.flush()

        try:
            automation = await self._get_automation(job.automation_id)
            if not automation or automation.status != "active":
                await self._fail_job(job, "Automation not active")
                return

            # Build node graph
            nodes = await self._get_nodes(automation.id)
            edges = await self._get_edges(automation.id)

            node_map = {n.node_id_in_flow: n for n in nodes}
            edge_map = self._build_edge_map(edges)

            # Find trigger node (starting point)
            trigger_node = next(
                (n for n in nodes if n.node_type == "trigger"), None
            )
            if not trigger_node:
                await self._fail_job(job, "No trigger node found in flow")
                return

            context = job.execution_context or {}
            context["job_id"] = job_id
            context["automation_id"] = automation.id

            # Walk the flow
            await self._walk_flow(
                job=job,
                current_node=trigger_node,
                node_map=node_map,
                edge_map=edge_map,
                context=context,
                automation=automation,
            )

            job.status = "completed"
            job.completed_at = datetime.now(timezone.utc)
            job.execution_context = context
            await self._log(job, "info", "system", "Job completed successfully")

        except Exception as e:
            log.exception("Job execution failed", job_id=job_id, error=str(e))
            await self._fail_job(job, str(e))

        await self.db.commit()

    async def _walk_flow(
        self,
        job: Job,
        current_node: WorkflowNode,
        node_map: dict,
        edge_map: dict,
        context: dict,
        automation: Automation,
    ):
        """Recursively walk the flow graph, executing each node."""
        visited = set()

        node = current_node
        while node and node.node_id_in_flow not in visited:
            visited.add(node.node_id_in_flow)
            job.current_node_id = node.node_id_in_flow

            await self._log(job, "info", node.node_type, f"Executing node: {node.node_type}", node_id=node.node_id_in_flow)

            # Execute the node
            result = await self._execute_node(job, node, context, automation)

            # Log attempt
            attempt = JobAttempt(
                job_id=job.id,
                attempt_number=job.retry_count,
                node_id=node.node_id_in_flow,
                started_at=datetime.now(timezone.utc),
                completed_at=datetime.now(timezone.utc),
                status=result.get("status", "completed"),
                result=result,
            )
            self.db.add(attempt)
            await self.db.flush()

            if result.get("status") == "error":
                await self._log(job, "error", node.node_type, result.get("error", "Unknown error"), node_id=node.node_id_in_flow)
                raise RuntimeError(result.get("error", "Node execution failed"))

            if result.get("status") == "stop":
                break

            # Determine next node
            handle = result.get("handle", "default")
            next_node_id = self._get_next_node(node.node_id_in_flow, edge_map, handle)

            if not next_node_id:
                break  # End of flow

            node = node_map.get(next_node_id)

    async def _execute_node(self, job: Job, node: WorkflowNode, context: dict, automation: Automation) -> dict:
        """Dispatch node execution by type."""
        config = node.config or {}
        ntype = node.node_type

        if ntype == "trigger":
            return {"status": "completed", "handle": "default"}

        if ntype == "end":
            return {"status": "stop"}

        if ntype == "message":
            return await self._exec_message(job, config, context, automation)

        if ntype == "comment_reply":
            return await self._exec_comment_reply(job, config, context, automation)

        if ntype == "condition":
            passed = ConditionEngine.evaluate(config.get("condition", {}), context)
            return {"status": "completed", "handle": "yes" if passed else "no"}

        if ntype == "delay":
            return await self._exec_delay(job, config, context)

        if ntype == "tag":
            return await self._exec_tag(job, config, context, add=True)

        if ntype == "remove_tag":
            return await self._exec_tag(job, config, context, add=False)

        if ntype == "randomizer":
            return self._exec_randomizer(config)

        if ntype == "follow_check":
            return self._exec_follow_check(config, context)

        if ntype == "link":
            return await self._exec_link(job, config, context, automation)

        if ntype == "collect_email":
            return await self._exec_collect_email(job, config, context, automation)

        if ntype == "start_automation":
            return await self._exec_start_automation(config, context)

        log.warning("Unknown node type", node_type=ntype)
        return {"status": "completed", "handle": "default"}

    async def _exec_message(self, job: Job, config: dict, context: dict, automation: Automation) -> dict:
        """Send a DM message."""
        from app.services.messaging_provider import MessagingProvider
        provider = MessagingProvider()
        result = await provider.send_message(
            ig_account_id=automation.ig_account_id,
            contact_id=job.contact_id,
            message_config=config,
            context=context,
        )
        context["last_message_sent"] = True
        return result

    async def _exec_comment_reply(self, job: Job, config: dict, context: dict, automation: Automation) -> dict:
        """Reply publicly to a comment."""
        from app.services.messaging_provider import MessagingProvider
        provider = MessagingProvider()
        comment_id = context.get("trigger_comment_id")
        if not comment_id:
            return {"status": "completed", "handle": "default"}  # No comment to reply to
        result = await provider.reply_to_comment(
            ig_account_id=automation.ig_account_id,
            comment_id=comment_id,
            message_config=config,
            context=context,
        )
        return result

    async def _exec_delay(self, job: Job, config: dict, context: dict) -> dict:
        """Schedule the job to resume after a delay."""
        delay_unit = config.get("unit", "minutes")
        delay_value = config.get("value", 5)
        unit_map = {"seconds": 1, "minutes": 60, "hours": 3600, "days": 86400}
        seconds = delay_value * unit_map.get(delay_unit, 60)

        scheduled_at = datetime.now(timezone.utc) + timedelta(seconds=seconds)
        job.scheduled_at = scheduled_at
        job.status = "pending"
        await self._log(job, "info", "delay", f"Job paused for {delay_value} {delay_unit}")
        return {"status": "stop"}  # Stop current execution; Celery beat will reschedule

    async def _exec_tag(self, job: Job, config: dict, context: dict, add: bool) -> dict:
        """Add or remove a tag from the contact."""
        from app.models.tag import ContactTag, Tag
        from datetime import datetime, timezone
        tag_name = config.get("tag_name")
        if not tag_name or not job.contact_id:
            return {"status": "completed", "handle": "default"}

        tag_result = await self.db.execute(
            select(Tag).where(Tag.name == tag_name)
        )
        tag = tag_result.scalar_one_or_none()

        if add and tag:
            existing = await self.db.execute(
                select(ContactTag).where(
                    ContactTag.contact_id == job.contact_id,
                    ContactTag.tag_id == tag.id,
                )
            )
            if not existing.scalar_one_or_none():
                ct = ContactTag(
                    contact_id=job.contact_id,
                    tag_id=tag.id,
                    added_at=datetime.now(timezone.utc),
                    added_by_automation_id=job.automation_id,
                )
                self.db.add(ct)
                tags = context.get("contact_tags", [])
                tags.append(tag_name)
                context["contact_tags"] = tags
        elif not add and tag:
            existing = await self.db.execute(
                select(ContactTag).where(
                    ContactTag.contact_id == job.contact_id,
                    ContactTag.tag_id == tag.id,
                )
            )
            ct = existing.scalar_one_or_none()
            if ct:
                await self.db.delete(ct)
                context["contact_tags"] = [t for t in context.get("contact_tags", []) if t != tag_name]

        return {"status": "completed", "handle": "default"}

    def _exec_randomizer(self, config: dict) -> dict:
        """Select a branch based on weighted probabilities."""
        branches = config.get("branches", [])
        if not branches:
            return {"status": "completed", "handle": "default"}
        weights = [b.get("weight", 1) for b in branches]
        chosen = random.choices(branches, weights=weights, k=1)[0]
        return {"status": "completed", "handle": chosen.get("handle", "default")}

    def _exec_follow_check(self, config: dict, context: dict) -> dict:
        """
        Follow gate check.
        FOLLOW_VERIFICATION is not available via Meta API for standard accounts.
        We use the self-reported confirmation flow.
        """
        follow_confirmed = context.get("follow_confirmed", False)
        if follow_confirmed:
            return {"status": "completed", "handle": "yes"}
        return {"status": "completed", "handle": "no"}

    async def _exec_link(self, job: Job, config: dict, context: dict, automation: Automation) -> dict:
        """Send a protected or direct link."""
        from app.services.link_provider import LinkProvider
        provider = LinkProvider(self.db)
        result = await provider.deliver_link(
            link_id=config.get("link_id"),
            contact_id=job.contact_id,
            automation_id=automation.id,
            campaign_id=automation.campaign_id,
            context=context,
        )
        return result

    async def _exec_collect_email(self, job: Job, config: dict, context: dict, automation: Automation) -> dict:
        """Send an email collection message and wait for user input."""
        # This node sends a prompt and pauses; the DM reply handler will resume
        from app.services.messaging_provider import MessagingProvider
        provider = MessagingProvider()
        await provider.send_message(
            ig_account_id=automation.ig_account_id,
            contact_id=job.contact_id,
            message_config={
                "text": config.get("prompt", "Please enter your email address:"),
                "type": "text",
            },
            context=context,
        )
        context["waiting_for"] = "email"
        job.execution_context = context
        return {"status": "stop"}  # Pause; resume when user replies

    async def _exec_start_automation(self, config: dict, context: dict) -> dict:
        """Trigger another automation."""
        target_automation_id = config.get("automation_id")
        if target_automation_id and target_automation_id != context.get("automation_id"):
            from app.tasks.automation_tasks import trigger_automation
            trigger_automation.delay(
                automation_id=target_automation_id,
                contact_id=context.get("contact_id"),
                trigger_context=context,
            )
        return {"status": "completed", "handle": "default"}

    # ── Graph helpers ─────────────────────────────────────────────
    def _build_edge_map(self, edges: list[WorkflowEdge]) -> dict:
        """Build {source_node_id: [(target_node_id, handle)]} map."""
        edge_map = {}
        for edge in edges:
            if edge.source_node_id not in edge_map:
                edge_map[edge.source_node_id] = []
            edge_map[edge.source_node_id].append({
                "target": edge.target_node_id,
                "handle": edge.source_handle or "default",
            })
        return edge_map

    def _get_next_node(self, current_id: str, edge_map: dict, handle: str) -> Optional[str]:
        edges = edge_map.get(current_id, [])
        # Prefer edge matching handle
        for edge in edges:
            if edge["handle"] == handle:
                return edge["target"]
        # Fallback: first edge
        if edges:
            return edges[0]["target"]
        return None

    # ── DB helpers ────────────────────────────────────────────────
    async def _get_job(self, job_id: str) -> Optional[Job]:
        result = await self.db.execute(select(Job).where(Job.id == job_id))
        return result.scalar_one_or_none()

    async def _get_automation(self, automation_id: str) -> Optional[Automation]:
        result = await self.db.execute(select(Automation).where(Automation.id == automation_id))
        return result.scalar_one_or_none()

    async def _get_nodes(self, automation_id: str) -> list[WorkflowNode]:
        result = await self.db.execute(
            select(WorkflowNode).where(WorkflowNode.automation_id == automation_id)
        )
        return list(result.scalars().all())

    async def _get_edges(self, automation_id: str) -> list[WorkflowEdge]:
        result = await self.db.execute(
            select(WorkflowEdge).where(WorkflowEdge.automation_id == automation_id)
        )
        return list(result.scalars().all())

    async def _fail_job(self, job: Job, error: str):
        job.status = "failed"
        job.error = error
        job.completed_at = datetime.now(timezone.utc)
        await self._log(job, "failed", "system", f"Job failed: {error}")
        await self.db.flush()

    async def _log(self, job: Job, level: str, category: str, message: str, node_id: Optional[str] = None):
        entry = ExecutionLog(
            job_id=job.id,
            automation_id=job.automation_id,
            contact_id=job.contact_id,
            level=level,
            category=category,
            node_id=node_id,
            message=message,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(entry)
        await self.db.flush()
