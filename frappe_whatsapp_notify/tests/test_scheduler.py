"""Tests for frappe_whatsapp_notify.api.scheduler"""
import unittest
from unittest.mock import MagicMock, patch, call


class TestSendOverduePaymentReminders(unittest.TestCase):
    """Unit tests for send_overdue_payment_reminders()."""

    def _mock_settings(self, enabled=True):
        s = MagicMock()
        s.enabled = enabled
        return s

    @patch("frappe_whatsapp_notify.api.scheduler.frappe")
    def test_skips_when_app_disabled(self, mock_frappe):
        """If WhatsApp Settings.enabled is False, the function returns early."""
        from frappe_whatsapp_notify.api.scheduler import send_overdue_payment_reminders

        mock_frappe.get_single.return_value = self._mock_settings(enabled=False)
        mock_frappe.logger.return_value = MagicMock()

        send_overdue_payment_reminders()

        mock_frappe.get_all.assert_not_called()

    @patch("frappe_whatsapp_notify.api.scheduler.frappe")
    def test_skips_when_no_overdue_invoices(self, mock_frappe):
        """No messages sent when get_all returns an empty list."""
        from frappe_whatsapp_notify.api.scheduler import send_overdue_payment_reminders

        mock_frappe.get_single.return_value = self._mock_settings()
        mock_frappe.get_all.return_value = []
        mock_frappe.logger.return_value = MagicMock()

        with patch(
            "frappe_whatsapp_notify.api.scheduler.send_whatsapp_message"
        ) as mock_send:
            send_overdue_payment_reminders()
            mock_send.assert_not_called()

    @patch("frappe_whatsapp_notify.api.scheduler.frappe")
    def test_sends_reminder_for_overdue_invoice(self, mock_frappe):
        """A valid overdue invoice with a mobile number triggers a WhatsApp send."""
        from frappe_whatsapp_notify.api.scheduler import send_overdue_payment_reminders

        mock_frappe.get_single.return_value = self._mock_settings()
        mock_frappe.get_all.return_value = [
            MagicMock(
                name="SINV-0001",
                customer="Test Customer",
                outstanding_amount=5000.0,
                currency="INR",
                due_date="2024-01-01",
            )
        ]
        mock_frappe.logger.return_value = MagicMock()

        with patch(
            "frappe_whatsapp_notify.api.scheduler._get_customer_mobile",
            return_value="+919876543210",
        ), patch(
            "frappe_whatsapp_notify.api.scheduler.normalise_phone",
            return_value="+919876543210",
        ), patch(
            "frappe_whatsapp_notify.api.scheduler.send_whatsapp_message"
        ) as mock_send:
            send_overdue_payment_reminders()
            mock_send.assert_called_once()

    @patch("frappe_whatsapp_notify.api.scheduler.frappe")
    def test_skips_invoice_with_no_mobile(self, mock_frappe):
        """Invoice is skipped gracefully when no mobile number is found."""
        from frappe_whatsapp_notify.api.scheduler import send_overdue_payment_reminders

        mock_frappe.get_single.return_value = self._mock_settings()
        mock_frappe.get_all.return_value = [
            MagicMock(
                name="SINV-0002",
                customer="No Mobile Customer",
                outstanding_amount=1000.0,
                currency="INR",
                due_date="2024-01-15",
            )
        ]
        mock_frappe.logger.return_value = MagicMock()

        with patch(
            "frappe_whatsapp_notify.api.scheduler._get_customer_mobile",
            return_value=None,
        ), patch(
            "frappe_whatsapp_notify.api.scheduler.send_whatsapp_message"
        ) as mock_send:
            send_overdue_payment_reminders()
            mock_send.assert_not_called()

    @patch("frappe_whatsapp_notify.api.scheduler.frappe")
    def test_retries_on_send_failure(self, mock_frappe):
        """_send_with_retry retries MAX_RETRIES times before logging error."""
        from frappe_whatsapp_notify.api.scheduler import _send_with_retry

        mock_frappe.log_error = MagicMock()
        mock_frappe.logger.return_value = MagicMock()

        with patch(
            "frappe_whatsapp_notify.api.scheduler.send_whatsapp_message",
            side_effect=Exception("Twilio error"),
        ) as mock_send:
            result = _send_with_retry("+919876543210", "Test message", "SINV-0003")

            self.assertFalse(result)
            self.assertEqual(mock_send.call_count, 2)  # MAX_RETRIES = 2
            mock_frappe.log_error.assert_called_once()

    @patch("frappe_whatsapp_notify.api.scheduler.frappe")
    def test_send_with_retry_succeeds_on_first_try(self, mock_frappe):
        """_send_with_retry returns True immediately on successful send."""
        from frappe_whatsapp_notify.api.scheduler import _send_with_retry

        mock_frappe.logger.return_value = MagicMock()

        with patch(
            "frappe_whatsapp_notify.api.scheduler.send_whatsapp_message"
        ) as mock_send:
            result = _send_with_retry("+919876543210", "Test message", "SINV-0004")

            self.assertTrue(result)
            mock_send.assert_called_once_with("+919876543210", "Test message")


class TestGetCustomerMobile(unittest.TestCase):
    """Unit tests for _get_customer_mobile() helper."""

    @patch("frappe_whatsapp_notify.api.scheduler.frappe")
    def test_returns_customer_mobile_no(self, mock_frappe):
        """Returns mobile_no directly from Customer doctype if present."""
        from frappe_whatsapp_notify.api.scheduler import _get_customer_mobile

        mock_frappe.db.get_value.return_value = "+919876543210"
        result = _get_customer_mobile("Test Customer")
        self.assertEqual(result, "+919876543210")

    @patch("frappe_whatsapp_notify.api.scheduler.frappe")
    def test_falls_back_to_contact(self, mock_frappe):
        """Falls back to linked Contact mobile if Customer.mobile_no is empty."""
        from frappe_whatsapp_notify.api.scheduler import _get_customer_mobile

        mock_frappe.db.get_value.side_effect = [
            None,            # Customer.mobile_no → not found
            "CONT-0001",     # Dynamic Link → contact name
            "+919876543211", # Contact.mobile_no → found
        ]
        result = _get_customer_mobile("Test Customer")
        self.assertEqual(result, "+919876543211")

    @patch("frappe_whatsapp_notify.api.scheduler.frappe")
    def test_returns_none_when_no_mobile_anywhere(self, mock_frappe):
        """Returns None if neither Customer nor Contact has a mobile number."""
        from frappe_whatsapp_notify.api.scheduler import _get_customer_mobile

        mock_frappe.db.get_value.return_value = None
        result = _get_customer_mobile("No Mobile Customer")
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
