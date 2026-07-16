from __future__ import unicode_literals

import frappe
from frappe.model.document import Document


class JobWorkOrder(Document):
	def validate(self):
		self.update_status_based_on_returns()
		self.validate_close_conditions()

	def on_submit(self):
		self.create_stock_transfer_on_send()

	def on_update_after_submit(self):
		self.reconcile_returns()

	def update_status_based_on_returns(self):
		"""Auto-update status based on child table entries."""
		if not self.is_new() and self.get("job_work_returns"):
			total_sent = self.qty_sent
			total_received = sum(r.qty_received for r in self.job_work_returns if r.qty_received)

			if total_received == 0:
				self.status = "Sent"
			elif total_received < total_sent:
				self.status = "Partially Received"
			elif total_received >= total_sent:
				self.status = "Received"

	def validate_close_conditions(self):
		"""Ensure Fabric Wastage Log exists if wastage > 0 before closing."""
		# Only enforce on transition to Received/Closed, not on re-save
		prev_doc = self.get_doc_before_save()
		if prev_doc and prev_doc.status == self.status:
			return

		total_wastage = sum(r.wastage_qty or 0 for r in self.get("job_work_returns") if r.wastage_qty)

		# If there's wastage, check that a Fabric Wastage Log exists
		if total_wastage > 0 and self.status in ("Received", "Closed"):
			has_fwl = frappe.db.exists("Fabric Wastage Log", {
				"job_work_order": self.name,
				"wastage_qty": [">", 0],
			})
			if not has_fwl:
				frappe.throw(
					frappe._(
						"There is wastage ({0}) recorded in the returns but no Fabric Wastage Log "
						"is linked to this Job Work Order. Please create one before closing."
					).format(total_wastage),
					title=frappe._("Missing Wastage Log"),
				)

	def create_stock_transfer_on_send(self):
		"""Create Stock Entry for material transfer to subcontractor."""
		# Check if column exists before accessing to avoid Unknown Column errors
		if not frappe.db.has_column("Stock Settings", "allow_material_transfer_to_subcontractor"):
			return

		try:
			if frappe.db.get_single_value("Stock Settings", "allow_material_transfer_to_subcontractor"):
				from textile_tracking.textile.api import create_subcontract_transfer

				create_subcontract_transfer(self)
		except Exception:
			pass

	def reconcile_returns(self):
		"""Create Stock Entry for material receipt from subcontractor."""
		if self.status in ("Received", "Partially Received"):
			from textile_tracking.textile.api import create_receipt_entry

			create_receipt_entry(self)
