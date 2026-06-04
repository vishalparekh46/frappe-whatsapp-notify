# Copyright (c) 2024, Aavatto and contributors
# For license information, please see license.txt
"""Unit tests for send_low_stock_alerts() in scheduler.py.

Run with:
    bench run-tests --app frappe_whatsapp_notify \
        --module frappe_whatsapp_notify.tests.test_scheduler_low_stock
"""

import unittest
from unittest.mock import MagicMock, call, patch

MODULE = "frappe_whatsapp_notify.api.scheduler"


def _make_settings(enabled=True, mobile="919876543210"):
	s = MagicMock()
	s.enabled = enabled
	s.low_stock_alert_mobile = mobile
	return s


def _make_bin(item_code="ITEM-001", warehouse="Stores - T", actual_qty=5,
			  item_name="Test Item", stock_uom="Nos", reorder_level=10):
	return {
		"item_code": item_code,
		"warehouse": warehouse,
		"actual_qty": actual_qty,
		"item_name": item_name,
		"stock_uom": stock_uom,
		"reorder_level": reorder_level,
	}


class TestSendLowStockAlerts(unittest.TestCase):

	@patch(MODULE + ".frappe")
	def test_does_nothing_when_disabled(self, mock_frappe):
		"""When WhatsApp Settings.enabled is False the function returns early."""
		mock_frappe.get_single.return_value = _make_settings(enabled=False)
		from frappe_whatsapp_notify.api.scheduler import send_low_stock_alerts
		send_low_stock_alerts()
		mock_frappe.db.sql.assert_not_called()

	@patch(MODULE + ".frappe")
	def test_does_nothing_when_no_mobile(self, mock_frappe):
		"""When low_stock_alert_mobile is falsy the function returns early."""
		mock_frappe.get_single.return_value = _make_settings(mobile="")
		from frappe_whatsapp_notify.api.scheduler import send_low_stock_alerts
		send_low_stock_alerts()
		mock_frappe.db.sql.assert_not_called()

	@patch(MODULE + ".frappe")
	def test_no_alert_when_no_low_bins(self, mock_frappe):
		"""When DB returns no low-stock bins, no messages are sent."""
		mock_frappe.get_single.return_value = _make_settings()
		mock_frappe.db.sql.return_value = []
		mock_frappe.defaults.get_global_default.return_value = "Test Company"
		from frappe_whatsapp_notify.api.scheduler import send_low_stock_alerts
		send_low_stock_alerts()
		# sendMessage (Twilio client) should never be called
		mock_frappe.get_doc.assert_not_called()

	@patch(MODULE + "._send_with_retry")
	@patch(MODULE + ".frappe")
	def test_sends_alert_for_each_low_bin(self, mock_frappe, mock_send):
		"""One WhatsApp message is dispatched per low-stock bin row."""
		mock_frappe.get_single.return_value = _make_settings()
		mock_frappe.defaults.get_global_default.return_value = "Acme Ltd"
		low_bins = [
			_make_bin("ITEM-001", "Stores - T", 3, "Widget A", "Nos", 10),
			_make_bin("ITEM-002", "FG Store - T", 0, "Widget B", "Kg", 5),
		]
		mock_frappe.db.sql.return_value = low_bins
		from frappe_whatsapp_notify.api.scheduler import send_low_stock_alerts
		send_low_stock_alerts()
		self.assertEqual(mock_send.call_count, 2)

	@patch(MODULE + "._send_with_retry")
	@patch(MODULE + ".frappe")
	def test_message_contains_item_name(self, mock_frappe, mock_send):
		"""Message body must mention the item name and warehouse."""
		mock_frappe.get_single.return_value = _make_settings()
		mock_frappe.defaults.get_global_default.return_value = "Acme Ltd"
		low_bins = [_make_bin(item_name="Critical Part", warehouse="Raw - T")]
		mock_frappe.db.sql.return_value = low_bins
		from frappe_whatsapp_notify.api.scheduler import send_low_stock_alerts
		send_low_stock_alerts()
		# Inspect the message body passed to _send_with_retry
		_, kwargs = mock_send.call_args
		message_body = kwargs.get("message") or mock_send.call_args[0][1]
		self.assertIn("Critical Part", message_body)
		self.assertIn("Raw - T", message_body)

	@patch(MODULE + "._send_with_retry")
	@patch(MODULE + ".frappe")
	def test_sql_query_uses_batch_size(self, mock_frappe, mock_send):
		"""The DB query must include a LIMIT equal to BATCH_SIZE."""
		mock_frappe.get_single.return_value = _make_settings()
		mock_frappe.defaults.get_global_default.return_value = "Acme"
		mock_frappe.db.sql.return_value = []
		from frappe_whatsapp_notify.api.scheduler import send_low_stock_alerts, BATCH_SIZE
		send_low_stock_alerts()
		call_args = mock_frappe.db.sql.call_args
		params = call_args[0][1] if len(call_args[0]) > 1 else call_args[1].get("values", {})
		self.assertEqual(params.get("limit"), BATCH_SIZE)


class TestNormalisePhone(unittest.TestCase):

	def test_strips_spaces_and_dashes(self):
		from frappe_whatsapp_notify.api.scheduler import normalise_phone
		self.assertEqual(normalise_phone("+91 98765-43210"), "+919876543210")

	def test_adds_plus_if_missing(self):
		from frappe_whatsapp_notify.api.scheduler import normalise_phone
		self.assertEqual(normalise_phone("919876543210"), "+919876543210")

	def test_preserves_existing_plus(self):
		from frappe_whatsapp_notify.api.scheduler import normalise_phone
		self.assertEqual(normalise_phone("+919876543210"), "+919876543210")


if __name__ == "__main__":
	unittest.main()
