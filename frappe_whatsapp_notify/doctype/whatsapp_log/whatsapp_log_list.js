// Copyright (c) 2024, Aavatto and contributors
// For license information, please see license.txt

frappe.listview_settings["WhatsApp Log"] = {
	onload: function (listview) {
		// Add a quick filter bar for Status
		listview.page.add_field({
			fieldname: "status",
			label: __("Status"),
			fieldtype: "Select",
			options: "\nSent\nFailed\nPending",
			change: function () {
				const val = this.get_value();
				if (val) {
					listview.filter_area.add([[
						"WhatsApp Log", "status", "=", val
					]]);
				} else {
					listview.filter_area.remove("status");
				}
				listview.refresh();
			},
		});
	},

	get_indicator: function (doc) {
		if (doc.status === "Sent") {
			return [__("Sent"), "green", "status,=,Sent"];
		} else if (doc.status === "Failed") {
			return [__("Failed"), "red", "status,=,Failed"];
		} else if (doc.status === "Pending") {
			return [__("Pending"), "orange", "status,=,Pending"];
		}
		return [__("Unknown"), "grey", "status,=,"];
	},

	formatters: {
		mobile_no: function (value) {
			// Highlight mobile numbers that look malformed (too short)
			if (value && value.replace(/\D/g, "").length < 10) {
				return '<span style="color: var(--red-500);" title="Check mobile number">'
					+ frappe.utils.escape_html(value)
					+ ' &#9888;</span>';
			}
			return frappe.utils.escape_html(value || "");
		},

		sent_at: function (value) {
			if (!value) return "—";
			return frappe.datetime.str_to_user(value);
		},
	},

	// Show a re-send button on Failed rows
	button: {
		show: function (doc) {
			return doc.status === "Failed";
		},
		get_label: function () {
			return __("Retry");
		},
		get_description: function (doc) {
			return __("Retry sending WhatsApp message to {0}", [doc.mobile_no]);
		},
		action: function (doc) {
			frappe.call({
				method: "frappe_whatsapp_notify.api.whatsapp.resend_whatsapp_message",
				args: { log_name: doc.name },
				callback: function (r) {
					if (!r.exc) {
						frappe.show_alert({
							message: __("Message queued for retry"),
							indicator: "green",
						});
						cur_list.refresh();
					}
				},
			});
		},
	},

	// Hide the sidebar count for better readability on small screens
	hide_name_column: false,
};
