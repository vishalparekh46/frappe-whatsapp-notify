"""
Shared pytest fixtures for frappe-whatsapp-notify tests.
"""
import sys
import types
from unittest.mock import MagicMock, patch
import pytest


# ---------------------------------------------------------------------------
# Frappe stub -- inserted into sys.modules so imports work without a real
# Frappe/ERPNext environment.
# ---------------------------------------------------------------------------

def _make_frappe_stub():
    frappe = types.ModuleType("frappe")

    # Common frappe helpers used across modules
    frappe.log_error = MagicMock()
    frappe.log = MagicMock()
    frappe.throw = MagicMock(side_effect=Exception)
    frappe.msgprint = MagicMock()
    frappe.get_doc = MagicMock()
    frappe.get_all = MagicMock(return_value=[])
    frappe.db = MagicMock()
    frappe.db.get_value = MagicMock(return_value=None)
    frappe.db.get_single_value = MagicMock(return_value=None)
    frappe.db.exists = MagicMock(return_value=False)
    frappe.session = MagicMock()
    frappe.session.user = "Administrator"
    frappe.local = MagicMock()
    frappe.utils = types.ModuleType("frappe.utils")
    frappe.utils.now_datetime = MagicMock(return_value=None)
    frappe.utils.getdate = MagicMock()
    frappe.utils.add_days = MagicMock()
    frappe.utils.date_diff = MagicMock(return_value=0)

    # Sub-modules
    sys.modules["frappe"] = frappe
    sys.modules["frappe.utils"] = frappe.utils
    return frappe


@pytest.fixture(scope="session", autouse=True)
def frappe_stub():
    """Insert a minimal frappe stub into sys.modules for the whole test session."""
    return _make_frappe_stub()


# ---------------------------------------------------------------------------
# WhatsApp Settings fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_whatsapp_settings():
    """Return a mock WhatsApp Settings document."""
    settings = MagicMock()
    settings.enabled = 1
    settings.api_endpoint = "https://api.whatsapp.example.com/v1/messages"
    settings.api_token = "test-token-abc123"
    settings.from_phone_number = "+919876543210"
    settings.max_retries = 3
    settings.retry_delay = 5
    settings.log_messages = 1
    return settings


# ---------------------------------------------------------------------------
# Generic document fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_doc():
    """Return a generic mock Frappe document."""
    doc = MagicMock()
    doc.name = "TEST-DOC-001"
    doc.doctype = "Sales Invoice"
    doc.customer = "Test Customer Pvt Ltd"
    doc.grand_total = 11800.00
    doc.outstanding_amount = 11800.00
    doc.due_date = "2024-02-15"
    doc.owner = "Administrator"
    doc.company = "Test Company Pvt Ltd"
    return doc


# ---------------------------------------------------------------------------
# WhatsApp Log fixture
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_whatsapp_log():
    """Return a mock WhatsApp Log document."""
    log = MagicMock()
    log.name = "WA-LOG-00001"
    log.status = "Sent"
    log.to_number = "+919876543210"
    log.message_body = "Your invoice TEST-DOC-001 is due."
    log.doctype_ref = "Sales Invoice"
    log.document_name = "TEST-DOC-001"
    log.retry_count = 0
    log.error_message = None
    return log


# ---------------------------------------------------------------------------
# requests mock fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_requests_success():
    """Patch requests.post to return a successful 200 response."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"messages": [{"id": "msg-id-001"}]}
    with patch("requests.post", return_value=mock_resp) as mock_post:
        yield mock_post


@pytest.fixture
def mock_requests_failure():
    """Patch requests.post to return a 400 error response."""
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.json.return_value = {"error": {"message": "Bad request", "code": 100}}
    with patch("requests.post", return_value=mock_resp) as mock_post:
        yield mock_post


@pytest.fixture
def mock_requests_timeout():
    """Patch requests.post to raise a Timeout exception."""
    import requests as req_lib
    with patch("requests.post", side_effect=req_lib.Timeout("Connection timed out")) as mock_post:
        yield mock_post
