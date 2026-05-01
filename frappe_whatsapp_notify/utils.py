"""
Utility helpers for frappe_whatsapp_notify.
"""
import re
import frappe


def normalise_phone(number: str) -> str | None:
    """
    Normalise a phone number to E.164 format (+<digits>).

    Returns None if the number is blank or clearly invalid.
    """
    if not number:
        return None

    # Strip whitespace, dashes, parentheses
    cleaned = re.sub(r"[\s\-().]+", "", number.strip())

    if not cleaned:
        return None

    # Add leading + if missing
    if not cleaned.startswith("+"):
        cleaned = "+" + cleaned

    # Must be + followed by 7-15 digits
    if not re.fullmatch(r"\+\d{7,15}", cleaned):
        frappe.logger().warning(f"WhatsApp: '{number}' does not look like a valid E.164 number.")
        return None

    return cleaned


def format_currency(amount: float, currency: str = "INR") -> str:
    """Return a human-readable currency string."""
    try:
        return f"{currency} {amount:,.2f}"
    except (TypeError, ValueError):
        return f"{currency} 0.00"


def build_message(template: str, **kwargs) -> str:
    """
    Simple template renderer using str.format_map.

    Example:
        build_message("Hi {customer}, your order {name} is confirmed.", customer="Acme", name="SO-0001")
    """
    try:
        return template.format_map(kwargs)
    except KeyError as e:
        frappe.logger().warning(f"WhatsApp message template missing key: {e}")
        return template


# ---------------------------------------------------------------------------
# Default message templates — override in WhatsApp Settings if needed
# ---------------------------------------------------------------------------

TEMPLATES = {
    "sales_order": (
        "Hi {customer},\n"
        "Your Sales Order *{name}* has been confirmed.\n"
        "Total: {amount}\n"
        "Thank you for your business!"
    ),
    "sales_invoice": (
        "Hi {customer},\n"
        "Invoice *{name}* for {amount} has been raised.\n"
        "Due Date: {due_date}\n"
        "Please make payment at your earliest convenience."
    ),
    "payment_receipt": (
        "Hi {customer},\n"
        "We have received your payment of {amount}.\n"
        "Payment Reference: *{name}*\n"
        "Thank you!"
    ),
    "overdue_reminder": (
        "Dear {customer},\n"
        "Invoice *{name}* for {amount} was due on {due_date}.\n"
        "Kindly arrange payment at your earliest convenience."
    ),
}
