"""
frappe_whatsapp_notify.notifications
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
High-level helpers for sending WhatsApp notifications triggered by
ERPNext document events (Sales Invoice submission, payment reminders, etc.).

Usage example in hooks.py::

    doc_events = {
        "Sales Invoice": {
            "on_submit": "frappe_whatsapp_notify.notifications.send_invoice_notification",
        }
    }
"""

import frappe
from jinja2 import Template

from frappe_whatsapp_notify.scheduler import _send_with_retry
from frappe_whatsapp_notify.doctype.whatsapp_settings.whatsapp_settings import get_settings

# ---------------------------------------------------------------------------
# Message templates (plain-text Jinja2)
# ---------------------------------------------------------------------------

TEMPLATES = {
    "invoice": (
        "Dear {{ customer_name }},\n\n"
        "Your Tax Invoice *{{ invoice_no }}* dated {{ posting_date }} "
        "for *{{ currency }} {{ grand_total }}* has been generated.\n\n"
        "Due Date: {{ due_date }}\n"
        "Please make payment by the due date to avoid late charges.\n\n"
        "Thank you for your business!\n"
        "-- {{ company }}"
    ),
    "payment_reminder": (
        "Dear {{ customer_name }},\n\n"
        "This is a gentle reminder that Invoice *{{ invoice_no }}* "
        "for *{{ currency }} {{ outstanding_amount }}* was due on {{ due_date }}.\n\n"
        "The invoice is now *{{ days_overdue }} day(s) overdue*.\n"
        "Kindly arrange payment at the earliest.\n\n"
        "For queries, reply to this message.\n"
        "-- {{ company }}"
    ),
    "low_stock": (
        "Warning: *Low Stock Alert*\n\n"
        "Item: *{{ item_name }}* ({{ item_code }})\n"
        "Warehouse: {{ warehouse }}\n"
        "Current Stock: {{ actual_qty }} {{ uom }}\n"
        "Reorder Level: {{ reorder_level }} {{ uom }}\n\n"
        "Please raise a Purchase Order to replenish stock.\n"
        "-- {{ company }}"
    ),
}


def _render(template_key, context):
    """Render a named template with the supplied context dict."""
    raw = TEMPLATES.get(template_key, "")
    return Template(raw).render(**context)


def _get_mobile(doc):
    """
    Return the primary mobile number for the customer on doc.

    Tries doc.contact_mobile -> doc.mobile_no -> customer first contact.
    Returns None if no number is found.
    """
    mobile = getattr(doc, "contact_mobile", None) or getattr(doc, "mobile_no", None)
    if not mobile and getattr(doc, "customer", None):
        contacts = frappe.get_list(
            "Contact",
            filters={"link_doctype": "Customer", "link_name": doc.customer},
            fields=["mobile_no"],
            limit=1,
        )
        if contacts:
            mobile = contacts[0].get("mobile_no")
    return mobile or None


# ---------------------------------------------------------------------------
# Public notification functions
# ---------------------------------------------------------------------------


def send_invoice_notification(doc, method=None):
    """
    Send a WhatsApp message to the customer when a Sales Invoice is submitted.

    Hooked via doc_events["Sales Invoice"]["on_submit"].
    Silently skips if WhatsApp Settings are disabled or no mobile is found.
    """
    settings = get_settings()
    if not settings.is_enabled:
        return

    mobile = _get_mobile(doc)
    if not mobile:
        frappe.log_error(
            "send_invoice_notification: no mobile found for {}".format(doc.name),
            "WhatsApp Notify",
        )
        return

    message = _render(
        "invoice",
        {
            "customer_name": doc.customer_name,
            "invoice_no": doc.name,
            "posting_date": str(doc.posting_date),
            "currency": doc.currency,
            "grand_total": "{:,.2f}".format(doc.grand_total),
            "due_date": str(doc.due_date or "N/A"),
            "company": doc.company,
        },
    )

    try:
        _send_with_retry(mobile, message)
        frappe.logger("whatsapp").info(
            "Invoice notification sent for {} -> {}".format(doc.name, mobile)
        )
    except Exception as exc:
        frappe.log_error(
            "send_invoice_notification failed for {}: {}".format(doc.name, exc),
            "WhatsApp Notify",
        )


def send_payment_reminder(doc, days_overdue=0, method=None):
    """
    Send a WhatsApp payment reminder for an overdue Sales Invoice.

    Can be called manually or from a scheduled job:

        from frappe_whatsapp_notify.notifications import send_payment_reminder
        inv = frappe.get_doc("Sales Invoice", "SINV-0001")
        send_payment_reminder(inv, days_overdue=7)

    Silently skips if WhatsApp Settings are disabled or no mobile is found.
    """
    settings = get_settings()
    if not settings.is_enabled:
        return

    mobile = _get_mobile(doc)
    if not mobile:
        frappe.log_error(
            "send_payment_reminder: no mobile found for {}".format(doc.name),
            "WhatsApp Notify",
        )
        return

    message = _render(
        "payment_reminder",
        {
            "customer_name": doc.customer_name,
            "invoice_no": doc.name,
            "currency": doc.currency,
            "outstanding_amount": "{:,.2f}".format(doc.outstanding_amount),
            "due_date": str(doc.due_date or "N/A"),
            "days_overdue": days_overdue,
            "company": doc.company,
        },
    )

    try:
        _send_with_retry(mobile, message)
        frappe.logger("whatsapp").info(
            "Payment reminder sent for {} -> {} ({}d overdue)".format(
                doc.name, mobile, days_overdue
            )
        )
    except Exception as exc:
        frappe.log_error(
            "send_payment_reminder failed for {}: {}".format(doc.name, exc),
            "WhatsApp Notify",
        )
