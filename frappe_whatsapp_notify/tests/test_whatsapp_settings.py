"""Unit tests for WhatsApp Settings controller."""
import unittest
from unittest.mock import MagicMock, patch

MODULE = "frappe_whatsapp_notify.doctype.whatsapp_settings.whatsapp_settings"


class TestWhatsAppSettings(unittest.TestCase):
    """Tests for the WhatsApp Settings DocType controller."""

    def _make_doc(self, **kwargs):
        """Return a minimal mock WhatsApp Settings document."""
        doc = MagicMock()
        doc.is_enabled = kwargs.get("is_enabled", 1)
        doc.api_key = kwargs.get("api_key", "test-api-key-123")
        doc.phone_number_id = kwargs.get("phone_number_id", "1234567890")
        doc.whatsapp_business_account_id = kwargs.get("whatsapp_business_account_id", "")
        doc.api_version = kwargs.get("api_version", "v17.0")
        return doc

    @patch(MODULE + ".frappe")
    def test_validate_raises_if_enabled_without_api_key(self, mock_frappe):
        """Validate should raise ValidationError when enabled but api_key is blank."""
        from frappe_whatsapp_notify.doctype.whatsapp_settings.whatsapp_settings import (
            WhatsAppSettings,
        )

        mock_frappe.throw = MagicMock(side_effect=Exception("api_key required"))
        ctrl = WhatsAppSettings.__new__(WhatsAppSettings)
        ctrl.__dict__.update(self._make_doc(api_key="").__dict__)

        with self.assertRaises(Exception) as ctx:
            ctrl.validate()
        self.assertIn("api_key", str(ctx.exception))

    @patch(MODULE + ".frappe")
    def test_validate_raises_if_enabled_without_phone_number(self, mock_frappe):
        """Validate should raise when enabled but phone_number_id is blank."""
        from frappe_whatsapp_notify.doctype.whatsapp_settings.whatsapp_settings import (
            WhatsAppSettings,
        )

        mock_frappe.throw = MagicMock(side_effect=Exception("phone_number_id required"))
        ctrl = WhatsAppSettings.__new__(WhatsAppSettings)
        ctrl.__dict__.update(self._make_doc(phone_number_id="").__dict__)

        with self.assertRaises(Exception) as ctx:
            ctrl.validate()
        self.assertIn("phone_number_id", str(ctx.exception))

    @patch(MODULE + ".frappe")
    def test_validate_passes_when_disabled(self, mock_frappe):
        """Validate should not raise when is_enabled=0 even if fields are blank."""
        from frappe_whatsapp_notify.doctype.whatsapp_settings.whatsapp_settings import (
            WhatsAppSettings,
        )

        mock_frappe.throw = MagicMock(side_effect=Exception("should not throw"))
        ctrl = WhatsAppSettings.__new__(WhatsAppSettings)
        ctrl.__dict__.update(
            self._make_doc(is_enabled=0, api_key="", phone_number_id="").__dict__
        )

        # Should not raise
        try:
            ctrl.validate()
        except Exception:
            self.fail("validate() raised unexpectedly when settings are disabled")

    @patch(MODULE + ".frappe")
    def test_get_settings_returns_doc(self, mock_frappe):
        """get_settings() should return a single WhatsApp Settings document."""
        from frappe_whatsapp_notify.doctype.whatsapp_settings.whatsapp_settings import (
            get_settings,
        )

        mock_doc = self._make_doc()
        mock_frappe.get_single.return_value = mock_doc

        result = get_settings()
        mock_frappe.get_single.assert_called_once_with("WhatsApp Settings")
        self.assertEqual(result, mock_doc)

    @patch(MODULE + ".frappe")
    def test_is_enabled_returns_true_when_active(self, mock_frappe):
        """is_enabled flag should be truthy when the integration is active."""
        mock_doc = self._make_doc(is_enabled=1)
        mock_frappe.get_single.return_value = mock_doc

        from frappe_whatsapp_notify.doctype.whatsapp_settings.whatsapp_settings import (
            get_settings,
        )

        settings = get_settings()
        self.assertTrue(settings.is_enabled)

    @patch(MODULE + ".frappe")
    def test_is_enabled_returns_false_when_inactive(self, mock_frappe):
        """is_enabled flag should be falsy when the integration is disabled."""
        mock_doc = self._make_doc(is_enabled=0)
        mock_frappe.get_single.return_value = mock_doc

        from frappe_whatsapp_notify.doctype.whatsapp_settings.whatsapp_settings import (
            get_settings,
        )

        settings = get_settings()
        self.assertFalse(settings.is_enabled)

    @patch(MODULE + ".frappe")
    def test_api_version_defaults_to_v17(self, mock_frappe):
        """api_version should default to v17.0 if not explicitly set."""
        mock_doc = self._make_doc(api_version="v17.0")
        mock_frappe.get_single.return_value = mock_doc

        from frappe_whatsapp_notify.doctype.whatsapp_settings.whatsapp_settings import (
            get_settings,
        )

        settings = get_settings()
        self.assertEqual(settings.api_version, "v17.0")


class TestPhoneNormalisation(unittest.TestCase):
    """Tests for phone number normalisation used in settings validation."""

    @patch(MODULE + ".frappe")
    def test_strips_leading_plus(self, mock_frappe):
        """Phone numbers already starting with + should be kept as-is."""
        from frappe_whatsapp_notify.doctype.whatsapp_settings.whatsapp_settings import (
            normalise_phone,
        )

        self.assertEqual(normalise_phone("+919876543210"), "+919876543210")

    @patch(MODULE + ".frappe")
    def test_adds_plus_to_numeric_string(self, mock_frappe):
        """Numeric phone strings without + should get a + prefix."""
        from frappe_whatsapp_notify.doctype.whatsapp_settings.whatsapp_settings import (
            normalise_phone,
        )

        self.assertEqual(normalise_phone("919876543210"), "+919876543210")

    @patch(MODULE + ".frappe")
    def test_strips_spaces_and_hyphens(self, mock_frappe):
        """Spaces and hyphens should be removed before normalisation."""
        from frappe_whatsapp_notify.doctype.whatsapp_settings.whatsapp_settings import (
            normalise_phone,
        )

        self.assertEqual(normalise_phone("+91 98765-43210"), "+919876543210")


if __name__ == "__main__":
    unittest.main()
