import frappe
from frappe.model.document import Document


class WhatsAppSettings(Document):
    """Controller for WhatsApp Settings singleton DocType."""

    def validate(self):
        if self.enabled:
            self._validate_required_fields()
            self._validate_from_number()

    def _validate_required_fields(self):
        if not self.account_sid:
            frappe.throw("Twilio Account SID is required to enable WhatsApp notifications.")
        if not self.get_password("auth_token"):
            frappe.throw("Auth Token is required to enable WhatsApp notifications.")
        if not self.from_number:
            frappe.throw("From Number is required to enable WhatsApp notifications.")

    def _validate_from_number(self):
        number = self.from_number.strip()
        if not number.startswith("+"):
            frappe.throw(
                "From Number must include the country code with a leading '+'. "
                "Example: +14155238886"
            )
        # Remove the + and check remaining digits
        digits = number[1:].replace(" ", "").replace("-", "")
        if not digits.isdigit() or len(digits) < 7:
            frappe.throw("From Number does not appear to be a valid phone number.")

    def on_update(self):
        frappe.cache().delete_key("whatsapp_settings")
        if self.enabled:
            frappe.msgprint(
                "WhatsApp notifications enabled successfully.",
                indicator="green",
                alert=True,
            )
