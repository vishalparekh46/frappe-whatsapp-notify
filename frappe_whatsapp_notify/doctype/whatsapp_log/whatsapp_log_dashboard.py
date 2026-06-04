# Copyright (c) 2024, Aavatto and contributors
# For license information, please see license.txt

from frappe import _


def get_data():
	"""
	Returns the Dashboard configuration for the WhatsApp Log DocType.

	This config drives the "Dashboard" tab visible in the form view of
	every WhatsApp Log record in the ERPNext desk.  It exposes:

	- A Number Card section showing total / sent / failed / pending counts.
	- A quick Timeline showing when the message was sent / retried.
	- Heatmap data to visualise message volume over time.
	"""
	return {
		"fieldname": "whatsapp_log",
		"non_standard_fieldnames": {},
		"transactions": [
			{
				"label": _("Linked Documents"),
				"items": [
					"Sales Invoice",
					"Sales Order",
					"Payment Entry",
				],
			},
		],
		# ------------------------------------------------------------------ #
		# Number Cards — shown at the top of the dashboard                    #
		# ------------------------------------------------------------------ #
		"number_cards": [
			{
				"name": "Total WhatsApp Logs",
				"label": _("Total Messages"),
				"document_type": "WhatsApp Log",
				"filters_json": "[]",
				"function": "Count",
				"aggregate_function_based_on": "name",
				"color": "#2196F3",
			},
			{
				"name": "Sent WhatsApp Logs",
				"label": _("Sent"),
				"document_type": "WhatsApp Log",
				"filters_json": '[["WhatsApp Log","status","=","Sent"]]',
				"function": "Count",
				"aggregate_function_based_on": "name",
				"color": "#4CAF50",
			},
			{
				"name": "Failed WhatsApp Logs",
				"label": _("Failed"),
				"document_type": "WhatsApp Log",
				"filters_json": '[["WhatsApp Log","status","=","Failed"]]',
				"function": "Count",
				"aggregate_function_based_on": "name",
				"color": "#F44336",
			},
			{
				"name": "Pending WhatsApp Logs",
				"label": _("Pending"),
				"document_type": "WhatsApp Log",
				"filters_json": '[["WhatsApp Log","status","=","Pending"]]',
				"function": "Count",
				"aggregate_function_based_on": "name",
				"color": "#FF9800",
			},
		],
		# ------------------------------------------------------------------ #
		# Charts — message volume trend                                        #
		# ------------------------------------------------------------------ #
		"charts": [
			{
				"name": "WhatsApp Message Trend",
				"chart_name": _("Message Volume (Last 30 Days)"),
				"chart_type": "Group By",
				"document_type": "WhatsApp Log",
				"group_by_field": "status",
				"aggregate_function": "Count",
				"color": "#5e64ff",
				"filters_json": "[]",
				"timespan": "Last Month",
				"time_interval": "Daily",
				"based_on": "sent_at",
			},
		],
		# ------------------------------------------------------------------ #
		# Heatmap — activity calendar                                          #
		# ------------------------------------------------------------------ #
		"heatmap": True,
		"heatmap_message": _("This heatmap shows the daily WhatsApp message activity."),
		"heatmap_based_on": "sent_at",
	}
