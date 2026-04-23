app_name = "frappe_whatsapp_notify"
app_title = "Frappe WhatsApp Notify"
app_publisher = "Vishal Parekh"
app_description = "Send WhatsApp notifications from ERPNext via Twilio"
app_email = "vishal@aavatto.com"
app_license = "MIT"

# ---------------------------------------------------------------------------
# Document Events
# ---------------------------------------------------------------------------
doc_events = {
    "Sales Order": {
        "on_submit": "frappe_whatsapp_notify.api.whatsapp.send_sales_order_confirmation",
    },
    "Sales Invoice": {
        "on_submit": "frappe_whatsapp_notify.api.whatsapp.send_invoice_notification",
    },
    "Payment Entry": {
        "on_submit": "frappe_whatsapp_notify.api.whatsapp.send_payment_receipt",
    },
}

# ---------------------------------------------------------------------------
# Scheduled Tasks
# ---------------------------------------------------------------------------
scheduler_events = {
    "daily": [
        "frappe_whatsapp_notify.api.scheduler.send_overdue_payment_reminders",
    ],
}
