from __future__ import unicode_literals

import os
import sys

import click

import frappe
from frappe.utils import today, add_days, now_datetime


def _init_frappe():
	"""Ensure frappe is initialized and connected for the current site.

	The bench CLI does NOT always call frappe.init() before dispatching
	to custom app commands. This helper detects whether init has been
	done by checking for frappe.local.conf, and if missing, finds the
	site name from sys.argv and calls frappe.init() + frappe.connect().
	"""
	try:
		# Check if frappe is already initialized
		_ = frappe.local.conf
	except AttributeError:
		# frappe.init() hasn't been called — find site from CLI args
		site = None
		for i, arg in enumerate(sys.argv):
			if arg == '--site' and i + 1 < len(sys.argv):
				site = sys.argv[i + 1]
				break
			if arg.startswith('--site='):
				site = arg.split('=', 1)[1]
				break

		if not site:
			site = os.environ.get('FRAPPE_SITE')

		if not site:
			print("❌ Error: Could not determine site name.")
			print("   Usage: bench --site <sitename> insert-demo-data")
			sys.exit(1)

		frappe.init(site=site)

	# Now connect to the database
	frappe.connect()


@click.command("insert-demo-data")
def insert_demo_data_command():
	"""Insert demo data for Textile Tracking app.

	Usage:
		bench --site [site] insert-demo-data
	"""
	_init_frappe()
	try:
		# Phase 1: Core demo data (contractors, JWOs, wastage logs, raw materials, fabric rolls)
		if not frappe.db.sql("SELECT name FROM `tabJob Contractor` LIMIT 1"):
			print("Inserting demo data...")
			_create_demo_contractors_sql()
			frappe.db.commit()

			_create_demo_jwo_sql()
			frappe.db.commit()

			_create_demo_fwl_sql()
			frappe.db.commit()

			_create_demo_raw_material_batches()
			frappe.db.commit()

			_create_demo_fabric_rolls()
			frappe.db.commit()

			print("✅ Demo data inserted successfully!")
		else:
			print("✅ Demo data already exists, skipping Phase 1")

		# Phase 2: Additional feature demo data (looms, patterns, vendor deliveries)
		if not frappe.db.sql("SELECT name FROM `tabLoom` LIMIT 1"):
			print("Inserting demo data for new features...")
			_create_demo_looms()
			frappe.db.commit()

			_create_demo_patterns()
			frappe.db.commit()

			_create_demo_vendor_deliveries()
			frappe.db.commit()

			print("✅ Demo data for new features inserted!")
		else:
			print("✅ New feature demo data already exists, skipping Phase 2")
	finally:
		frappe.destroy()


# Backward compatibility: insert_demo_data() can still be called from console
def insert_demo_data():
	"""Insert core demo data (backward compat entry point).

	Run via bench console:
		import textile_tracking.commands
		textile_tracking.commands.insert_demo_data()
	"""
	_init_frappe()
	try:
		if frappe.db.sql("SELECT name FROM `tabJob Contractor` LIMIT 1"):
			print("✅ Demo data already exists, skipping")
			return
		print("Inserting demo data...")
		_create_demo_contractors_sql()
		frappe.db.commit()
		_create_demo_jwo_sql()
		frappe.db.commit()
		_create_demo_fwl_sql()
		frappe.db.commit()
		_create_demo_raw_material_batches()
		frappe.db.commit()
		_create_demo_fabric_rolls()
		frappe.db.commit()
		print("✅ Demo data inserted successfully!")
	finally:
		frappe.destroy()


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


