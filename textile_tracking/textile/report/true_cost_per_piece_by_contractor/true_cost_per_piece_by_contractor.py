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
		{"label": _("Job Contractor"), "fieldname": "contractor", "fieldtype": "Link", "options": "Job Contractor", "width": 180},
		{"label": _("Process"), "fieldname": "process_name", "fieldtype": "Data", "width": 150},
		{"label": _("Total Qty Sent"), "fieldname": "total_qty_sent", "fieldtype": "Float", "width": 120},
		{"label": _("Total Qty Received"), "fieldname": "total_qty_received", "fieldtype": "Float", "width": 130},
		{"label": _("Total Wastage Qty"), "fieldname": "total_wastage_qty", "fieldtype": "Float", "width": 130},
		{"label": _("Wastage %"), "fieldname": "wastage_pct", "fieldtype": "Percent", "width": 100},
		{"label": _("Rate Per Piece"), "fieldname": "rate_per_piece", "fieldtype": "Currency", "width": 120},
		{"label": _("Labor Cost"), "fieldname": "labor_cost", "fieldtype": "Currency", "width": 120},
		{"label": _("Wastage Cost"), "fieldname": "wastage_cost", "fieldtype": "Currency", "width": 120},
		{"label": _("True Cost Per Piece"), "fieldname": "true_cost_per_piece", "fieldtype": "Currency", "width": 150},
	]


def get_data(filters):
	conditions = []
	params = {}

	if filters.get("contractor"):
		conditions.append("jwp.contractor = %(contractor)s")
		params["contractor"] = filters["contractor"]

	if filters.get("process_name"):
		conditions.append("jwp.process_name = %(process_name)s")
		params["process_name"] = filters["process_name"]

	if filters.get("from_date"):
		conditions.append("jwp.date_sent >= %(from_date)s")
		params["from_date"] = filters["from_date"]

	if filters.get("to_date"):
		conditions.append("jwp.date_sent <= %(to_date)s")
		params["to_date"] = filters["to_date"]

	where_clause = " AND ".join(conditions) if conditions else "1=1"

	# Get rate card rate for each contractor+process
	raw_data = frappe.db.sql(f"""
		SELECT
			jwp.contractor,
			jwp.process_name,
			SUM(jwp.qty_sent) as total_qty_sent,
			COALESCE(SUM(jwr.qty_received), 0) as total_qty_received,
			COALESCE(SUM(jwr.wastage_qty), 0) as total_wastage_qty,
			AVG(jwp.rate_per_piece) as rate_per_piece
		FROM `tabJob Work Order Process` jwp
		INNER JOIN `tabJob Work Order` jwo ON jwo.name = jwp.parent AND jwp.parenttype = 'Job Work Order'
		LEFT JOIN `tabJob Work Return` jwr ON jwr.parent = jwo.name AND jwr.parenttype = 'Job Work Order'
		WHERE {where_clause}
		GROUP BY jwp.contractor, jwp.process_name
		ORDER BY jwp.contractor, jwp.process_name
	""", params, as_dict=True)

	# Get raw material cost from item valuation
	data = []
	for row in raw_data:
		qty_received = row.total_qty_received
		wastage_qty = row.total_wastage_qty
		wastage_pct = 0
		if row.total_qty_sent > 0:
			wastage_pct = round((wastage_qty / row.total_qty_sent) * 100, 2)

		# Get source item from any JWO linked to this contractor+process
		source_item = frappe.db.get_value(
			"Job Work Order",
			{"name": frappe.db.get_value("Job Work Order Process", {"contractor": row.contractor, "process_name": row.process_name}, "parent")},
			"source_item"
		)
		avg_raw_material_rate = frappe.db.get_value(
			"Item", {"name": source_item}, "valuation_rate"
		) or 0

		labor_cost = qty_received * row.rate_per_piece
		wastage_cost = wastage_qty * avg_raw_material_rate
		total_cost = labor_cost + wastage_cost
		true_cost_per_piece = round(total_cost / qty_received, 2) if qty_received > 0 else 0

		data.append({
			"contractor": row.contractor,
			"process_name": row.process_name,
			"total_qty_sent": row.total_qty_sent,
			"total_qty_received": qty_received,
			"total_wastage_qty": wastage_qty,
			"wastage_pct": wastage_pct,
			"rate_per_piece": row.rate_per_piece,
			"labor_cost": labor_cost,
			"wastage_cost": wastage_cost,
			"true_cost_per_piece": true_cost_per_piece,
		})

	return data


def get_chart(data):
	if not data:
		return None

	labels = [d.contractor for d in data]
	return {
		"data": {
			"labels": labels,
			"datasets": [
				{"name": _("Rate Per Piece"), "values": [d.rate_per_piece for d in data]},
				{"name": _("True Cost Per Piece"), "values": [d.true_cost_per_piece for d in data]},
			],
		},
		"type": "bar",
		"colors": ["#2490ef", "#ff6b6b"],
		"bar_options": {"stacked": 0},
	}
