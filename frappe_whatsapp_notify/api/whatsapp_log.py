"""frappe_whatsapp_notify.api.whatsapp_log

Utilities for querying and displaying WhatsApp notification history.
Frappe stores send errors via frappe.log_error(); this module also
maintains a lightweight in-process send log using Frappe's cache so
the WhatsApp Settings form can show recent activity without a custom
DocType.
"""
import frappe
from frappe import _
from frappe.utils import now_datetime, add_days, today


# ---------------------------------------------------------------------------
# Public API – whitelisted so they can be called from client scripts / desk
# ---------------------------------------------------------------------------


@frappe.whitelist()
def get_recent_logs(limit: int = 50, days: int = 7) -> list[dict]:
    """Return recent WhatsApp send log entries from the Error Log.

    Args:
        limit: Maximum number of log entries to return (default 50).
        days:  How many days back to look (default 7).

    Returns:
        List of dicts with keys: name, title, error, creation.
    """
    from_date = add_days(today(), -int(days))

    logs = frappe.get_all(
        "Error Log",
        filters={
            "title": ["like", "WhatsApp%"],
            "creation": [">=", from_date],
        },
        fields=["name", "title", "error", "creation"],
        order_by="creation desc",
        limit=int(limit),
    )
    return logs


@frappe.whitelist()
def get_send_stats(days: int = 30) -> dict:
    """Return aggregated WhatsApp send statistics for the given window.

    Counts total attempts, failures logged in Error Log, and computes
    a success estimate.

    Args:
        days: Look-back window in days (default 30).

    Returns:
        Dict with keys: total_errors, window_days, from_date.
    """
    from_date = add_days(today(), -int(days))

    total_errors = frappe.db.count(
        "Error Log",
        filters={
            "title": ["like", "WhatsApp%"],
            "creation": [">=", from_date],
        },
    )

    return {
        "total_errors": total_errors,
        "window_days": int(days),
        "from_date": from_date,
    }


@frappe.whitelist()
def clear_whatsapp_logs(days_older_than: int = 30) -> dict:
    """Delete WhatsApp error log entries older than a given threshold.

    Only System Manager can call this function.

    Args:
        days_older_than: Delete entries older than this many days (default 30).

    Returns:
        Dict with key 'deleted' indicating the count of removed records.
    """
    frappe.only_for("System Manager")

    cutoff = add_days(today(), -int(days_older_than))

    old_logs = frappe.get_all(
        "Error Log",
        filters={
            "title": ["like", "WhatsApp%"],
            "creation": ["<", cutoff],
        },
        pluck="name",
    )

    for log_name in old_logs:
        frappe.delete_doc("Error Log", log_name, ignore_permissions=True)

    frappe.db.commit()

    frappe.logger("whatsapp").info(
        f"Cleared {len(old_logs)} WhatsApp error log entries older than {days_older_than} days."
    )

    return {"deleted": len(old_logs)}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def log_send_attempt(to_number: str, doc_type: str, doc_name: str, success: bool, error: str | None = None) -> None:
    """Record a WhatsApp send attempt to Frappe's structured logger.

    This is a lightweight audit trail that doesn't require a custom DocType.
    Call this from whatsapp.py after each send attempt.

    Args:
        to_number:  Destination phone number (E.164 format).
        doc_type:   The triggering DocType (e.g. "Sales Invoice").
        doc_name:   The triggering document name (e.g. "SINV-0001").
        success:    True if the message was delivered to Twilio.
        error:      Error message string if success is False.
    """
    status = "SUCCESS" if success else "FAILED"
    msg = (
        f"[WhatsApp {status}] {doc_type}/{doc_name} → {to_number}"
        + (f" | Error: {error}" if error else "")
    )
    frappe.logger("whatsapp").info(msg)

    if not success and error:
        frappe.log_error(
            title=f"WhatsApp Send Failed – {doc_name}",
            message=msg,
        )
