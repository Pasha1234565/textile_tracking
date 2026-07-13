from __future__ import unicode_literals

import frappe
from frappe.utils import today, add_days


def execute():
	"""Insert demo data for the Textile Tracking app."""
	if frappe.db.get_all("Contractor", limit=1):
		print("Demo data already exists — skipping")
		return

	create_demo_contractors()
	create_demo_job_work_orders()
	create_demo_fabric_wastage_logs()
	print("Demo data inserted successfully")


def create_demo_contractors():
	"""Create demo contractors with rate cards."""
	contractors = [
		{
			"contractor_name": "Kashmir Stitching Works",
			"contractor_type": "Stitching",
			"status": "Active",
			"default_wastage_allowance_pct": 2.0,
			"email": "info@kashmirstitching.in",
			"phone": "+91-9876543210",
			"rate_card": [
				{"subcontract_process": "Stitching", "rate_per_piece": 15.00, "effective_from": add_days(today(), -60)},
			],
		},
		{
			"contractor_name": "Raj Cutting Services",
			"contractor_type": "Cutting",
			"status": "Active",
			"default_wastage_allowance_pct": 1.5,
			"email": "raj.cutting@example.com",
			"phone": "+91-9876543211",
			"rate_card": [
				{"subcontract_process": "Cutting", "rate_per_piece": 8.00, "effective_from": add_days(today(), -90)},
			],
		},
		{
			"contractor_name": "Sara Dyeing House",
			"contractor_type": "Dyeing",
			"status": "Active",
			"default_wastage_allowance_pct": 3.0,
			"email": "sara.dye@example.com",
			"phone": "+91-9876543212",
			"rate_card": [
				{"subcontract_process": "Dyeing", "rate_per_piece": 12.00, "effective_from": add_days(today(), -45)},
			],
		},
		{
			"contractor_name": "Punjab Embroidery",
			"contractor_type": "Embroidery",
			"status": "Active",
			"default_wastage_allowance_pct": 2.5,
			"email": "info@punjabembroidery.in",
			"phone": "+91-9876543213",
			"rate_card": [
				{"subcontract_process": "Embroidery", "rate_per_piece": 25.00, "effective_from": add_days(today(), -30)},
			],
		},
		{
			"contractor_name": "Finishing Masters",
			"contractor_type": "Finishing",
			"status": "Active",
			"default_wastage_allowance_pct": 1.0,
			"email": "contact@finishingmasters.com",
			"phone": "+91-9876543214",
			"rate_card": [
				{"subcontract_process": "Finishing", "rate_per_piece": 5.00, "effective_from": add_days(today(), -120)},
			],
		},
	]

	for c in contractors:
		rate_card = c.pop("rate_card")
		doc = frappe.get_doc({"doctype": "Contractor", **c})
		doc.insert(ignore_permissions=True)

		for rate in rate_card:
			doc.append("rate_card", {
				"subcontract_process": rate["subcontract_process"],
				"rate_per_piece": rate["rate_per_piece"],
				"effective_from": rate["effective_from"],
			})
		doc.save()
		print(f"Created Contractor: {doc.name}")


def get_or_create_demo_item():
	"""Create a demo Item if it doesn't exist, return its name."""
	item_name = "Cotton Fabric - Demo"
	if frappe.db.exists("Item", item_name):
		return item_name

	# Only create if Item doctype is available (requires ERPNext or similar)
	if frappe.db.exists("DocType", "Item"):
		try:
			item = frappe.get_doc({
				"doctype": "Item",
				"item_code": item_name,
				"item_name": "Cotton Fabric (Demo)",
				"item_group": "Raw Material",
				"stock_uom": "Meter",
				"is_stock_item": 1,
			})
			item.insert(ignore_permissions=True)
			print(f"Created demo Item: {item_name}")
			return item_name
		except Exception as e:
			print(f"Could not create demo Item: {e}")
	return None


