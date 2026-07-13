from __future__ import unicode_literals

import frappe
from frappe.utils import today, add_days, now_datetime


def insert_demo_data():
	"""Insert demo data using direct SQL to bypass DocType controller issues.

	Run via bench console:
		import textile_tracking.commands
		textile_tracking.commands.insert_demo_data()
	"""
	# Check if demo data already exists
	existing = frappe.db.sql("SELECT name FROM `tabJob Contractor` LIMIT 1")
	if existing:
		print("✅ Demo data already exists, skipping")
		return

	print("Inserting demo data...")
	_create_demo_contractors_sql()
	frappe.db.commit()

	_create_demo_jwo_sql()
	frappe.db.commit()

	_create_demo_fwl_sql()
	frappe.db.commit()

	print("✅ Demo data inserted successfully!")


def _create_demo_contractors_sql():
	"""Insert demo contractors using raw SQL."""
	now = now_datetime()
	today_date = today()

	contractors = [
		{
			"name": "Kashmir Stitching Works",
			"contractor_name": "Kashmir Stitching Works",
			"contractor_type": "Stitching",
			"status": "Active",
			"default_wastage_allowance_pct": 2.0,
			"email": "info@kashmirstitching.in",
			"phone": "+91-9876543210",
		},
		{
			"name": "Raj Cutting Services",
			"contractor_name": "Raj Cutting Services",
			"contractor_type": "Cutting",
			"status": "Active",
			"default_wastage_allowance_pct": 1.5,
			"email": "raj.cutting@example.com",
			"phone": "+91-9876543211",
		},
		{
			"name": "Sara Dyeing House",
			"contractor_name": "Sara Dyeing House",
			"contractor_type": "Dyeing",
			"status": "Active",
			"default_wastage_allowance_pct": 3.0,
			"email": "sara.dye@example.com",
			"phone": "+91-9876543212",
		},
		{
			"name": "Punjab Embroidery",
			"contractor_name": "Punjab Embroidery",
			"contractor_type": "Embroidery",
			"status": "Active",
			"default_wastage_allowance_pct": 2.5,
			"email": "info@punjabembroidery.in",
			"phone": "+91-9876543213",
		},
		{
			"name": "Finishing Masters",
			"contractor_name": "Finishing Masters",
			"contractor_type": "Finishing",
			"status": "Active",
			"default_wastage_allowance_pct": 1.0,
			"email": "contact@finishingmasters.com",
			"phone": "+91-9876543214",
		},
	]

	for c in contractors:
		frappe.db.sql("""
			INSERT INTO `tabJob Contractor`
				(name, contractor_name, contractor_type, status,
				 default_wastage_allowance_pct, email, phone,
				 creation, modified, modified_by, owner, docstatus, idx)
			VALUES
				(%(name)s, %(contractor_name)s, %(contractor_type)s, %(status)s,
				 %(default_wastage_allowance_pct)s, %(email)s, %(phone)s,
				 %(now)s, %(now)s, 'Administrator', 'Administrator', 0, 0)
		""", {**c, "now": now})
		print(f"  ✅ Created Contractor: {c['name']}")

	# Commit contractors first so they survive any subsequent transaction failure
	frappe.db.commit()

	# Try to add rate card items (may fail if child table is incomplete from migration)
	try:
		rates = [
			("Kashmir Stitching Works", "Stitching", 15.00, add_days(today_date, -60)),
			("Raj Cutting Services", "Cutting", 8.00, add_days(today_date, -90)),
			("Sara Dyeing House", "Dyeing", 12.00, add_days(today_date, -45)),
			("Punjab Embroidery", "Embroidery", 25.00, add_days(today_date, -30)),
			("Finishing Masters", "Finishing", 5.00, add_days(today_date, -120)),
		]

		for idx, (contractor, process, rate, eff_date) in enumerate(rates, 1):
			frappe.db.sql("""
				INSERT INTO `tabContractor Rate Item`
					(name, parent, parenttype, parentfield, idx,
					 subcontract_process, rate_per_piece, effective_from,
					 creation, modified, modified_by, owner, docstatus)
				VALUES
					(%(name)s, %(parent)s, 'Job Contractor', 'rate_card', %(idx)s,
					 %(process)s, %(rate)s, %(eff_date)s,
					 %(now)s, %(now)s, 'Administrator', 'Administrator', 0)
			""", {
				"name": frappe.generate_hash("", 10),
				"parent": contractor,
				"idx": idx,
				"process": process,
				"rate": rate,
				"eff_date": eff_date,
				"now": now,
			})
		frappe.db.commit()
		print("  ✅ Added rate card items")
	except Exception as e:
		frappe.db.rollback()  # Required to clear MySQL aborted transaction state
		print(f"  ⚠️  Rate cards skipped (child table needs repair): {e}")


