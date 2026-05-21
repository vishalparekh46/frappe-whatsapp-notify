# Copyright (c) 2024, Aavatto and contributors
# For license information, please see license.txt
"""
Patch v1.1.0 — Install WhatsApp Log DocType

Ensures the WhatsApp Log DocType is present in the database after
upgrading from v1.0.x. Frappe auto-creates tables for new DocTypes
during migrate, but this patch also backfills the default retention
setting so the purge scheduler starts clean.
"""

import frappe


def execute():
    """Run on bench migrate when upgrading to v1.1.0+."""
    # Reload the DocType so Frappe picks up the new JSON definition
    if frappe.db.exists("DocType", "WhatsApp Log"):
        frappe.reload_doc("frappe_whatsapp_notify", "doctype", "whatsapp_log")
    else:
        # First-time install: create the DocType from the bundled JSON
        frappe.reload_doc("frappe_whatsapp_notify", "doctype", "whatsapp_log", force=True)

    # Ensure the WhatsApp Settings singleton has log_messages enabled by default
    if frappe.db.exists("WhatsApp Settings", "WhatsApp Settings"):
        settings = frappe.get_doc("WhatsApp Settings", "WhatsApp Settings")
        if not hasattr(settings, "log_messages") or settings.log_messages is None:
            frappe.db.set_value(
                "WhatsApp Settings",
                "WhatsApp Settings",
                "log_messages",
                1,
                update_modified=False,
            )

    frappe.db.commit()
    frappe.msgprint(
        "WhatsApp Log DocType installed successfully.",
        alert=True,
        indicator="green",
    )
