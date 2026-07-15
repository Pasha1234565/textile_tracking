from __future__ import unicode_literals

import frappe
from frappe.model.document import Document


class FabricRoll(Document):
	def validate(self):
		self.set_roll_number_from_series()
		self.generate_qr_data()

	def on_submit(self):
		self.update_job_work_order_with_roll()

	def on_cancel(self):
		self.clear_job_work_order_roll_reference()

	def set_roll_number_from_series(self):
		"""Auto-generate roll_number from naming series if not provided."""
		if not self.roll_number:
			self.roll_number = self.name

	def generate_qr_data(self):
		"""Generate Digital Product Passport data string for QR code."""
		# Build a URL-friendly passport string
		site_url = frappe.utils.get_url()
		self.qr_code_text = f"{site_url}/dpp/{self.name}"

	def update_job_work_order_with_roll(self):
		"""Link this Fabric Roll back to the Job Work Order for traceability."""
		if self.job_work_order:
			frappe.db.set_value(
				"Job Work Order",
				self.job_work_order,
				"fabric_roll",
				self.name,
			)

	def clear_job_work_order_roll_reference(self):
		"""Clear the fabric_roll reference on the JWO when this roll is cancelled."""
		if self.job_work_order:
			frappe.db.set_value(
				"Job Work Order",
				self.job_work_order,
				"fabric_roll",
				None,
			)