def create_demo_job_work_orders():
	"""Create demo Job Work Orders with varied statuses."""
	contractors = frappe.db.get_all("Contractor", pluck="name")
	demo_item = get_or_create_demo_item()

	jwo_data = [
		{
			"contractor": contractors[0],
			"source_item": demo_item,
			"qty_sent": 500,
			"subcontract_process": "Stitching",
			"rate_per_piece": 15.00,
			"date_sent": add_days(today(), -10),
			"expected_return_date": add_days(today(), -2),
			"status": "Sent",
		},
		{
			"contractor": contractors[1],
			"source_item": demo_item,
			"qty_sent": 300,
			"subcontract_process": "Cutting",
			"rate_per_piece": 8.00,
			"date_sent": add_days(today(), -15),
			"expected_return_date": add_days(today(), -5),
			"status": "Partially Received",
			"returns": [
				{"qty_received": 200, "qty_rejected": 10, "wastage_qty": 5, "date_received": add_days(today(), -8)},
			],
		},
		{
			"contractor": contractors[2],
			"source_item": demo_item,
			"qty_sent": 200,
			"subcontract_process": "Dyeing",
			"rate_per_piece": 12.00,
			"date_sent": add_days(today(), -20),
			"expected_return_date": add_days(today(), -10),
			"status": "Received",
			"returns": [
				{"qty_received": 190, "qty_rejected": 5, "wastage_qty": 8, "date_received": add_days(today(), -12)},
			],
		},
		{
			"contractor": contractors[3],
			"source_item": demo_item,
			"qty_sent": 150,
			"subcontract_process": "Embroidery",
			"rate_per_piece": 25.00,
			"date_sent": add_days(today(), -5),
			"expected_return_date": add_days(today(), 5),
			"status": "Draft",
		},
		{
			"contractor": contractors[4],
			"source_item": demo_item,
			"qty_sent": 400,
			"subcontract_process": "Finishing",
			"rate_per_piece": 5.00,
			"date_sent": add_days(today(), -25),
			"expected_return_date": add_days(today(), -15),
			"status": "Closed",
			"returns": [
				{"qty_received": 395, "qty_rejected": 2, "wastage_qty": 3, "date_received": add_days(today(), -18)},
			],
		},
	]

	for jwo in jwo_data:
		returns = jwo.pop("returns", [])
		try:
			doc = frappe.get_doc({"doctype": "Job Work Order", **jwo})
			doc.insert(ignore_permissions=True)

			for ret in returns:
				doc.append("job_work_returns", ret)
			doc.save()
			print(f"Created Job Work Order: {doc.name}")
		except Exception as e:
			frappe.log_error(frappe.get_traceback(), f"Demo JWO creation failed for {jwo.get('contractor')}")
			print(f"Skipping Job Work Order ({jwo.get('contractor')}): {str(e)[:100]}")


def create_demo_fabric_wastage_logs():
	"""Create demo Fabric Wastage Log entries linked to JWO returns."""
	jwos = frappe.db.get_all("Job Work Order", pluck="name", limit=3)

	if not jwos:
		print("No Job Work Orders found, skipping Fabric Wastage Log demo data")
		return

	fwl_data = [
		{
			"job_work_order": jwos[0] if len(jwos) > 0 else None,
			"contractor": frappe.db.get_value("Job Work Order", jwos[0], "contractor") if len(jwos) > 0 else None,
			"date_logged": add_days(today(), -8),
			"qty_sent": 500,
			"wastage_qty": 8.5,
			"wastage_category": "Contractor Damage",
			"remarks": "Stitching defects found during inspection",
		},
		{
			"job_work_order": jwos[1] if len(jwos) > 1 else None,
			"contractor": frappe.db.get_value("Job Work Order", jwos[1], "contractor") if len(jwos) > 1 else None,
			"date_logged": add_days(today(), -12),
			"qty_sent": 300,
			"wastage_qty": 5.0,
			"wastage_category": "Cutting Loss",
			"remarks": "Edge trimming waste within acceptable limits",
		},
		{
			"job_work_order": jwos[2] if len(jwos) > 2 else None,
			"contractor": frappe.db.get_value("Job Work Order", jwos[2], "contractor") if len(jwos) > 2 else None,
			"date_logged": add_days(today(), -12),
			"qty_sent": 200,
			"wastage_qty": 8.0,
			"wastage_category": "Quality Reject",
			"remarks": "Color mismatch in batch 3, entire lot rejected",
		},
	]

	for fwl in fwl_data:
		try:
			doc = frappe.get_doc({"doctype": "Fabric Wastage Log", **fwl})
			doc.insert(ignore_permissions=True)
			print(f"Created Fabric Wastage Log: {doc.name}")
		except Exception as e:
			frappe.log_error(frappe.get_traceback(), f"Demo FWL creation failed")
			print(f"Skipping Fabric Wastage Log: {str(e)[:100]}")
