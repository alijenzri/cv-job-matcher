"""
Notification Service: handles async status updates and webhook notifications.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class NotificationService:
    async def send_email(self, recipient: str, message: str) -> bool:
        """Send email notification (placeholder — integrate with SendGrid/SES in prod)."""
        logger.info(f"📧 Email to {recipient}: {message}")
        return True

    async def notify_cv_processed(self, cv_id: str, status: str, filename: str):
        """Notify that a CV has been processed."""
        logger.info(f"📋 CV Notification — ID: {cv_id}, Status: {status}, File: {filename}")

    async def send_webhook(self, url: str, payload: dict) -> bool:
        """Send webhook notification for integrations (e.g., Slack, Teams)."""
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, timeout=10)
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Webhook failed to {url}: {e}")
            return False
