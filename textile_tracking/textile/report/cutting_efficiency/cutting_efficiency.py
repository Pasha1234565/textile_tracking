from __future__ import unicode_literals

import frappe
from frappe import _


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	chart = get_chart(data)
	return columns, data, None, chart


def get_columns():
	return [
		{"label": _("Cutting Plan"), "fieldname": "cutting_plan", "fieldtype": "Link", "options": "Cutting Plan", "width": 150},
		{"label": _("Fabric Roll"), "fieldname": "fabric_roll", "fieldtype": "Link", "options": "Fabric Roll", "width": 150},
		{"label": _("Roll Length (m)"), "fieldname": "roll_length", "fieldtype": "Float", "width": 100},
		{"label": _("Roll Width (cm)"), "fieldname": "roll_width", "fieldtype": "Float", "width": 100},
		{"label": _("Total Area (sq m)"), "fieldname": "total_area", "fieldtype": "Float", "width": 120},
		{"label": _("Fabric Used (sq m)"), "fieldname": "fabric_used", "fieldtype": "Float", "width": 130},
		{"label": _("Est. Waste (%)"), "fieldname": "est_waste_pct", "fieldtype": "Percent", "width": 110},
		{"label": _("Created On"), "fieldname": "creation_date", "fieldtype": "Date", "width": 100},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 100},
	]


def get_data(filters):
	conditions = []
	params = {}

	if filters.get("fabric_roll"):
		conditions.append("cp.fabric_roll = %(fabric_roll)s")
		params["fabric_roll"] = filters["fabric_roll"]

	if filters.get("from_date"):
		conditions.append("cp.creation >= %(from_date)s")
		params["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions.append("cp.creation <= %(to_date)s")
		params["to_date"] = filters["to_date"] + " 23:59:59"

	where_clause = " AND ".join(conditions) if conditions else "1=1"

	data = frappe.db.sql(f"""
		SELECT
			cp.name as cutting_plan,
			cp.fabric_roll,
			cp.roll_length_meters as roll_length,
			cp.roll_width_cm as roll_width,
			ROUND((cp.roll_length_meters * cp.roll_width_cm) / 100, 2) as total_area,
			cp.total_fabric_used as fabric_used,
			cp.estimated_waste_pct as est_waste_pct,
			DATE(cp.creation) as creation_date,
			cp.docstatus
		FROM `tabCutting Plan` cp
		WHERE {where_clause}
		ORDER BY cp.creation DESC
	""", params, as_dict=True)

	for row in data:
		row.status = "Draft" if row.docstatus == 0 else ("Submitted" if row.docstatus == 1 else "Cancelled")

	return data


def get_chart(data):
	if not data:
		return None

	labels = [d.cutting_plan for d in data]
	return {
		"data": {
			"labels": labels,
			"datasets": [
				{"name": _("Est. Waste (%)"), "values": [d.est_waste_pct or 0 for d in data]},
				{"name": _("Fabric Used (sq m)"), "values": [d.fabric_used or 0 for d in data]},
			],
		},
		"type": "bar",
		"colors": ["#ff6b6b", "#2490ef"],
		"bar_options": {"stacked": 0},
	}
