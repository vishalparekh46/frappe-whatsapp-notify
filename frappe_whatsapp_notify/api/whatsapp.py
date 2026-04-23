import frappe
from twilio.rest import Client


def get_settings():
    """Fetch WhatsApp Settings from ERPNext."""
    settings = frappe.get_single("WhatsApp Settings")
    return settings


def send_whatsapp_message(to_number, message):
    """Send a WhatsApp message via Twilio."""
    settings = get_settings()
    if not settings.enabled:
        return

    client = Client(settings.account_sid, settings.get_password("auth_token"))
    client.messages.create(
        from_=f"whatsapp:{settings.from_number}",
        body=message,
        to=f"whatsapp:{to_number}",
    )


def send_sales_order_confirmation(doc, method):
    """Triggered on Sales Order submission."""
    customer = frappe.get_doc("Customer", doc.customer)
    mobile = customer.mobile_no
    if not mobile:
        return

    message = (
        f"Hi {doc.customer},\n"
        f"Your Sales Order *{doc.name}* has been confirmed.\n"
        f"Total: {doc.currency} {doc.grand_total:,.2f}\n"
        f"Thank you for your business!"
    )
    send_whatsapp_message(mobile, message)


def send_invoice_notification(doc, method):
    """Triggered on Sales Invoice submission."""
    customer = frappe.get_doc("Customer", doc.customer)
    mobile = customer.mobile_no
    if not mobile:
        return

    message = (
        f"Hi {doc.customer},\n"
        f"Invoice *{doc.name}* for {doc.currency} {doc.grand_total:,.2f} has been raised.\n"
        f"Due Date: {doc.due_date}\n"
        f"Please make payment at your earliest convenience."
    )
    send_whatsapp_message(mobile, message)


def send_payment_receipt(doc, method):
    """Triggered on Payment Entry submission."""
    customer_name = doc.party
    mobile = frappe.db.get_value("Customer", customer_name, "mobile_no")
    if not mobile:
        return

    message = (
        f"Hi {customer_name},\n"
        f"We have received your payment of {doc.paid_amount:,.2f} {doc.paid_to_account_currency}.\n"
        f"Payment Reference: *{doc.name}*\n"
        f"Thank you!"
    )
    send_whatsapp_message(mobile, message)
