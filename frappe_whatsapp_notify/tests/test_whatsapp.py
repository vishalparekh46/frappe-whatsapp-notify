import unittest
from unittest.mock import MagicMock, patch

import frappe


class TestWhatsAppNotify(unittest.TestCase):
    """Unit tests for frappe_whatsapp_notify.api.whatsapp"""

    def setUp(self):
        """Set up mock settings for each test."""
        self.mock_settings = MagicMock()
        self.mock_settings.enabled = True
        self.mock_settings.account_sid = "ACtest123"
        self.mock_settings.from_number = "+14155238886"
        self.mock_settings.get_password.return_value = "test_auth_token"

    @patch("frappe_whatsapp_notify.api.whatsapp.get_settings")
    @patch("frappe_whatsapp_notify.api.whatsapp.Client")
    def test_send_whatsapp_message_success(self, mock_client_cls, mock_get_settings):
        """Test that a WhatsApp message is sent successfully."""
        mock_get_settings.return_value = self.mock_settings
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(sid="SM123")

        from frappe_whatsapp_notify.api.whatsapp import send_whatsapp_message
        send_whatsapp_message("+919876543210", "Test message")

        mock_client.messages.create.assert_called_once_with(
            from_="whatsapp:+14155238886",
            body="Test message",
            to="whatsapp:+919876543210",
        )

    @patch("frappe_whatsapp_notify.api.whatsapp.get_settings")
    def test_send_skipped_when_disabled(self, mock_get_settings):
        """Test that sending is skipped when notifications are disabled."""
        self.mock_settings.enabled = False
        mock_get_settings.return_value = self.mock_settings

        from frappe_whatsapp_notify.api.whatsapp import send_whatsapp_message
        # Should return without error and without sending
        send_whatsapp_message("+919876543210", "Test message")

    @patch("frappe_whatsapp_notify.api.whatsapp.get_settings")
    def test_send_skipped_when_no_number(self, mock_get_settings):
        """Test that sending is skipped when no phone number provided."""
        mock_get_settings.return_value = self.mock_settings

        from frappe_whatsapp_notify.api.whatsapp import send_whatsapp_message
        # Should return without error
        send_whatsapp_message(None, "Test message")
        send_whatsapp_message("", "Test message")

    @patch("frappe_whatsapp_notify.api.whatsapp.get_settings")
    @patch("frappe_whatsapp_notify.api.whatsapp.Client")
    def test_number_normalised_with_plus(self, mock_client_cls, mock_get_settings):
        """Test that numbers without + prefix get normalised."""
        mock_get_settings.return_value = self.mock_settings
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(sid="SM456")

        from frappe_whatsapp_notify.api.whatsapp import send_whatsapp_message
        send_whatsapp_message("919876543210", "Test message")

        call_args = mock_client.messages.create.call_args
        self.assertEqual(call_args.kwargs["to"], "whatsapp:+919876543210")


if __name__ == "__main__":
    unittest.main()
