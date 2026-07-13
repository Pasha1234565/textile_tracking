from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns = [
		{"label": "Contractor", "fieldname": "contractor", "fieldtype": "Link", "options": "Contractor", "width": 180},
		{"label": "Month", "fieldname": "month", "fieldtype": "Data", "width": 100},
		{"label": "Qty Sent", "fieldname": "qty_sent", "fieldtype": "Float", "width": 120},
		{"label": "Wastage Qty", "fieldname": "wastage_qty", "fieldtype": "Float", "width": 120},
		{"label": "Wastage (%)", "fieldname": "wastage_pct", "fieldtype": "Float", "width": 120}
	]
	
	data = frappe.db.sql("""
		SELECT
			con.name as contractor,
			DATE_FORMAT(fwl.date_logged, '%Y-%m') as month,
			SUM(fwl.qty_sent) as qty_sent,
			SUM(fwl.wastage_qty) as wastage_qty,
			ROUND((SUM(fwl.wastage_qty) / NULLIF(SUM(fwl.qty_sent), 0)) * 100, 2) as wastage_pct
		FROM `tabFabric Wastage Log` fwl
		JOIN `tabContractor` con ON con.name = fwl.contractor
		GROUP BY con.name, DATE_FORMAT(fwl.date_logged, '%Y-%m')
		ORDER BY fwl.date_logged DESC
	""", as_dict=True)
	
	chart = {
		"data": {
			"labels": [d.month for d in data],
			"datasets": [{"name": "Wastage %", "values": [d.wastage_pct for d in data]}]
		},
		"type": "line",
		"line_options": {"regionFill": 1}
	}
	
	return columns, data, None, chart
