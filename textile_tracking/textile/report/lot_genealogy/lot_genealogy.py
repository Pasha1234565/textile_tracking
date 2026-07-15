from __future__ import unicode_literals

import frappe
from frappe import _


def execute(filters=None):
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{"label": _("Type"), "fieldname": "doc_type", "fieldtype": "Data", "width": 100},
		{"label": _("ID"), "fieldname": "doc_name", "fieldtype": "Dynamic Link", "options": "doc_type", "width": 200},
		{"label": _("Material / Item"), "fieldname": "material_name", "fieldtype": "Data", "width": 200},
		{"label": _("Supplier / Contractor"), "fieldname": "party", "fieldtype": "Data", "width": 180},
		{"label": _("Quantity"), "fieldname": "quantity", "fieldtype": "Float", "width": 120},
		{"label": _("Date"), "fieldname": "date", "fieldtype": "Date", "width": 120},
		{"label": _("Grade / Status"), "fieldname": "grade_status", "fieldtype": "Data", "width": 120},
		{"label": _("Certification"), "fieldname": "certification", "fieldtype": "Data", "width": 150},
		{"label": _("Level"), "fieldname": "level", "fieldtype": "Int", "width": 60},
	]


def get_data(filters):
	"""Build a traceability tree from raw material batch to fabric rolls."""
	data = []

	batch_name = filters.get("raw_material_batch")
	roll_name = filters.get("fabric_roll")

	# Case 1: Start from a specific Fabric Roll, trace back to its raw material
	if roll_name:
		roll = frappe.db.get_value(
			"Fabric Roll",
			roll_name,
			["name", "roll_number", "source_item", "contractor",
			 "length_meters", "production_date", "grade", "quality_status",
			 "raw_material_batch"],
			as_dict=True,
		)
		if roll:
			data.append({
				"doc_type": "Fabric Roll",
				"doc_name": roll.name,
				"material_name": roll.source_item or roll.roll_number,
				"party": roll.contractor or "",
				"quantity": roll.length_meters,
				"date": roll.production_date,
				"grade_status": _("{0} / {1}").format(roll.grade or "-", roll.quality_status or "-"),
				"certification": "",
				"level": 1,
			})

			# Trace back to raw material batch
			if roll.raw_material_batch:
				add_batch_info(data, roll.raw_material_batch, level=2)

		return data

	# Case 2: Start from a Raw Material Batch, trace forward to all Fabric Rolls
	if batch_name:
		add_batch_info(data, batch_name, level=1)

		# Find all Fabric Rolls that use this batch
		rolls = frappe.db.get_all(
			"Fabric Roll",
			filters={"raw_material_batch": batch_name, "docstatus": 1},
			fields=["name", "roll_number", "source_item", "contractor",
					"length_meters", "production_date", "grade", "quality_status"],
		)
		for r in rolls:
			data.append({
				"doc_type": "Fabric Roll",
				"doc_name": r.name,
				"material_name": r.source_item or r.roll_number,
				"party": r.contractor or "",
				"quantity": r.length_meters,
				"date": r.production_date,
				"grade_status": _("{0} / {1}").format(r.grade or "-", r.quality_status or "-"),
				"certification": "",
				"level": 2,
			})

		return data

	# Case 3: No filter — show all batches with their roll counts
	batches = frappe.db.get_all(
		"Raw Material Batch",
		fields=["name", "batch_id", "material_type", "supplier",
				"quantity", "received_date", "quality_grade", "certification_type",
				"origin_country"],
		order_by="received_date DESC",
		limit=50,
	)
	for b in batches:
		roll_count = frappe.db.count("Fabric Roll", {
			"raw_material_batch": b.name,
			"docstatus": 1,
		})
		cert_parts = [c for c in [b.certification_type, b.origin_country] if c]
		data.append({
			"doc_type": "Raw Material Batch",
			"doc_name": b.name,
			"material_name": _("{0} - {1}").format(b.material_type or "", b.batch_id or ""),
			"party": b.supplier or "",
			"quantity": b.quantity,
			"date": b.received_date,
			"grade_status": b.quality_grade or "",
			"certification": " | ".join(cert_parts),
			"level": 1,
			"roll_count": roll_count,
		})

	return data


def add_batch_info(data, batch_name, level=1):
	"""Add raw material batch details to the report data."""
	batch = frappe.db.get_value(
		"Raw Material Batch",
		batch_name,
		["name", "batch_id", "material_type", "supplier",
		 "quantity", "uom", "received_date", "quality_grade",
		 "certification_type", "origin_country", "organic_cert_id"],
		as_dict=True,
	)
	if not batch:
		return

	cert_parts = [c for c in [batch.certification_type, batch.origin_country] if c]
	cert_str = " | ".join(cert_parts)
	if batch.organic_cert_id:
		cert_str += _(" (Cert: {0})").format(batch.organic_cert_id)

	data.append({
		"doc_type": "Raw Material Batch",
		"doc_name": batch.name,
		"material_name": _("{0} - {1}").format(batch.material_type or "", batch.batch_id or ""),
		"party": batch.supplier or "",
		"quantity": batch.quantity,
		"date": batch.received_date,
		"grade_status": batch.quality_grade or "",
		"certification": cert_str,
		"level": level,
	})