def _create_demo_raw_material_batches():
	"""Insert demo Raw Material Batches for traceability."""
	now = now_datetime()
	today_date = today()

	# Get or create a demo supplier
	supplier_name = None
	try:
		supplier_name = frappe.db.get_value("Supplier", {}, "name")
		if not supplier_name:
			frappe.db.sql("""
				INSERT INTO `tabSupplier`
					(name, supplier_name, supplier_type, supplier_group,
					 creation, modified, modified_by, owner, docstatus, idx)
				VALUES
					('Organic Cotton Supplier', 'Organic Cotton Supplier', 'Individual', 'All Supplier Groups',
					 %(now)s, %(now)s, 'Administrator', 'Administrator', 0, 0)
			""", {"now": now})
			supplier_name = "Organic Cotton Supplier"
			frappe.db.commit()
			print("  ✅ Created demo Supplier: Organic Cotton Supplier")
	except Exception as e:
		print(f"  ⚠️  Supplier setup skipped: {e}")

	# Try to get UOM
	uom = frappe.db.get_value("UOM", {}, "name") or "Kg"

	batches = [
		{
			"name": "RMB-DEMO-0001",
			"batch_id": "COT-2024-001",
			"material_type": "Cotton",
			"supplier": supplier_name,
			"supplier_batch_no": "SUP-B2024-001",
			"origin_country": "India",
			"certification_type": "GOTS",
			"organic_cert_id": "GOTS-CERT-2024-001",
			"gots_certified": 1,
			"received_date": add_days(today_date, -120),
			"quantity": 5000,
			"uom": uom,
			"quality_grade": "Premium",
			"notes": "Premium organic cotton from Gujarat. GOTS certified.",
		},
		{
			"name": "RMB-DEMO-0002",
			"batch_id": "POLY-2024-001",
			"material_type": "Polyester",
			"supplier": supplier_name,
			"supplier_batch_no": "SUP-B2024-002",
			"origin_country": "China",
			"certification_type": "OEKO-TEX",
			"organic_cert_id": "OEKO-2024-001",
			"gots_certified": 0,
			"received_date": add_days(today_date, -90),
			"quantity": 3000,
			"uom": uom,
			"quality_grade": "Standard A",
			"notes": "Recycled polyester standA from Shanghai Textiles.",
		},
		{
			"name": "RMB-DEMO-0003",
			"batch_id": "COT-2024-002",
			"material_type": "Cotton",
			"supplier": supplier_name,
			"supplier_batch_no": "SUP-B2024-003",
			"origin_country": "Egypt",
			"certification_type": "Fair Trade",
			"organic_cert_id": "FT-2024-001",
			"gots_certified": 0,
			"received_date": add_days(today_date, -60),
			"quantity": 2000,
			"uom": uom,
			"quality_grade": "Premium",
			"notes": "Egyptian long-staple cotton, Fair Trade certified.",
		},
	]

	for idx, b in enumerate(batches, 1):
		frappe.db.sql("""
			INSERT INTO `tabRaw Material Batch`
				(name, naming_series, batch_id, material_type, supplier,
				 supplier_batch_no, origin_country, certification_type,
				 organic_cert_id, gots_certified, received_date,
				 quantity, uom, quality_grade, notes,
				 creation, modified, modified_by, owner, docstatus, idx)
			VALUES
				(%(name)s, 'RMB-DEMO-', %(batch_id)s, %(material_type)s, %(supplier)s,
				 %(supplier_batch_no)s, %(origin_country)s, %(certification_type)s,
				 %(organic_cert_id)s, %(gots_certified)s, %(received_date)s,
				 %(quantity)s, %(uom)s, %(quality_grade)s, %(notes)s,
				 %(now)s, %(now)s, 'Administrator', 'Administrator', 0, %(idx)s)
		""", {**b, "idx": idx, "now": now})
		print(f"  ✅ Created Raw Material Batch: {b['batch_id']}")


