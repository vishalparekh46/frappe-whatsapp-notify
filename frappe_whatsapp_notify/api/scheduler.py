import frappe
from frappe.utils import today

from frappe_whatsapp_notify.api.whatsapp import send_whatsapp_message


def send_overdue_payment_reminders():
    """Daily scheduled task: remind customers with overdue Sales Invoices."""
    overdue_invoices = frappe.get_all(
        "Sales Invoice",
        filters={
            "docstatus": 1,
            "outstanding_amount": [">", 0],
            "due_date": ["<", today()],
        },
        fields=["name", "customer", "outstanding_amount", "currency", "due_date"],
    )

    for inv in overdue_invoices:
        mobile = frappe.db.get_value("Customer", inv.customer, "mobile_no")
        if not mobile:
            continue

        message = (
            f"Dear {inv.customer},\n"
            f"This is a reminder that Invoice *{inv.name}* "
            f"for {inv.currency} {inv.outstanding_amount:,.2f} was due on {inv.due_date}.\n"
            f"Kindly arrange payment at your earliest convenience.\n"
            f"Thank you."
        )
        try:
            send_whatsapp_message(mobile, message)
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                f"WhatsApp reminder failed for {inv.name}",
            )
