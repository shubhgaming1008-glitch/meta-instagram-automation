"""
Models package — import all models here so SQLAlchemy registers them.
"""
from app.models.user import User  # noqa
from app.models.instagram_account import InstagramAccount  # noqa
from app.models.campaign import Campaign  # noqa
from app.models.automation import Automation, AutomationVersion  # noqa
from app.models.workflow import WorkflowNode, WorkflowEdge  # noqa
from app.models.contact import Contact  # noqa
from app.models.tag import Tag, ContactTag  # noqa
from app.models.link import Link, LinkClick  # noqa
from app.models.message import Message, Conversation  # noqa
from app.models.event import WebhookEvent  # noqa
from app.models.job import Job, JobAttempt  # noqa
from app.models.log import ExecutionLog  # noqa
