import frappe
from frappe.utils import today, add_days, nowdate
from frappe_whatsapp_notify.api.whatsapp import send_whatsapp_message
from frappe_whatsapp_notify.utils import normalise_phone, format_currency, TEMPLATES, build_message

# Configurable batch size – override via Site Config if needed
BATCH_SIZE = frappe.conf.get("whatsapp_reminder_batch_size", 50)
MAX_RETRIES = 2


def send_overdue_payment_reminders():
    """Daily scheduled task: remind customers with overdue Sales Invoices.

    Runs via hooks.py scheduler_events → daily.
    Fetches all submitted, unpaid invoices where due_date < today,
    then sends a WhatsApp reminder to the customer's mobile number.
    Failed sends are retried up to MAX_RETRIES times before logging.
    """
    settings = frappe.get_single("WhatsApp Settings")
    if not settings.enabled:
        frappe.logger("whatsapp").info("WhatsApp reminders skipped – app disabled.")
        return

    overdue_invoices = frappe.get_all(
        "Sales Invoice",
        filters={
            "docstatus": 1,
            "outstanding_amount": [">", 0],
            "due_date": ["<", today()],
        },
        fields=["name", "customer", "outstanding_amount", "currency", "due_date"],
        limit=BATCH_SIZE,
        order_by="due_date asc",
    )

    if not overdue_invoices:
        frappe.logger("whatsapp").info("No overdue invoices found for WhatsApp reminders.")
        return

    sent_count = 0
    failed_count = 0

    for inv in overdue_invoices:
        mobile = _get_customer_mobile(inv.customer)
        if not mobile:
            frappe.logger("whatsapp").warning(
                f"Skipping overdue reminder for {inv.name} – no mobile number for {inv.customer}"
            )
            continue

        normalized = normalise_phone(mobile)
        if not normalized:
            frappe.logger("whatsapp").warning(
                f"Skipping {inv.name} – invalid phone number '{mobile}' for {inv.customer}"
            )
            continue

        message = build_message(
            TEMPLATES["overdue_reminder"],
            customer=inv.customer,
            name=inv.name,
            currency=inv.currency,
            outstanding_amount=format_currency(inv.outstanding_amount, inv.currency),
            due_date=inv.due_date,
        )

        success = _send_with_retry(normalized, message, inv.name)
        if success:
            sent_count += 1
        else:
            failed_count += 1

    frappe.logger("whatsapp").info(
        f"Overdue reminders complete. Sent: {sent_count}, Failed: {failed_count}, "
        f"Total: {len(overdue_invoices)}"
    )

    if failed_count > 0:
        frappe.log_error(
            title="WhatsApp Overdue Reminder Failures",
            message=f"{failed_count} reminders could not be sent. Check frappe.log for details.",
        )


def _send_with_retry(mobile: str, message: str, doc_name: str) -> bool:
    """Attempt to send a WhatsApp message with up to MAX_RETRIES retries.

    Returns True if the message was sent successfully, False otherwise.
    """
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            send_whatsapp_message(mobile, message)
            return True
        except Exception as e:
            last_error = e
            frappe.logger("whatsapp").warning(
                f"Attempt {attempt}/{MAX_RETRIES} failed for {doc_name}: {e}"
            )

    frappe.log_error(
        title=f"WhatsApp Reminder Failed – {doc_name}",
        message=f"All {MAX_RETRIES} attempts failed.\nLast error: {last_error}",
    )
    return False


def _get_customer_mobile(customer: str) -> str | None:
    """Retrieve the primary mobile number for a customer.

    Checks Customer.mobile_no first, then falls back to the first
    Contact linked to the customer.
    """
    mobile = frappe.db.get_value("Customer", customer, "mobile_no")
    if mobile:
        return mobile

    # Fallback: linked Contact
    contact_name = frappe.db.get_value(
        "Dynamic Link",
        {"link_doctype": "Customer", "link_name": customer, "parenttype": "Contact"},
        "parent",
    )
    if contact_name:
        return frappe.db.get_value("Contact", contact_name, "mobile_no")

    return None