def _create_demo_fabric_rolls():
	"""Insert demo Fabric Rolls with traceability links."""
	now = now_datetime()

	# Get JWOs
	jwos = frappe.db.sql(
		"SELECT name, contractor, source_item FROM `tabJob Work Order` LIMIT 3",
		as_dict=True,
	)
	if not jwos:
		print("  ⚠️  No JWOs found for Fabric Rolls")
		return

	# Get raw material batches
	batches = frappe.db.sql(
		"SELECT name, batch_id FROM `tabRaw Material Batch` LIMIT 2",
		as_dict=True,
	)

	rolls = [
		{
			"name": "FBR-DEMO-0001",
			"roll_number": "FBR-2407-001",
			"status": "Completed",
			"source_item": jwos[0].source_item if jwos[0].source_item else None,
			"production_stage": "Finished",
			"raw_material_batch": batches[0].name if len(batches) > 0 else None,
			"job_work_order": jwos[0].name,
			"contractor": jwos[0].contractor,
			"length_meters": 480,
			"width_cm": 150,
			"weight_kg": 72,
			"grade": "A",
			"quality_status": "Passed",
			"production_date": add_days(today(), -5),
		},
		{
			"name": "FBR-DEMO-0002",
			"roll_number": "FBR-2407-002",
			"status": "Completed",
			"source_item": jwos[1].source_item if len(jwos) > 1 and jwos[1].source_item else None,
			"production_stage": "Finished",
			"raw_material_batch": batches[1].name if len(batches) > 1 else None,
			"job_work_order": jwos[1].name if len(jwos) > 1 else None,
			"contractor": jwos[1].contractor if len(jwos) > 1 else None,
			"length_meters": 290,
			"width_cm": 160,
			"weight_kg": 58,
			"grade": "Premium",
			"quality_status": "Passed",
			"production_date": add_days(today(), -3),
		},
	]

	for idx, r in enumerate(rolls, 1):
		frappe.db.sql("""
			INSERT INTO `tabFabric Roll`
				(name, naming_series, roll_number, status, source_item,
				 production_stage, raw_material_batch, job_work_order,
				 contractor, length_meters, width_cm, weight_kg,
				 grade, quality_status, production_date, docstatus,
				 creation, modified, modified_by, owner, idx)
			VALUES
				(%(name)s, 'FBR-DEMO-', %(roll_number)s, %(status)s, %(source_item)s,
				 %(production_stage)s, %(raw_material_batch)s, %(job_work_order)s,
				 %(contractor)s, %(length_meters)s, %(width_cm)s, %(weight_kg)s,
				 %(grade)s, %(quality_status)s, %(production_date)s, 1,
				 %(now)s, %(now)s, 'Administrator', 'Administrator', %(idx)s)
		""", {**r, "idx": idx, "now": now})

		# Add a process history entry for this roll (skip gracefully if table missing)
		if r.get("job_work_order"):
			try:
				frappe.db.sql("""
					INSERT INTO `tabProcess History Entry`
						(name, parent, parenttype, parentfield, idx,
						 process_name, contractor, date_completed, notes,
						 creation, modified, modified_by, owner, docstatus)
					VALUES
						(%(name)s, %(parent)s, 'Fabric Roll', 'process_history', 1,
						 %(process)s, %(contractor)s, %(date)s, %(notes)s,
						 %(now)s, %(now)s, 'Administrator', 'Administrator', 0)
				""", {
					"name": frappe.generate_hash("", 10),
					"parent": r["name"],
					"process": "Weaving",
					"contractor": r["contractor"],
					"date": add_days(today(), -7),
					"notes": "Processed via job work order",
					"now": now,
				})
			except Exception as e:
				frappe.db.rollback()
				print(f"  ⚠️  Process History skipped (table not ready, run bench migrate first): {e}")

		print(f"  ✅ Created Fabric Roll: {r['roll_number']}")


