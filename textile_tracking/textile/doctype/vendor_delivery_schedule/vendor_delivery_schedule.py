from __future__ import unicode_literals

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class VendorDeliverySchedule(Document):
	def validate(self):
		self.track_supplier_updates()

	def on_update_after_submit(self):
		"""Adjust production schedule only after submit and when delivery date actually changes."""
		prev = self.get_doc_before_save()
		if prev:
			old_date = prev.revised_delivery_date or prev.original_delivery_date
			new_date = self.revised_delivery_date or self.original_delivery_date
			if old_date != new_date:
				self.adjust_production_schedule()

	def track_supplier_updates(self):
		"""Track when supplier updates the delivery date."""
		if self.revised_delivery_date and self.revised_delivery_date != self.original_delivery_date:
			user_roles = frappe.get_roles(frappe.session.user)
			if "Supplier" in user_roles:
				self.last_updated_by_supplier = now_datetime()
				self.status = "Delayed" if self.revised_delivery_date > self.original_delivery_date else "Confirmed"

	def adjust_production_schedule(self):
		"""Auto-adjust affected Job Work Orders when delivery dates change.

		Uses frappe.enqueue to avoid nested transactions during document save.
		"""
		if not self.raw_material_batch or self.status not in ("Delayed", "Confirmed"):
			return

		frappe.enqueue(
			"textile_tracking.textile.doctype.vendor_delivery_schedule.vendor_delivery_schedule._adjust_jwo_schedule",
			queue="short",
			raw_material_batch=self.raw_material_batch,
			revised_date=self.revised_delivery_date,
			original_date=self.original_delivery_date,
			now=frappe.flags.in_test,
		)


def _adjust_jwo_schedule(raw_material_batch, revised_date, original_date):
	"""Background job: shift affected JWO expected return dates."""
	if not revised_date or not original_date:
		return

	delay_days = frappe.utils.date_diff(revised_date, original_date)
	if delay_days <= 0:
		return

	affected_jwos = frappe.db.get_all(
		"Job Work Order",
		filters={
			"raw_material_batch": raw_material_batch,
			"status": ["in", ["Draft", "Sent"]],
		},
		fields=["name", "expected_return_date"],
	)

	for jwo in affected_jwos:
		if jwo.expected_return_date:
			new_date = frappe.utils.add_days(jwo.expected_return_date, delay_days)
			frappe.db.set_value("Job Work Order", jwo.name, "expected_return_date", new_date)

			notification = frappe.new_doc("Notification Log")
			notification.for_user = "Administrator"
			notification.title = frappe._("Production Schedule Adjusted")
			notification.subject = frappe._(
				"JWO {0} shifted by {1} day(s) due to supplier delivery update. "
				"New expected return: {2}"
			).format(jwo.name, delay_days, new_date)
			notification.document_type = "Job Work Order"
			notification.document_name = jwo.name
			notification.insert(ignore_permissions=True)

	frappe.db.commit()
