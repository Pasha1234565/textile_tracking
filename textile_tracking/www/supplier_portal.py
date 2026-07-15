from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import today


def get_context(context):
	"""Build supplier portal context."""
	context.title = _("Supplier Portal")
	context.no_cache = 1
	context.today_date = today()
	context.csrf_token = frappe.sessions.get_csrf_token()

	# Check if user is logged in
	if frappe.session.user == "Guest":
		context.login_required = True
		return

	user_roles = frappe.get_roles(frappe.session.user)
	context.is_supplier = "Supplier" in user_roles

	# Find the supplier linked to this user
	supplier = None
	if context.is_supplier:
		supplier = frappe.db.get_value(
			"Supplier",
			{"email": frappe.session.user},
			["name", "supplier_name"],
			as_dict=True,
		)
		if not supplier:
			# Try finding by email ID field
			supplier = frappe.db.get_value(
				"Supplier",
				{"email_id": frappe.session.user},
				["name", "supplier_name"],
				as_dict=True,
			)

	if supplier:
		context.supplier = supplier
		# Get this supplier's delivery schedules
		deliveries = frappe.db.get_all(
			"Vendor Delivery Schedule",
			filters={"supplier": supplier.name},
			fields=[
				"name", "raw_material_batch", "original_delivery_date",
				"revised_delivery_date", "qty_expected", "uom",
				"status", "supplier_notes", "last_updated_by_supplier",
			],
			order_by="creation DESC",
		)
		context.deliveries = deliveries
		context.delivery_count = len(deliveries)

		# Pending deliveries count
		context.pending_count = frappe.db.count(
			"Vendor Delivery Schedule",
			{"supplier": supplier.name, "status": ["in", ["Pending", "Confirmed"]]},
		)
	else:
		context.no_supplier_link = True
		context.deliveries = []
		context.delivery_count = 0
		context.pending_count = 0
