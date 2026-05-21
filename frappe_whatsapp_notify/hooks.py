app_name = "frappe_whatsapp_notify"
app_title = "Frappe WhatsApp Notify"
app_publisher = "Vishal Parekh"
app_description = "Send WhatsApp notifications from ERPNext via Twilio"
app_email = "vishal@aavatto.com"
app_license = "MIT"
app_version = "1.1.0"

# ------------------------------------------------------------------------
# Fixtures — exported DocTypes bundled with the app
# ------------------------------------------------------------------------
fixtures = [
    {
        "dt": "DocType",
        "filters": [
            ["name", "in", ["WhatsApp Settings", "WhatsApp Log"]],
        ],
    },
    {
        "dt": "Custom Field",
        "filters": [["dt", "in", ["Sales Order", "Sales Invoice", "Payment Entry"]]],
    },
]

# ------------------------------------------------------------------------
# Document Events
# ------------------------------------------------------------------------
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

# ------------------------------------------------------------------------
# Scheduled Tasks
# ------------------------------------------------------------------------
scheduler_events = {
    "daily": [
        "frappe_whatsapp_notify.api.scheduler.send_overdue_payment_reminders",
        "frappe_whatsapp_notify.doctype.whatsapp_log.whatsapp_log.WhatsAppLog.purge_old_logs",
    ],
}
