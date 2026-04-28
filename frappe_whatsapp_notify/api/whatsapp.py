import frappe
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException


def get_settings():
    """Fetch WhatsApp Settings from ERPNext."""
    settings = frappe.get_single("WhatsApp Settings")
    if not settings.enabled:
        frappe.logger().debug("WhatsApp notifications are disabled.")
    return settings


def send_whatsapp_message(to_number, message):
    """Send a WhatsApp message via Twilio with error handling."""
    settings = get_settings()
    if not settings.enabled:
        return

    if not to_number:
        frappe.logger().warning("WhatsApp: No phone number provided, skipping.")
        return

    # Normalise number — ensure it starts with +
    if not to_number.startswith("+"):
        to_number = "+" + to_number.strip()

    try:
        client = Client(settings.account_sid, settings.get_password("auth_token"))
        msg = client.messages.create(
            from_=f"whatsapp:{settings.from_number}",
            body=message,
            to=f"whatsapp:{to_number}",
        )
        frappe.logger().info(f"WhatsApp sent to {to_number} | SID: {msg.sid}")
    except TwilioRestException as e:
        frappe.log_error(str(e), f"WhatsApp send failed to {to_number}")
        frappe.logger().error(f"Twilio error: {e}")
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"WhatsApp unexpected error for {to_number}")


def _get_customer_mobile(customer_name):
    """Helper to fetch customer mobile number."""
    mobile = frappe.db.get_value("Customer", customer_name, "mobile_no")
    if not mobile:
        frappe.logger().debug(f"WhatsApp: No mobile_no for customer {customer_name}")
    return mobile


def send_sales_order_confirmation(doc, method):
    """Triggered on Sales Order submission."""
    mobile = _get_customer_mobile(doc.customer)
    if not mobile:
        return

    message = (
        f"Hi {doc.customer_name or doc.customer},\n"
        f"Your Sales Order *{doc.name}* has been confirmed.\n"
        f"Total: {doc.currency} {doc.grand_total:,.2f}\n"
        f"Thank you for your business!"
    )
    send_whatsapp_message(mobile, message)


def send_invoice_notification(doc, method):
    """Triggered on Sales Invoice submission."""
    mobile = _get_customer_mobile(doc.customer)
    if not mobile:
        return

    message = (
        f"Hi {doc.customer_name or doc.customer},\n"
        f"Invoice *{doc.name}* for {doc.currency} {doc.grand_total:,.2f} has been raised.\n"
        f"Due Date: {doc.due_date}\n"
        f"Please make payment at your earliest convenience."
    )
    send_whatsapp_message(mobile, message)


def send_payment_receipt(doc, method):
    """Triggered on Payment Entry submission."""
    if doc.party_type != "Customer":
        return

    mobile = _get_customer_mobile(doc.party)
    if not mobile:
        return

    message = (
        f"Hi {doc.party_name or doc.party},\n"
        f"We have received your payment of "
        f"{doc.paid_amount:,.2f} {doc.paid_to_account_currency}.\n"
        f"Payment Reference: *{doc.name}*\n"
        f"Thank you!"
    )
    send_whatsapp_message(mobile, message)
