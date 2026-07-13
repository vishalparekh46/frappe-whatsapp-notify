"""Unit tests for frappe_whatsapp_notify.notifications module."""
import unittest
from unittest.mock import MagicMock, patch, call

MODULE = "frappe_whatsapp_notify.notifications"


def _make_settings(is_enabled=1):
    s = MagicMock()
    s.is_enabled = is_enabled
    return s


def _make_invoice(**kwargs):
    doc = MagicMock()
    doc.name = kwargs.get("name", "SINV-0001")
    doc.customer_name = kwargs.get("customer_name", "Test Customer")
    doc.posting_date = kwargs.get("posting_date", "2024-01-15")
    doc.currency = kwargs.get("currency", "INR")
    doc.grand_total = kwargs.get("grand_total", 11800.00)
    doc.outstanding_amount = kwargs.get("outstanding_amount", 11800.00)
    doc.due_date = kwargs.get("due_date", "2024-02-15")
    doc.company = kwargs.get("company", "Test Company Pvt Ltd")
    doc.contact_mobile = kwargs.get("contact_mobile", None)
    doc.mobile_no = kwargs.get("mobile_no", None)
    doc.customer = kwargs.get("customer", "CUST-0001")
    return doc


class TestSendInvoiceNotification(unittest.TestCase):
    """Tests for send_invoice_notification()."""

    @patch(MODULE + ".get_settings")
    def test_skips_when_disabled(self, mock_get_settings):
        """Should return early without sending when settings.is_enabled is False."""
        mock_get_settings.return_value = _make_settings(is_enabled=0)

        from frappe_whatsapp_notify.notifications import send_invoice_notification

        doc = _make_invoice()
        with patch(MODULE + "._send_with_retry") as mock_send:
            send_invoice_notification(doc)
            mock_send.assert_not_called()

    @patch(MODULE + ".get_settings")
    @patch(MODULE + ".frappe")
    def test_skips_when_no_mobile(self, mock_frappe, mock_get_settings):
        """Should log error and return when no mobile number is found."""
        mock_get_settings.return_value = _make_settings(is_enabled=1)
        mock_frappe.get_list.return_value = []

        from frappe_whatsapp_notify.notifications import send_invoice_notification

        doc = _make_invoice(contact_mobile=None, mobile_no=None)
        with patch(MODULE + "._send_with_retry") as mock_send:
            send_invoice_notification(doc)
            mock_send.assert_not_called()
            mock_frappe.log_error.assert_called_once()

    @patch(MODULE + ".get_settings")
    @patch(MODULE + ".frappe")
    def test_sends_when_mobile_on_doc(self, mock_frappe, mock_get_settings):
        """Should call _send_with_retry when contact_mobile is set on doc."""
        mock_get_settings.return_value = _make_settings(is_enabled=1)
        mock_logger = MagicMock()
        mock_frappe.logger.return_value = mock_logger

        from frappe_whatsapp_notify.notifications import send_invoice_notification

        doc = _make_invoice(contact_mobile="+919876543210")
        with patch(MODULE + "._send_with_retry") as mock_send:
            send_invoice_notification(doc)
            mock_send.assert_called_once()
            args = mock_send.call_args[0]
            self.assertEqual(args[0], "+919876543210")
            self.assertIn("SINV-0001", args[1])
            self.assertIn("Test Customer", args[1])

    @patch(MODULE + ".get_settings")
    @patch(MODULE + ".frappe")
    def test_fetches_mobile_from_contact(self, mock_frappe, mock_get_settings):
        """Should fall back to customer Contact if mobile not on doc."""
        mock_get_settings.return_value = _make_settings(is_enabled=1)
        mock_frappe.get_list.return_value = [{"mobile_no": "+911234567890"}]
        mock_logger = MagicMock()
        mock_frappe.logger.return_value = mock_logger

        from frappe_whatsapp_notify.notifications import send_invoice_notification

        doc = _make_invoice(contact_mobile=None, mobile_no=None)
        with patch(MODULE + "._send_with_retry") as mock_send:
            send_invoice_notification(doc)
            mock_send.assert_called_once()
            self.assertEqual(mock_send.call_args[0][0], "+911234567890")


class TestSendPaymentReminder(unittest.TestCase):
    """Tests for send_payment_reminder()."""

    @patch(MODULE + ".get_settings")
    def test_skips_when_disabled(self, mock_get_settings):
        """Should return early without sending when settings disabled."""
        mock_get_settings.return_value = _make_settings(is_enabled=0)

        from frappe_whatsapp_notify.notifications import send_payment_reminder

        doc = _make_invoice()
        with patch(MODULE + "._send_with_retry") as mock_send:
            send_payment_reminder(doc, days_overdue=7)
            mock_send.assert_not_called()

    @patch(MODULE + ".get_settings")
    @patch(MODULE + ".frappe")
    def test_includes_days_overdue_in_message(self, mock_frappe, mock_get_settings):
        """Rendered message should mention the number of days overdue."""
        mock_get_settings.return_value = _make_settings(is_enabled=1)
        mock_logger = MagicMock()
        mock_frappe.logger.return_value = mock_logger

        from frappe_whatsapp_notify.notifications import send_payment_reminder

        doc = _make_invoice(contact_mobile="+919000000000")
        with patch(MODULE + "._send_with_retry") as mock_send:
            send_payment_reminder(doc, days_overdue=14)
            mock_send.assert_called_once()
            message = mock_send.call_args[0][1]
            self.assertIn("14", message)
            self.assertIn("SINV-0001", message)


class TestRenderTemplates(unittest.TestCase):
    """Tests for _render() template function."""

    def test_invoice_template_contains_expected_fields(self):
        """Invoice template should render customer name, invoice number, and amount."""
        from frappe_whatsapp_notify.notifications import _render

        result = _render(
            "invoice",
            {
                "customer_name": "Acme Corp",
                "invoice_no": "SINV-9999",
                "posting_date": "2024-03-01",
                "currency": "INR",
                "grand_total": "1,18,000.00",
                "due_date": "2024-03-31",
                "company": "My Company",
            },
        )
        self.assertIn("Acme Corp", result)
        self.assertIn("SINV-9999", result)
        self.assertIn("1,18,000.00", result)
        self.assertIn("My Company", result)

    def test_payment_reminder_template_contains_overdue(self):
        """Payment reminder template should include days_overdue."""
        from frappe_whatsapp_notify.notifications import _render

        result = _render(
            "payment_reminder",
            {
                "customer_name": "Beta Ltd",
                "invoice_no": "SINV-0042",
                "currency": "INR",
                "outstanding_amount": "50,000.00",
                "due_date": "2024-01-01",
                "days_overdue": 30,
                "company": "My Company",
            },
        )
        self.assertIn("30", result)
        self.assertIn("SINV-0042", result)
        self.assertIn("overdue", result.lower())

    def test_unknown_template_returns_empty_string(self):
        """_render with unknown key should return empty string."""
        from frappe_whatsapp_notify.notifications import _render

        result = _render("nonexistent_template", {})
        self.assertEqual(result, "")


if __name__ == "__main__":
    unittest.main()
