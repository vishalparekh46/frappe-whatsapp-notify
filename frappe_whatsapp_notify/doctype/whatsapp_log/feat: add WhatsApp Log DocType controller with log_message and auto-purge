"""frappe_whatsapp_notify.doctype.whatsapp_log.whatsapp_log

Controller for the WhatsApp Log DocType.

WhatsApp Log persists a record of every message send attempt so that
admins can review history, debug failures, and track delivery rates
directly from the ERPNext desk – without relying on Frappe Error Log.
"""
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import now_datetime, add_days, today

# Keep at most this many days of log data; older entries auto-purge
LOG_RETENTION_DAYS = frappe.conf.get("whatsapp_log_retention_days", 90)


class WhatsAppLog(Document):
    """WhatsApp Log document controller."""

    # ------------------------------------------------------------------
    # Lifecycle hooks
    # ------------------------------------------------------------------

    def before_insert(self):
        """Set sent_on timestamp if not already provided."""
        if not self.sent_on:
            self.sent_on = now_datetime()

    def validate(self):
        """Truncate message_preview to 500 characters to avoid DB overflow."""
        if self.message_preview and len(self.message_preview) > 500:
            self.message_preview = self.message_preview[:497] + "..."

    # ------------------------------------------------------------------
    # Class-level helpers (callable without an instance)
    # ------------------------------------------------------------------

    @classmethod
    def log_message(
        cls,
        *,
        document_type: str,
        document_name: str,
        mobile_number: str,
        message: str,
        status: str,
        triggered_by: str = "Manual",
        error_message: str | None = None,
    ) -> "WhatsAppLog":
        """Create and insert a new WhatsApp Log entry.

        Args:
            document_type:  The DocType that triggered the notification.
            document_name:  The document name (e.g. "SINV-0001").
            mobile_number:  Destination phone number in E.164 format.
            message:        Full message text (truncated to 500 chars in validate).
            status:         One of "Sent", "Failed", "Skipped".
            triggered_by:   One of "Sales Order", "Sales Invoice", "Payment Entry",
                            "Scheduler", "Manual".
            error_message:  Error string if status is "Failed".

        Returns:
            The newly created WhatsAppLog document.
        """
        settings = frappe.get_cached_doc("WhatsApp Settings")
        if not settings.get("log_messages", True):
            # Logging disabled in settings – return a dummy doc without saving
            return frappe.new_doc("WhatsApp Log")

        doc = frappe.new_doc("WhatsApp Log")
        doc.document_type = document_type
        doc.document_name = document_name
        doc.mobile_number = mobile_number
        doc.message_preview = message
        doc.status = status
        doc.triggered_by = triggered_by
        doc.error_message = error_message or ""
        doc.sent_on = now_datetime()
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        return doc

    @classmethod
    def purge_old_logs(cls, days: int | None = None) -> int:
        """Delete WhatsApp Log entries older than *days* days.

        Intended to be called from a scheduled task (e.g. weekly).

        Args:
            days: Retention window in days. Falls back to LOG_RETENTION_DAYS
                  which reads from site config (default 90).

        Returns:
            Number of records deleted.
        """
        retention = days or LOG_RETENTION_DAYS
        cutoff = add_days(today(), -int(retention))

        old_logs = frappe.get_all(
            "WhatsApp Log",
            filters={"sent_on": ["<", cutoff]},
            pluck="name",
        )

        for log_name in old_logs:
            frappe.delete_doc("WhatsApp Log", log_name, ignore_permissions=True)

        if old_logs:
            frappe.db.commit()
            frappe.logger("whatsapp").info(
                f"Purged {len(old_logs)} WhatsApp Log entries older than {retention} days."
            )

        return len(old_logs)

    @classmethod
    def get_recent_summary(cls, limit: int = 20) -> list[dict]:
        """Return a brief summary of recent log entries for the Settings form.

        Args:
            limit: Max entries to return (default 20).

        Returns:
            List of dicts with: name, document_type, document_name,
            mobile_number, status, sent_on.
        """
        return frappe.get_all(
            "WhatsApp Log",
            fields=[
                "name",
                "document_type",
                "document_name",
                "mobile_number",
                "status",
                "triggered_by",
                "sent_on",
            ],
            order_by="sent_on desc",
            limit=limit,
        )
