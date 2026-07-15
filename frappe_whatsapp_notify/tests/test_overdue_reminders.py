"""Unit tests for frappe_whatsapp_notify.overdue_reminders module."""
import unittest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch, call

MODULE = "frappe_whatsapp_notify.overdue_reminders"


def _make_inv_data(**kwargs):
    """Return a dict mimicking a frappe.get_list row for Sales Invoice."""
    today = date.today()
    return {
        "name": kwargs.get("name", "SINV-0001"),
        "customer": kwargs.get("customer", "CUST-0001"),
        "customer_name": kwargs.get("customer_name", "Test Customer"),
        "due_date": kwargs.get("due_date", today - timedelta(days=7)),
        "outstanding_amount": kwargs.get("outstanding_amount", 11800.00),
        "contact_mobile": kwargs.get("contact_mobile", None),
        "mobile_no": kwargs.get("mobile_no", None),
        "currency": kwargs.get("currency", "INR"),
        "grand_total": kwargs.get("grand_total", 11800.00),
        "company": kwargs.get("company", "Test Company Pvt Ltd"),
        "posting_date": kwargs.get("posting_date", str(today - timedelta(days=30))),
    }


class TestDaysOverdue(unittest.TestCase):
    """Tests for the _days_overdue() helper."""

    def test_returns_correct_days_for_date_object(self):
        """Should calculate days overdue from a date object."""
        from frappe_whatsapp_notify.overdue_reminders import _days_overdue

        due = date.today() - timedelta(days=10)
        result = _days_overdue(due)
        self.assertEqual(result, 10)

    def test_returns_correct_days_for_string(self):
        """Should parse a YYYY-MM-DD string and calculate days overdue."""
        from frappe_whatsapp_notify.overdue_reminders import _days_overdue

        due = date.today() - timedelta(days=5)
        result = _days_overdue(str(due))
        self.assertEqual(result, 5)

    def test_returns_zero_for_future_date(self):
        """Should clamp to 0 if due date is in the future."""
        from frappe_whatsapp_notify.overdue_reminders import _days_overdue

        due = date.today() + timedelta(days=3)
        result = _days_overdue(due)
        self.assertEqual(result, 0)

    def test_returns_zero_for_today(self):
        """Should return 0 when due date is today."""
        from frappe_whatsapp_notify.overdue_reminders import _days_overdue

        result = _days_overdue(date.today())
        self.assertEqual(result, 0)

    def test_handles_datetime_object(self):
        """Should call .date() on datetime objects."""
        from datetime import datetime
        from frappe_whatsapp_notify.overdue_reminders import _days_overdue

        due_dt = datetime.combine(date.today() - timedelta(days=3), datetime.min.time())
        result = _days_overdue(due_dt)
        self.assertEqual(result, 3)


class TestGetOverdueInvoices(unittest.TestCase):
    """Tests for _get_overdue_invoices()."""

    @patch(MODULE + ".frappe")
    def test_calls_get_list_with_correct_filters(self, mock_frappe):
        """Should query Sales Invoice with docstatus=1, outstanding>0, due_date<today."""
        mock_frappe.get_list.return_value = []

        from frappe_whatsapp_notify.overdue_reminders import _get_overdue_invoices

        _get_overdue_invoices()
        mock_frappe.get_list.assert_called_once()
        call_kwargs = mock_frappe.get_list.call_args
        filters = call_kwargs[1]["filters"] if call_kwargs[1] else call_kwargs[0][1]
        self.assertIn("docstatus", filters)
        self.assertIn("outstanding_amount", filters)
        self.assertIn("due_date", filters)

    @patch(MODULE + ".frappe")
    def test_returns_list_from_frappe(self, mock_frappe):
        """Should return whatever frappe.get_list returns."""
        expected = [_make_inv_data(), _make_inv_data(name="SINV-0002")]
        mock_frappe.get_list.return_value = expected

        from frappe_whatsapp_notify.overdue_reminders import _get_overdue_invoices

        result = _get_overdue_invoices()
        self.assertEqual(result, expected)


