# Copyright (c) 2024, Aavatto and contributors
# For license information, please see license.txt
"""
Whitelisted API endpoints for the WhatsApp Log DocType.

These are called from the ERPNext desk via frappe.call() to display
recent WhatsApp notification history and statistics.
"""

import frappe
from frappe.utils import add_days, today


@frappe.whitelist()
def get_recent_logs(limit=20, status=None, triggered_by=None):
    """Return recent WhatsApp Log entries for the desk widget.

    Args:
        limit (int): Max number of records to return (default 20, max 200).
        status (str|None): Filter by status — "Sent", "Failed", or "Skipped".
        triggered_by (str|None): Filter by trigger source.

    Returns:
        list[dict]: Log entries ordered by sent_on DESC.
    """
    limit = min(int(limit), 200)
    filters = {}
    if status:
        filters["status"] = status
    if triggered_by:
        filters["triggered_by"] = triggered_by

    return frappe.get_all(
        "WhatsApp Log",
        filters=filters,
        fields=[
            "name",
            "document_type",
            "document_name",
            "mobile_number",
            "status",
            "triggered_by",
            "sent_on",
            "message_preview",
            "error_message",
        ],
        order_by="sent_on desc",
        limit=limit,
    )


@frappe.whitelist()
def get_log_summary(days=7):
    """Return send/fail/skip counts for the last N days.

    Args:
        days (int): Number of days to look back (default 7).

    Returns:
        dict: Keys "sent", "failed", "skipped", "total", "period_days".
    """
    days = int(days)
    cutoff = add_days(today(), -days)

    rows = frappe.db.get_all(
        "WhatsApp Log",
        filters={"sent_on": [">=", cutoff]},
        fields=["status"],
    )

    counts = {"Sent": 0, "Failed": 0, "Skipped": 0}
    for row in rows:
        if row.status in counts:
            counts[row.status] += 1

    return {
        "sent": counts["Sent"],
        "failed": counts["Failed"],
        "skipped": counts["Skipped"],
        "total": len(rows),
        "period_days": days,
    }


@frappe.whitelist()
def get_failed_logs(limit=50):
    """Return unresolved failed WhatsApp Log entries.

    Useful for a desk alert widget showing messages that need attention.

    Args:
        limit (int): Max number of records (default 50).

    Returns:
        list[dict]: Failed log entries with error details.
    """
    limit = min(int(limit), 200)
    return frappe.get_all(
        "WhatsApp Log",
        filters={"status": "Failed"},
        fields=[
            "name",
            "document_type",
            "document_name",
            "mobile_number",
            "triggered_by",
            "sent_on",
            "error_message",
        ],
        order_by="sent_on desc",
        limit=limit,
    )


@frappe.whitelist()
def purge_old_logs(days=None):
    """Manually trigger a log purge from the desk.

    Args:
        days (int|None): Retention days. Defaults to whatsapp_log_retention_days
                         site config or 90 days.

    Returns:
        dict: Number of deleted records.
    """
    frappe.only_for("System Manager")
    from frappe_whatsapp_notify.doctype.whatsapp_log.whatsapp_log import WhatsAppLog

    deleted = WhatsAppLog.purge_old_logs(days=days)
    frappe.msgprint(
        f"Purged {deleted} old WhatsApp Log entries.",
        alert=True,
        indicator="green" if deleted else "blue",
    )
    return {"deleted": deleted}