def _create_demo_looms():
	"""Insert demo Looms/Machines."""
	now = now_datetime()

	looms = [
		{"machine_id": "L-001", "machine_type": "Airjet Loom", "status": "Running", "speed_rpm": 800, "location": "Floor 1 - A", "operator_name": "Rajesh Kumar", "max_width_cm": 190, "manufacturer": "Picanol"},
		{"machine_id": "L-002", "machine_type": "Airjet Loom", "status": "Running", "speed_rpm": 750, "location": "Floor 1 - A", "operator_name": "Suresh Patel", "max_width_cm": 190, "manufacturer": "Picanol"},
		{"machine_id": "L-003", "machine_type": "Rapier Loom", "status": "Idle", "speed_rpm": 450, "location": "Floor 1 - B", "operator_name": "Amit Singh", "max_width_cm": 220, "manufacturer": "Toyota"},
		{"machine_id": "L-004", "machine_type": "Rapier Loom", "status": "Under Maintenance", "speed_rpm": 0, "location": "Floor 1 - B", "operator_name": "", "max_width_cm": 220, "manufacturer": "Toyota"},
		{"machine_id": "L-005", "machine_type": "Shuttle Loom", "status": "Running", "speed_rpm": 200, "location": "Floor 2 - A", "operator_name": "Vikram Joshi", "max_width_cm": 160, "manufacturer": "Sulzer"},
		{"machine_id": "L-006", "machine_type": "Dobby Loom", "status": "Running", "speed_rpm": 600, "location": "Floor 2 - B", "operator_name": "Deepak Verma", "max_width_cm": 180, "manufacturer": "RIETER"},
		{"machine_id": "L-007", "machine_type": "Circular Knitting", "status": "Idle", "speed_rpm": 350, "location": "Floor 3", "operator_name": "", "max_width_cm": 200, "manufacturer": "Mayer"},
		{"machine_id": "L-008", "machine_type": "Waterjet Loom", "status": "Running", "speed_rpm": 650, "location": "Floor 1 - C", "operator_name": "Prakash Nair", "max_width_cm": 170, "manufacturer": "Tsudakoma"},
	]

	for loom in looms:
		frappe.db.sql("""
			INSERT INTO `tabLoom`
				(name, machine_id, machine_type, status, speed_rpm,
				 location, operator_name, max_width_cm, manufacturer,
				 creation, modified, modified_by, owner, docstatus, idx)
			VALUES
				(%(machine_id)s, %(machine_id)s, %(machine_type)s, %(status)s, %(speed_rpm)s,
				 %(location)s, %(operator_name)s, %(max_width_cm)s, %(manufacturer)s,
				 %(now)s, %(now)s, 'Administrator', 'Administrator', 0, 1)
		""", {**loom, "now": now})
	print(f"  ✅ Created {len(looms)} Looms/Machines")

	# Add some machine output logs
	for idx, loom in enumerate(looms[:5], 1):
		if loom["status"] == "Running":
			frappe.db.sql("""
				INSERT INTO `tabMachine Output Log`
					(name, naming_series, loom, log_date, shift,
					 meters_produced, runtime_minutes, defect_count,
					 creation, modified, modified_by, owner, docstatus, idx)
				VALUES
					(%(name)s, 'MOL-DEMO-', %(loom)s, %(date)s, 'Morning',
					 %(meters)s, %(runtime)s, %(defects)s,
					 %(now)s, %(now)s, 'Administrator', 'Administrator', 0, 1)
			""", {
				"name": f"MOL-DEMO-{idx:04d}",
				"loom": loom["machine_id"],
				"date": add_days(today(), -1),
				"meters": (idx * 200),
				"runtime": (idx * 360),
				"defects": idx,
				"now": now,
			})
	print("  ✅ Created demo Machine Output Logs")


