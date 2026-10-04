"""
FollowerVerificationProvider — compliant follow gate implementation.

Meta's Instagram API does not expose a reliable real-time follower verification
endpoint for standard accounts. This provider implements the compliant fallback:

1. Self-reported confirmation: User clicks "I've Followed" button
2. The provider returns UNAVAILABLE to document that cryptographic verification
   is not possible, and the system proceeds on user confirmation.

If/when Meta adds a supported follow-check API, this provider can be upgraded
to return VERIFIED based on an actual API call.
"""
from enum import Enum
from typing import Optional

import structlog

log = structlog.get_logger()


class VerificationResult(str, Enum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified"
    UNAVAILABLE = "unavailable"  # API capability not available


class FollowerVerificationProvider:
    """
    Interface for follow verification.
    Current implementation: Self-reported (always returns UNAVAILABLE from API).
    """

    @classmethod
    async def verify(
        cls,
        ig_account_id: str,
        follower_ig_user_id: str,
        account_ig_user_id: str,
    ) -> VerificationResult:
        """
        Attempt to verify if follower_ig_user_id follows account_ig_user_id.

        Current capability: NOT AVAILABLE via Meta API for standard accounts.
        Returns UNAVAILABLE to signal that the UI should use self-reported confirmation.
        """
        log.info(
            "Follow verification requested — API not available, returning UNAVAILABLE",
            follower=follower_ig_user_id,
            account=account_ig_user_id,
        )
        # TODO: If Meta adds a supported endpoint, implement it here:
        # resp = await meta_client.check_follower(account_ig_user_id, follower_ig_user_id)
        # if resp.is_following: return VerificationResult.VERIFIED
        return VerificationResult.UNAVAILABLE

    @classmethod
    def get_capability_description(cls) -> dict:
        return {
            "available": False,
            "reason": (
                "Instagram API does not provide real-time follower verification "
                "for standard accounts. The follow gate uses a self-reported "
                "confirmation button ('I've Followed'). This is compliant behavior."
            ),
            "fallback": "self_reported_confirmation",
        }
