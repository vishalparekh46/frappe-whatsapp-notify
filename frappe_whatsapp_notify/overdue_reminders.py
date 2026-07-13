"""
frappe_whatsapp_notify.overdue_reminders
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Daily scheduler job that scans for overdue Sales Invoices and sends
WhatsApp payment-reminder messages to customers via the notifications
module.

Wire it up in hooks.py::

    scheduler_events = {
        "daily": [
            "frappe_whatsapp_notify.overdue_reminders.send_overdue_reminders",
        ]
    }
"""

from datetime import date

import frappe

from frappe_whatsapp_notify.notifications import send_payment_reminder


def _get_overdue_invoices():
    """
    Return all outstanding submitted Sales Invoices whose due date is in
    the past.

    Returns a list of dicts with fields: name, customer, due_date,
    outstanding_amount, customer_name, contact_mobile, mobile_no, currency,
    grand_total, company, posting_date.
    """
    today = date.today().isoformat()
    return frappe.get_list(
        "Sales Invoice",
        filters={
            "docstatus": 1,
            "outstanding_amount": [">", 0],
            "due_date": ["<", today],
        },
        fields=[
            "name",
            "customer",
            "customer_name",
            "due_date",
            "outstanding_amount",
            "contact_mobile",
            "mobile_no",
            "currency",
            "grand_total",
            "company",
            "posting_date",
        ],
        order_by="due_date asc",
    )


def _days_overdue(due_date):
    """Return the number of calendar days an invoice is past its due date."""
    today = date.today()
    if hasattr(due_date, "date"):
        due = due_date.date()
    else:
        from datetime import datetime
        due = datetime.strptime(str(due_date), "%Y-%m-%d").date()
    delta = today - due
    return max(0, delta.days)


def send_overdue_reminders():
    """
    Entry point called by the Frappe daily scheduler.

    Fetches all overdue Sales Invoices, calculates how many days each is
    past its due date, and delegates to send_payment_reminder() for each
    one. Errors for individual invoices are logged and do not abort the
    loop.
    """
    invoices = _get_overdue_invoices()

    if not invoices:
        frappe.logger("whatsapp").info(
            "overdue_reminders: no overdue invoices found, nothing to send."
        )
        return

    frappe.logger("whatsapp").info(
        "overdue_reminders: processing {} overdue invoice(s).".format(len(invoices))
    )

    sent = 0
    failed = 0

    for inv_data in invoices:
        try:
            doc = frappe.get_doc("Sales Invoice", inv_data["name"])
            days = _days_overdue(inv_data["due_date"])
            send_payment_reminder(doc, days_overdue=days)
            sent += 1
        except Exception as exc:
            failed += 1
            frappe.log_error(
                "overdue_reminders: failed for {}: {}".format(inv_data["name"], exc),
                "WhatsApp Notify",
            )

    frappe.logger("whatsapp").info(
        "overdue_reminders: done. sent={}, failed={}.".format(sent, failed)
    )