def _create_demo_patterns():
	"""Insert demo Pattern Template and Cutting Plan."""
	now = now_datetime()
	uom = frappe.db.get_value("UOM", {}, "name") or "Meter"

	# Create a pattern template for a T-Shirt
	frappe.db.sql("""
		INSERT INTO `tabPattern Template`
			(name, naming_series, template_name, total_area_sq_m,
			 creation, modified, modified_by, owner, docstatus, idx)
		VALUES
			('PT-DEMO-0001', 'PT-DEMO-', 'T-Shirt Basic', 1.76,
			 %(now)s, %(now)s, 'Administrator', 'Administrator', 0, 1)
	""", {"now": now})

	# Add pattern pieces
	pieces = [
		("PT-DEMO-0001", "Front Body", 70, 80, 1),
		("PT-DEMO-0001", "Back Body", 70, 80, 1),
		("PT-DEMO-0001", "Sleeve", 55, 60, 2),
		("PT-DEMO-0001", "Collar", 20, 10, 1),
	]
	for idx, (parent, name, w, h, qty) in enumerate(pieces, 1):
		frappe.db.sql("""
			INSERT INTO `tabPattern Piece`
				(name, parent, parenttype, parentfield, idx,
				 piece_name, width_cm, height_cm, qty_per_roll,
				 creation, modified, modified_by, owner, docstatus)
			VALUES
				(%(name)s, %(parent)s, 'Pattern Template', 'pieces', %(idx)s,
				 %(piece)s, %(width)s, %(height)s, %(qty)s,
				 %(now)s, %(now)s, 'Administrator', 'Administrator', 0)
		""", {
			"name": frappe.generate_hash("", 10),
			"parent": parent,
			"idx": idx,
			"piece": piece,
			"width": w,
			"height": h,
			"qty": qty,
			"now": now,
		})

	# Get a fabric roll for the cutting plan
	roll = frappe.db.get_value("Fabric Roll", {"docstatus": 1}, "name")
	if roll:
		frappe.db.sql("""
			INSERT INTO `tabCutting Plan`
				(name, naming_series, cutting_plan_name, fabric_roll,
				 roll_length_meters, roll_width_cm, total_fabric_used, estimated_waste_pct,
				 docstatus,
				 creation, modified, modified_by, owner, idx)
			VALUES
				('CP-DEMO-0001', 'CP-DEMO-', 'T-Shirt Batch 1', %(roll)s,
				 480, 150, 60.5, 12.3, 1,
				 %(now)s, %(now)s, 'Administrator', 'Administrator', 1)
		""", {"roll": roll, "now": now})
		print(f"  ✅ Created demo Cutting Plan for roll: {roll}")

	print("  ✅ Created demo Pattern Template: T-Shirt Basic")


def _create_demo_vendor_deliveries():
	"""Insert demo Vendor Delivery Schedules."""
	now = now_datetime()
	uom = frappe.db.get_value("UOM", {}, "name") or "Kg"

	# Get supplier and batch
	supplier = frappe.db.get_value("Supplier", {}, "name")
	batch = frappe.db.get_value("Raw Material Batch", {}, "name")

	if supplier and batch:
		frappe.db.sql("""
			INSERT INTO `tabVendor Delivery Schedule`
				(name, naming_series, supplier, raw_material_batch,
				 original_delivery_date, qty_expected, uom, status,
				 docstatus,
				 creation, modified, modified_by, owner, idx)
			VALUES
				('VDS-DEMO-0001', 'VDS-DEMO-', %(supplier)s, %(batch)s,
				 %(date)s, 1000, %(uom)s, 'Pending',
				 1,
				 %(now)s, %(now)s, 'Administrator', 'Administrator', 1)
		""", {
			"supplier": supplier,
			"batch": batch,
			"date": add_days(today(), 14),
			"uom": uom,
			"now": now,
		})
		frappe.db.sql("""
			INSERT INTO `tabVendor Delivery Schedule`
				(name, naming_series, supplier, raw_material_batch,
				 original_delivery_date, qty_expected, uom, status,
				 docstatus,
				 creation, modified, modified_by, owner, idx)
			VALUES
				('VDS-DEMO-0002', 'VDS-DEMO-', %(supplier)s, %(batch)s,
				 %(date)s, 500, %(uom)s, 'Confirmed',
				 1,
				 %(now)s, %(now)s, 'Administrator', 'Administrator', 2)
		""", {
			"supplier": supplier,
			"batch": batch,
			"date": add_days(today(), 7),
			"uom": uom,
			"now": now,
		})
		print(f"  ✅ Created demo Vendor Delivery Schedules")


commands = [
	insert_demo_data_command
]
