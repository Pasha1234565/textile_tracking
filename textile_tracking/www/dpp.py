from __future__ import unicode_literals

import frappe
from frappe import _


def get_context(context):
	"""Build the Digital Product Passport page context."""
	roll_id = frappe.form_dict.get("roll_id") or frappe.form_dict.get("name")

	if not roll_id:
		context.title = _("Digital Product Passport — Not Found")
		context.error = _("No Fabric Roll ID provided.")
		return

	# Fetch the fabric roll with all traceability data
	roll = frappe.db.get_value(
		"Fabric Roll",
		roll_id,
		[
			"name", "roll_number", "status", "source_item",
			"production_stage", "raw_material_batch", "job_work_order",
			"contractor", "length_meters", "width_cm", "weight_kg",
			"grade", "quality_status", "production_date",
		],
		as_dict=True,
	)

	if not roll:
		context.title = _("Digital Product Passport — Not Found")
		context.error = _("Fabric Roll {0} not found.").format(roll_id)
		return

	context.title = _("Digital Product Passport — {0}").format(roll.roll_number or roll.name)

	# Get raw material batch details
	batch = None
	if roll.raw_material_batch:
		batch = frappe.db.get_value(
			"Raw Material Batch",
			roll.raw_material_batch,
			[
				"batch_id", "material_type", "supplier", "origin_country",
				"certification_type", "organic_cert_id", "gots_certified",
				"quality_grade", "received_date",
			],
			as_dict=True,
		)

	# Get JWO details
	jwo = None
	if roll.job_work_order:
		jwo = frappe.db.get_value(
			"Job Work Order",
			roll.job_work_order,
			["name", "subcontract_process", "contractor", "date_sent", "status"],
			as_dict=True,
		)

	# Get process history
	process_history = frappe.db.get_all(
		"Process History Entry",
		filters={"parent": roll.name, "parenttype": "Fabric Roll"},
		fields=["process_name", "contractor", "date_completed", "notes"],
		order_by="idx ASC",
	)

	context.roll = roll
	context.batch = batch
	context.jwo = jwo
	context.process_history = process_history
	context.qr_url = frappe.utils.get_url() + "/dpp/" + roll.name
	context.today_date = frappe.utils.nowdate()
	context.no_cache = 1
	context.parents = [
		{"name": _("Home"), "route": "/"},
		{"name": _("Textile"), "route": "/app/textile-tracking"},
	]
