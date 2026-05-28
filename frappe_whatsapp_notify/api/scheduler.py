import frappe
from frappe.utils import today, add_days, nowdate
from frappe_whatsapp_notify.api.whatsapp import send_whatsapp_message
from frappe_whatsapp_notify.utils import normalise_phone, format_currency, TEMPLATES, build_message

# Configurable batch size
BATCH_SIZE = frappe.conf.get("whatsapp_reminder_batch_size", 50)
MAX_RETRIES = 2


def send_overdue_payment_reminders():
    """Daily scheduled task: remind customers with overdue Sales Invoices."""
    settings = frappe.get_single("WhatsApp Settings")
    if not settings.enabled:
        frappe.logger("whatsapp").info("WhatsApp reminders skipped — app disabled.")
        return

    overdue_invoices = frappe.get_all(
        "Sales Invoice",
        filters={
            "docstatus": 1,
            "outstanding_amount": [">", 0],
            "due_date": ["<", today()],
        },
        fields=["name", "customer", "outstanding_amount", "currency", "due_date"],
        limit=BATCH_SIZE,
        order_by="due_date asc",
    )

    if not overdue_invoices:
        return

    sent = failed = skipped = 0
    for inv in overdue_invoices:
        mobile = _get_customer_mobile(inv.customer)
        if not mobile:
            skipped += 1
            continue
        message = build_message(
            TEMPLATES["overdue_reminder"],
            customer=inv.customer,
            name=inv.name,
            amount=format_currency(inv.outstanding_amount, inv.currency),
            due_date=inv.due_date,
        )
        try:
            _send_with_retry(mobile, message)
            sent += 1
        except Exception as exc:
            frappe.logger("whatsapp").error(f"Overdue reminder failed for {inv.name}: {exc}")
            failed += 1

    frappe.logger("whatsapp").info(f"Overdue reminders: {sent} sent, {failed} failed, {skipped} skipped.")


def _send_with_retry(mobile, message, retries=MAX_RETRIES):
    """Attempt to send a WhatsApp message, retrying on failure."""
    last_exc = None
    for attempt in range(1, retries + 2):
        try:
            send_whatsapp_message(mobile, message)
            return
        except Exception as exc:
            last_exc = exc
            frappe.logger("whatsapp").warning(f"Send attempt {attempt} failed: {exc}")
    raise last_exc


def _get_customer_mobile(customer_name):
    """Return the primary mobile for a customer, or None if not found."""
    contact = frappe.db.get_value(
        "Contact",
        {"link_doctype": "Customer", "link_name": customer_name},
        ["mobile_no", "phone"],
        as_dict=True,
    )
    if not contact:
        return None
    raw = contact.mobile_no or contact.phone
    return normalise_phone(raw) if raw else None


# ---------------------------------------------------------------------------
# Low Stock Alert
# ---------------------------------------------------------------------------

LOW_STOCK_TEMPLATE = (
    "Dear {contact},\n\n"
    "\u26a0\ufe0f *Low Stock Alert* \u2014 {item_name}\n"
    "Warehouse: {warehouse}\n"
    "Current stock: {current_qty} {uom}\n"
    "Reorder level: {reorder_level} {uom}\n\n"
    "Please place a replenishment order at your earliest convenience.\n\n"
    "Regards,\n{company}"
)


def send_low_stock_alerts():
    """Daily scheduled task: notify managers about items below reorder level.

    Queries all items where actual stock (tabBin) has fallen at or below the
    item reorder_level. Sends a WhatsApp alert to low_stock_alert_mobile in
    WhatsApp Settings. Runs via hooks.py scheduler_events -> daily.
    """
    settings = frappe.get_single("WhatsApp Settings")
    if not settings.enabled:
        frappe.logger("whatsapp").info("Low-stock alerts skipped — app disabled.")
        return

    alert_mobile = getattr(settings, "low_stock_alert_mobile", None)
    if not alert_mobile:
        frappe.logger("whatsapp").info("No low_stock_alert_mobile configured — skipping.")
        return

    alert_mobile = normalise_phone(alert_mobile)
    company = frappe.defaults.get_global_default("company") or ""

    low_bins = frappe.db.sql(
        """
        SELECT b.item_code, b.warehouse, b.actual_qty,
               i.item_name, i.stock_uom, i.reorder_level
        FROM `tabBin` b
        INNER JOIN `tabItem` i ON i.name = b.item_code
        WHERE i.reorder_level > 0
          AND b.actual_qty <= i.reorder_level
          AND i.disabled = 0
        ORDER BY b.actual_qty ASC
        LIMIT %(limit)s
        """,
        {"limit": BATCH_SIZE},
        as_dict=True,
    )

    if not low_bins:
        frappe.logger("whatsapp").info("No low-stock items found today.")
        return

    sent = failed = 0
    for row in low_bins:
        message = LOW_STOCK_TEMPLATE.format(
            contact="Warehouse Manager",
            item_name=row.item_name or row.item_code,
            warehouse=row.warehouse,
            current_qty=row.actual_qty,
            uom=row.stock_uom,
            reorder_level=row.reorder_level,
            company=company,
        )
        try:
            _send_with_retry(alert_mobile, message)
            sent += 1
        except Exception as exc:
            frappe.logger("whatsapp").error(f"Low-stock alert failed for {row.item_code}: {exc}")
            failed += 1

    frappe.logger("whatsapp").info(f"Low-stock alerts: {sent} sent, {failed} failed for {len(low_bins)} items.")