class TestSendOverdueReminders(unittest.TestCase):
    """Tests for send_overdue_reminders()."""

    @patch(MODULE + ".frappe")
    @patch(MODULE + "._get_overdue_invoices")
    def test_does_nothing_when_no_invoices(self, mock_get_inv, mock_frappe):
        """Should log and return early when no overdue invoices exist."""
        mock_get_inv.return_value = []
        mock_logger = MagicMock()
        mock_frappe.logger.return_value = mock_logger

        from frappe_whatsapp_notify.overdue_reminders import send_overdue_reminders

        with patch(MODULE + ".send_payment_reminder") as mock_send:
            send_overdue_reminders()
            mock_send.assert_not_called()
        mock_logger.info.assert_called()

    @patch(MODULE + ".frappe")
    @patch(MODULE + "._get_overdue_invoices")
    def test_calls_send_payment_reminder_for_each_invoice(self, mock_get_inv, mock_frappe):
        """Should call send_payment_reminder once per overdue invoice."""
        inv1 = _make_inv_data(name="SINV-0001")
        inv2 = _make_inv_data(name="SINV-0002")
        mock_get_inv.return_value = [inv1, inv2]
        mock_frappe.get_doc.side_effect = lambda doctype, name: MagicMock(name=name)
        mock_logger = MagicMock()
        mock_frappe.logger.return_value = mock_logger

        from frappe_whatsapp_notify.overdue_reminders import send_overdue_reminders

        with patch(MODULE + ".send_payment_reminder") as mock_send:
            send_overdue_reminders()
            self.assertEqual(mock_send.call_count, 2)

    @patch(MODULE + ".frappe")
    @patch(MODULE + "._get_overdue_invoices")
    def test_passes_days_overdue_to_reminder(self, mock_get_inv, mock_frappe):
        """days_overdue passed to send_payment_reminder should match actual overdue days."""
        due = date.today() - timedelta(days=14)
        inv = _make_inv_data(name="SINV-0042", due_date=due)
        mock_get_inv.return_value = [inv]
        mock_doc = MagicMock()
        mock_frappe.get_doc.return_value = mock_doc
        mock_logger = MagicMock()
        mock_frappe.logger.return_value = mock_logger

        from frappe_whatsapp_notify.overdue_reminders import send_overdue_reminders

        with patch(MODULE + ".send_payment_reminder") as mock_send:
            send_overdue_reminders()
            mock_send.assert_called_once_with(mock_doc, days_overdue=14)

    @patch(MODULE + ".frappe")
    @patch(MODULE + "._get_overdue_invoices")
    def test_continues_loop_on_per_invoice_error(self, mock_get_inv, mock_frappe):
        """An error on one invoice should not abort processing of the rest."""
        inv1 = _make_inv_data(name="SINV-0001")
        inv2 = _make_inv_data(name="SINV-0002")
        mock_get_inv.return_value = [inv1, inv2]
        mock_logger = MagicMock()
        mock_frappe.logger.return_value = mock_logger
        mock_frappe.get_doc.return_value = MagicMock()

        from frappe_whatsapp_notify.overdue_reminders import send_overdue_reminders

        call_count = 0

        def flaky_send(doc, days_overdue=0):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError("WhatsApp API timeout")

        with patch(MODULE + ".send_payment_reminder", side_effect=flaky_send):
            send_overdue_reminders()

        self.assertEqual(call_count, 2)
        mock_frappe.log_error.assert_called_once()

    @patch(MODULE + ".frappe")
    @patch(MODULE + "._get_overdue_invoices")
    def test_logs_summary_at_end(self, mock_get_inv, mock_frappe):
        """Should log a sent/failed summary after processing all invoices."""
        mock_get_inv.return_value = [_make_inv_data()]
        mock_frappe.get_doc.return_value = MagicMock()
        mock_logger = MagicMock()
        mock_frappe.logger.return_value = mock_logger

        from frappe_whatsapp_notify.overdue_reminders import send_overdue_reminders

        with patch(MODULE + ".send_payment_reminder"):
            send_overdue_reminders()

        # logger.info should be called at least twice: start + summary
        self.assertGreaterEqual(mock_logger.info.call_count, 2)


if __name__ == "__main__":
    unittest.main()
