from __future__ import unicode_literals

import frappe
from frappe.utils import today, add_days


def insert_demo_data():
	"""Insert demo data for the Textile Tracking app.

	Run this via:
		bench --site mysite.localhost execute textile_tracking.commands.insert_demo_data
	"""
	_contractors = _create_demo_contractors()
	frappe.db.commit()

	_jwos = _create_demo_job_work_orders(_contractors)
	frappe.db.commit()

	_create_demo_fabric_wastage_logs(_jwos)
	frappe.db.commit()

	print("✅ Demo data inserted successfully!")


def _create_demo_contractors():
	"""Create demo contractors with rate cards."""
	contractors_data = [
		{
			"contractor_name": "Kashmir Stitching Works",
			"contractor_type": "Stitching",
			"status": "Active",
			"default_wastage_allowance_pct": 2.0,
			"email": "info@kashmirstitching.in",
			"phone": "+91-9876543210",
			"rates": [
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
			"rates": [
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
			"rates": [
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
			"rates": [
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
			"rates": [
				{"subcontract_process": "Finishing", "rate_per_piece": 5.00, "effective_from": add_days(today(), -120)},
			],
		},
	]

	created = []
	for data in contractors_data:
		name = data["contractor_name"]
		if frappe.db.exists("Job Contractor", name):
			print(f"  ⏩ Job Contractor '{name}' already exists — skipping")
			created.append(name)
			continue

		rates = data.pop("rates")
		# Pass child table data directly on creation to avoid missing 'parent' column issues
		doc_data = {"doctype": "Job Contractor", **data, "rate_card": rates}
		doc = frappe.get_doc(doc_data)
		doc.insert(ignore_permissions=True)
		created.append(name)
		print(f"  ✅ Created Job Contractor: {name}")

	return created


def _create_demo_job_work_orders(contractors):
	"""Create demo Job Work Orders with varied statuses."""
	if len(contractors) < 5:
		print("  ⚠️  Not enough contractors for JWO demo data")
		return []

	# Try to find or create a demo Item
	demo_item = _get_demo_item()

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
			"status": "Sent",
		},
		{
			"contractor": contractors[2],
			"source_item": demo_item,
			"qty_sent": 200,
			"subcontract_process": "Dyeing",
			"rate_per_piece": 12.00,
			"date_sent": add_days(today(), -20),
			"expected_return_date": add_days(today(), -10),
			"status": "Sent",
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
			"status": "Sent",
		},
	]

	created = []
	for data in jwo_data:
		try:
			jwo = frappe.get_doc({"doctype": "Job Work Order", **data})
			jwo.insert(ignore_permissions=True)
			created.append(jwo.name)
			print(f"  ✅ Created Job Work Order: {jwo.name} ({data['contractor']})")
		except Exception as e:
			import traceback
			frappe.log_error(frappe.get_traceback(), f"Demo JWO creation failed")
			print(f"  ❌ Failed JWO for {data['contractor']}: {e}")

	return created


def _create_demo_fabric_wastage_logs(jwos):
	"""Create demo Fabric Wastage Log entries linked to JWO."""
	if not jwos:
		print("  ⚠️  No JWO records to link FWL entries")
		return

	# Get contractors from the first few JWOs
	jwo_contractors = []
	for jwo_name in jwos[:3]:
		c = frappe.db.get_value("Job Work Order", jwo_name, "contractor")
		jwo_contractors.append((jwo_name, c))

	fwl_data = [
		{
			"job_work_order": jwo_contractors[0][0] if len(jwo_contractors) > 0 else None,
			"contractor": jwo_contractors[0][1] if len(jwo_contractors) > 0 else None,
			"date_logged": add_days(today(), -8),
			"qty_sent": 500,
			"wastage_qty": 8.5,
			"wastage_category": "Contractor Damage",
			"remarks": "Stitching defects found during inspection",
		},
		{
			"job_work_order": jwo_contractors[1][0] if len(jwo_contractors) > 1 else None,
			"contractor": jwo_contractors[1][1] if len(jwo_contractors) > 1 else None,
			"date_logged": add_days(today(), -12),
			"qty_sent": 300,
			"wastage_qty": 5.0,
			"wastage_category": "Cutting Loss",
			"remarks": "Edge trimming waste within acceptable limits",
		},
		{
			"job_work_order": jwo_contractors[2][0] if len(jwo_contractors) > 2 else None,
			"contractor": jwo_contractors[2][1] if len(jwo_contractors) > 2 else None,
			"date_logged": add_days(today(), -12),
			"qty_sent": 200,
			"wastage_qty": 8.0,
			"wastage_category": "Quality Reject",
			"remarks": "Color mismatch in batch 3, entire lot rejected",
		},
	]

	for data in fwl_data:
		try:
			fwl = frappe.get_doc({"doctype": "Fabric Wastage Log", **data})
			fwl.insert(ignore_permissions=True)
			print(f"  ✅ Created Fabric Wastage Log: {fwl.name}")
		except Exception as e:
			frappe.log_error(frappe.get_traceback(), "Demo FWL creation failed")
			print(f"  ❌ Failed FWL: {e}")


def _get_demo_item():
	"""Find or create a demo Item for job work orders."""
	item_name = "Cotton Fabric - Demo"

	if frappe.db.exists("Item", item_name):
		return item_name

	if not frappe.db.exists("DocType", "Item"):
		print("  ⚠️  Item DocType not found — JWO source_item will be empty")
		return None

	try:
		item_group = frappe.db.get_value("Item Group", {}, "name") or "All Item Groups"
		item = frappe.get_doc({
			"doctype": "Item",
			"item_code": item_name,
			"item_name": "Cotton Fabric (Demo)",
			"item_group": item_group,
			"stock_uom": "Meter",
			"is_stock_item": 1,
		})
		item.insert(ignore_permissions=True)
		print(f"  ✅ Created demo Item: {item_name}")
		return item_name
	except Exception as e:
		print(f"  ⚠️  Could not create demo Item: {e}")
		return None
