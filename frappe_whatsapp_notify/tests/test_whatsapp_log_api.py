# Copyright (c) 2024, Aavatto and contributors
# For license information, please see license.txt
"""Unit tests for frappe_whatsapp_notify.api.whatsapp_log_api."""

import unittest
from unittest.mock import MagicMock, patch

import frappe


class TestGetRecentLogs(unittest.TestCase):
    """Tests for get_recent_logs()."""

    @patch("frappe_whatsapp_notify.api.whatsapp_log_api.frappe")
    def test_returns_list(self, mock_frappe):
        from frappe_whatsapp_notify.api.whatsapp_log_api import get_recent_logs

        mock_frappe.get_all.return_value = [
            {"name": "WA-LOG-2024-01-01-00001", "status": "Sent"},
        ]
        result = get_recent_logs(limit=5)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)

    @patch("frappe_whatsapp_notify.api.whatsapp_log_api.frappe")
    def test_limit_capped_at_200(self, mock_frappe):
        from frappe_whatsapp_notify.api.whatsapp_log_api import get_recent_logs

        mock_frappe.get_all.return_value = []
        get_recent_logs(limit=999)
        call_kwargs = mock_frappe.get_all.call_args[1]
        self.assertEqual(call_kwargs["limit"], 200)

    @patch("frappe_whatsapp_notify.api.whatsapp_log_api.frappe")
    def test_status_filter_applied(self, mock_frappe):
        from frappe_whatsapp_notify.api.whatsapp_log_api import get_recent_logs

        mock_frappe.get_all.return_value = []
        get_recent_logs(status="Failed")
        call_kwargs = mock_frappe.get_all.call_args[1]
        self.assertEqual(call_kwargs["filters"]["status"], "Failed")

    @patch("frappe_whatsapp_notify.api.whatsapp_log_api.frappe")
    def test_no_filter_when_status_none(self, mock_frappe):
        from frappe_whatsapp_notify.api.whatsapp_log_api import get_recent_logs

        mock_frappe.get_all.return_value = []
        get_recent_logs(status=None)
        call_kwargs = mock_frappe.get_all.call_args[1]
        self.assertNotIn("status", call_kwargs["filters"])


class TestGetLogSummary(unittest.TestCase):
    """Tests for get_log_summary()."""

    @patch("frappe_whatsapp_notify.api.whatsapp_log_api.frappe")
    @patch("frappe_whatsapp_notify.api.whatsapp_log_api.add_days")
    @patch("frappe_whatsapp_notify.api.whatsapp_log_api.today")
    def test_counts_correctly(self, mock_today, mock_add_days, mock_frappe):
        from frappe_whatsapp_notify.api.whatsapp_log_api import get_log_summary

        mock_today.return_value = "2024-01-10"
        mock_add_days.return_value = "2024-01-03"
        mock_frappe.db.get_all.return_value = [
            {"status": "Sent"},
            {"status": "Sent"},
            {"status": "Failed"},
            {"status": "Skipped"},
        ]
        result = get_log_summary(days=7)
        self.assertEqual(result["sent"], 2)
        self.assertEqual(result["failed"], 1)
        self.assertEqual(result["skipped"], 1)
        self.assertEqual(result["total"], 4)
        self.assertEqual(result["period_days"], 7)

    @patch("frappe_whatsapp_notify.api.whatsapp_log_api.frappe")
    @patch("frappe_whatsapp_notify.api.whatsapp_log_api.add_days")
    @patch("frappe_whatsapp_notify.api.whatsapp_log_api.today")
    def test_empty_result(self, mock_today, mock_add_days, mock_frappe):
        from frappe_whatsapp_notify.api.whatsapp_log_api import get_log_summary

        mock_today.return_value = "2024-01-10"
        mock_add_days.return_value = "2024-01-03"
        mock_frappe.db.get_all.return_value = []
        result = get_log_summary(days=7)
        self.assertEqual(result["total"], 0)
        self.assertEqual(result["sent"], 0)


class TestGetFailedLogs(unittest.TestCase):
    """Tests for get_failed_logs()."""

    @patch("frappe_whatsapp_notify.api.whatsapp_log_api.frappe")
    def test_filters_by_failed(self, mock_frappe):
        from frappe_whatsapp_notify.api.whatsapp_log_api import get_failed_logs

        mock_frappe.get_all.return_value = []
        get_failed_logs()
        call_kwargs = mock_frappe.get_all.call_args[1]
        self.assertEqual(call_kwargs["filters"]["status"], "Failed")

    @patch("frappe_whatsapp_notify.api.whatsapp_log_api.frappe")
    def test_limit_capped(self, mock_frappe):
        from frappe_whatsapp_notify.api.whatsapp_log_api import get_failed_logs

        mock_frappe.get_all.return_value = []
        get_failed_logs(limit=500)
        call_kwargs = mock_frappe.get_all.call_args[1]
        self.assertEqual(call_kwargs["limit"], 200)

    @patch("frappe_whatsapp_notify.api.whatsapp_log_api.frappe")
    def test_returns_list(self, mock_frappe):
        from frappe_whatsapp_notify.api.whatsapp_log_api import get_failed_logs

        mock_frappe.get_all.return_value = [
            {"name": "WA-LOG-2024-01-01-00002", "status": "Failed"},
        ]
        result = get_failed_logs()
        self.assertIsInstance(result, list)
        self.assertEqual(result[0]["status"], "Failed")


class TestPurgeOldLogs(unittest.TestCase):
    """Tests for purge_old_logs()."""

    @patch("frappe_whatsapp_notify.api.whatsapp_log_api.frappe")
    @patch(
        "frappe_whatsapp_notify.api.whatsapp_log_api.frappe.only_for",
        return_value=None,
    )
    def test_returns_deleted_count(self, mock_only_for, mock_frappe):
        from frappe_whatsapp_notify.api.whatsapp_log_api import purge_old_logs

        with patch(
            "frappe_whatsapp_notify.doctype.whatsapp_log.whatsapp_log.WhatsAppLog.purge_old_logs",
            return_value=5,
        ):
            mock_frappe.only_for = MagicMock()
            mock_frappe.msgprint = MagicMock()
            result = purge_old_logs(days=30)
            self.assertEqual(result["deleted"], 5)


if __name__ == "__main__":
    unittest.main()
