from __future__ import unicode_literals

import frappe
from frappe.model.document import Document


# Mapping: Garment Type -> List of processes (in order)
GARMENT_PROCESS_MAP = {
	"Shirt": ["Cutting", "Stitching", "Finishing"],
	"T-Shirt": ["Cutting", "Stitching", "Finishing"],
	"Skirt": ["Cutting", "Stitching", "Finishing"],
	"Saree": ["Cutting", "Stitching", "Dyeing", "Embroidery", "Finishing"],
	"Blouse": ["Cutting", "Stitching", "Finishing"],
	"Kurta": ["Cutting", "Stitching", "Finishing"],
	"Jeans": ["Cutting", "Stitching", "Dyeing", "Finishing"],
	"Dress": ["Cutting", "Stitching", "Embroidery", "Finishing"],
	"Dupatta": ["Cutting", "Dyeing", "Finishing"],
	"Fabrics (Roll)": ["Dyeing", "Finishing"],
}


class JobWorkOrder(Document):
	def validate(self):
		self.auto_populate_processes()
		self.validate_processes_required()
		self.update_status_based_on_returns()
		self.validate_close_conditions()

	def on_submit(self):
		self.create_stock_transfer_on_send()

	def on_update_after_submit(self):
		self.reconcile_returns()

	def auto_populate_processes(self):
		"""Auto-populate processes based on selected garment type."""
		if not self.garment_type:
			return

		# Only auto-populate if the table is empty or garment type changed
		existing_processes = [p.process_name for p in self.get("processes") or []]
		expected_processes = GARMENT_PROCESS_MAP.get(self.garment_type, [])

		if not existing_processes:
			# Fresh auto-populate
			self.set("processes", [])
			for process_name in expected_processes:
				row = self.append("processes", {})
				row.process_name = process_name
				row.status = "Not Started"
				row.qty_sent = self.qty_sent

	def validate_processes_required(self):
		"""Validate that at least one process row exists.

		This runs AFTER auto_populate_processes() so auto-populated rows
		will have already been added. We use this instead of reqd=1 on the
		JSON field because Frappe's client-side reqd validation on Table
		fields can be unreliable.
		"""
		if not self.get("processes") or len(self.get("processes")) == 0:
			frappe.throw(
				frappe._("At least one process is required. Please select a Garment Type to auto-populate processes or add them manually."),
				title=frappe._("Processes Required"),
			)

	def update_status_based_on_returns(self):
		"""Auto-update overall JWO status based on child table entries."""
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

	def get_first_processing_contractor(self):
		"""Get the first process that is marked as 'Processing' or 'Completed'."""
		for p in self.get("processes") or []:
			if p.contractor and p.status in ("Processing", "Completed"):
				return p.contractor
		# Fallback: first process with a contractor
		for p in self.get("processes") or []:
			if p.contractor:
				return p.contractor
		return None

	def get_first_process_name(self):
		"""Get the name of the first process."""
		for p in self.get("processes") or []:
			return p.process_name
		return ""

	def get_all_contractors_display(self):
		"""Get a comma-separated list of all contractors involved."""
		contractors = []
		for p in self.get("processes") or []:
			if p.contractor and p.contractor not in contractors:
				contractors.append(p.contractor)
		return ", ".join(contractors)

	def create_stock_transfer_on_send(self):
		"""Create Stock Entry for material transfer to subcontractor.

		Uses the first process's contractor for the transfer.
		"""
		try:
			# Check if column/table exists before accessing to avoid errors
			if not frappe.db.has_column("Stock Settings", "allow_material_transfer_to_subcontractor"):
				return

			if frappe.db.get_single_value("Stock Settings", "allow_material_transfer_to_subcontractor"):
				from textile_tracking.textile.api import create_subcontract_transfer

				create_subcontract_transfer(self)
		except Exception:
			# Table or column may not exist in this ERPNext version — skip silently
			pass

	def reconcile_returns(self):
		"""Create Stock Entry for material receipt from subcontractor."""
		try:
			if self.status in ("Received", "Partially Received"):
				from textile_tracking.textile.api import create_receipt_entry

				create_receipt_entry(self)
		except Exception:
			# Stock module may not be available in this ERPNext setup — skip silently
			pass