def _create_demo_jwo_sql():
	"""Insert demo Job Work Orders using raw SQL."""
	now = now_datetime()
	today_date = today()

	contractors = [r[0] for r in frappe.db.sql(
		"SELECT name FROM `tabJob Contractor` ORDER BY name"
	)]
	if len(contractors) < 5:
		print("  ⚠️  Not enough contractors")
		return

	demo_item = None
	if frappe.db.exists("DocType", "Item"):
		try:
			item_group = frappe.db.get_value("Item Group", {}, "name") or "All Item Groups"
			frappe.db.sql("""
				INSERT INTO `tabItem`
					(name, item_code, item_name, item_group, stock_uom,
					 is_stock_item, creation, modified, modified_by, owner, docstatus, idx)
				VALUES
					('Cotton Fabric - Demo', 'Cotton Fabric - Demo', 'Cotton Fabric (Demo)',
					 %(item_group)s, 'Meter', 1,
					 %(now)s, %(now)s, 'Administrator', 'Administrator', 0, 0)
			""", {"item_group": item_group, "now": now})
			demo_item = "Cotton Fabric - Demo"
			print("  ✅ Created demo Item: Cotton Fabric - Demo")
		except Exception as e:
			print(f"  ⚠️  Demo item creation skipped: {e}")

	jwos = [
		(contractors[0], demo_item, 500, "Stitching", 15.00,
		 add_days(today_date, -10), add_days(today_date, -2), "Sent"),
		(contractors[1], demo_item, 300, "Cutting", 8.00,
		 add_days(today_date, -15), add_days(today_date, -5), "Sent"),
		(contractors[2], demo_item, 200, "Dyeing", 12.00,
		 add_days(today_date, -20), add_days(today_date, -10), "Sent"),
		(contractors[3], demo_item, 150, "Embroidery", 25.00,
		 add_days(today_date, -5), add_days(today_date, 5), "Draft"),
		(contractors[4], demo_item, 400, "Finishing", 5.00,
		 add_days(today_date, -25), add_days(today_date, -15), "Sent"),
	]

	for idx, (contractor, item, qty, process, rate, sent, expected, status) in enumerate(jwos, 1):
		jwo_name = f"JWO-DEMO-{idx:04d}"
		frappe.db.sql("""
			INSERT INTO `tabJob Work Order`
				(name, naming_series, contractor, source_item, qty_sent,
				 subcontract_process, rate_per_piece, date_sent,
				 expected_return_date, status,
				 creation, modified, modified_by, owner, docstatus, idx)
			VALUES
				(%(name)s, 'JWO-DEMO-', %(contractor)s, %(item)s, %(qty)s,
				 %(process)s, %(rate)s, %(sent)s,
				 %(expected)s, %(status)s,
				 %(now)s, %(now)s, 'Administrator', 'Administrator', 0, 0)
		""", {
			"name": jwo_name,
			"contractor": contractor,
			"item": item,
			"qty": qty,
			"process": process,
			"rate": rate,
			"sent": sent,
			"expected": expected,
			"status": status,
			"now": now,
		})
		print(f"  ✅ Created Job Work Order: {jwo_name} ({contractor})")


def _create_demo_fwl_sql():
	"""Insert demo Fabric Wastage Logs using raw SQL."""
	now = now_datetime()

	jwos = [r[0] for r in frappe.db.sql(
		"SELECT name FROM `tabJob Work Order` LIMIT 3"
	)]
	if not jwos:
		print("  ⚠️  No JWOs found")
		return

	fwl_records = [
		(jwos[0], 500, 8.5, "Contractor Damage",
		 "Stitching defects found during inspection", add_days(today(), -8)),
		(jwos[1] if len(jwos) > 1 else None, 300, 5.0, "Cutting Loss",
		 "Edge trimming waste within acceptable limits", add_days(today(), -12)),
		(jwos[2] if len(jwos) > 2 else None, 200, 8.0, "Quality Reject",
		 "Color mismatch in batch 3, entire lot rejected", add_days(today(), -12)),
	]

	for idx, (jwo, qty_sent, waste_qty, category, remarks, date_logged) in enumerate(fwl_records, 1):
		if not jwo:
			continue
		contractor = frappe.db.get_value("Job Work Order", jwo, "contractor")
		waste_pct = round((waste_qty / qty_sent) * 100, 2) if qty_sent > 0 else 0
		fwl_name = f"FWL-DEMO-{idx:04d}"

		frappe.db.sql("""
			INSERT INTO `tabFabric Wastage Log`
				(name, naming_series, job_work_order, contractor,
				 date_logged, qty_sent, wastage_qty, wastage_pct,
				 wastage_category, remarks,
				 creation, modified, modified_by, owner, docstatus, idx)
			VALUES
				(%(name)s, 'FWL-DEMO-', %(jwo)s, %(contractor)s,
				 %(date)s, %(qty_sent)s, %(waste_qty)s, %(waste_pct)s,
				 %(cat)s, %(remarks)s,
				 %(now)s, %(now)s, 'Administrator', 'Administrator', 0, 0)
		""", {
			"name": fwl_name,
			"jwo": jwo,
			"contractor": contractor,
			"date": date_logged,
			"qty_sent": qty_sent,
			"waste_qty": waste_qty,
			"waste_pct": waste_pct,
			"cat": category,
			"remarks": remarks,
			"now": now,
		})
		print(f"  ✅ Created Fabric Wastage Log: {fwl_name}")
