"""
CapabilityService — dynamically evaluates what features are available
for a given Instagram account based on its permissions and account type.

This prevents the UI from showing features the API cannot support.
"""
from dataclasses import dataclass
from typing import Optional

from app.models.instagram_account import InstagramAccount


@dataclass
class Capability:
    enabled: bool
    reason: str
    permission_required: Optional[str] = None
    account_type_required: Optional[str] = None


class CapabilityService:
    """
    Evaluate the capability matrix for a connected Instagram account.
    Returns a dict of capability_name → Capability details.
    """

    REQUIRED_PERMISSIONS = {
        "COMMENT_TRIGGER": "instagram_manage_comments",
        "DM_SEND": "instagram_manage_messages",
        "STORY_REPLY_TRIGGER": "instagram_manage_messages",
        "LIVE_COMMENTS": "instagram_manage_comments",
    }

    @classmethod
    def evaluate(cls, account: InstagramAccount) -> dict:
        permissions = set((account.permissions or {}).keys())
        account_type = (account.ig_account_type or "").lower()

        caps = {}

        # Comment triggers
        caps["COMMENT_TRIGGER"] = cls._check_permission(
            permissions, "instagram_manage_comments",
            "Comment triggers via Instagram API",
        )

        # DM sending
        caps["DM_SEND"] = cls._check_permission(
            permissions, "instagram_manage_messages",
            "Send DMs via Instagram Messaging API",
        )

        # Story reply trigger
        caps["STORY_REPLY_TRIGGER"] = cls._check_permission(
            permissions, "instagram_manage_messages",
            "Story reply automation",
        )

        # Story mention trigger
        caps["STORY_MENTION_TRIGGER"] = cls._check_permission(
            permissions, "instagram_manage_messages",
            "Story mention automation",
        )

        # Live comments
        caps["LIVE_COMMENTS"] = cls._check_permission(
            permissions, "instagram_manage_comments",
            "Live comment automation",
            extra_check=account_type in ("business", "creator"),
            extra_reason="Requires Business or Creator account",
        )

        # Follow verification — NOT available via standard API
        caps["FOLLOW_VERIFICATION"] = Capability(
            enabled=False,
            reason=(
                "Instagram API does not provide real-time follower verification. "
                "The follow gate uses a self-reported confirmation flow. "
                "This is documented behavior — not a bug."
            ),
            permission_required=None,
        )

        # Follow-based DM trigger
        caps["FOLLOW_TO_DM"] = Capability(
            enabled=False,
            reason="Meta does not currently expose follow events via webhook for standard accounts.",
            permission_required="instagram_manage_messages",
        )

        # Webhook
        caps["WEBHOOK"] = Capability(
            enabled=account.webhook_verified,
            reason="Webhook verified" if account.webhook_verified else "Webhook not yet verified",
        )

        return {k: v.__dict__ for k, v in caps.items()}

    @classmethod
    def _check_permission(
        cls,
        permissions: set,
        required_permission: str,
        description: str,
        extra_check: bool = True,
        extra_reason: str = "",
    ) -> Capability:
        has_permission = required_permission in permissions
        if has_permission and extra_check:
            return Capability(
                enabled=True,
                reason=f"{description} — available",
                permission_required=required_permission,
            )
        if not has_permission:
            return Capability(
                enabled=False,
                reason=f"Missing permission: {required_permission}",
                permission_required=required_permission,
            )
        return Capability(
            enabled=False,
            reason=extra_reason or "Account type not eligible",
            permission_required=required_permission,
        )

    @classmethod
    def is_capable(cls, account: InstagramAccount, capability_name: str) -> bool:
        caps = cls.evaluate(account)
        return caps.get(capability_name, {}).get("enabled", False)
