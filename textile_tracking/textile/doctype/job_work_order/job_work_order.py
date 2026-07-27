from __future__ import unicode_literals

import frappe
from frappe.model.document import Document
from frappe.utils import today


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
	def onload(self):
		"""Load child table data into __onload for reliable client-side access.

		Frappe's built-in doc loading sometimes fails to include child table data
		for workflow-enabled documents. This hook ensures process and return data
		is always available on the client via frm.__onload.
		"""
		if not self.get("__islocal") and self.name:
			processes = frappe.db.get_all(
				"Job Work Order Process",
				filters={"parent": self.name, "parenttype": "Job Work Order"},
				fields=["name", "idx", "process_no", "process_name", "contractor",
						"date_sent", "expected_return_date", "actual_return_date",
						"status", "qty_sent", "rate_per_piece", "notes"],
				order_by="idx asc",
			)
			returns = frappe.db.get_all(
				"Job Work Return",
				filters={"parent": self.name, "parenttype": "Job Work Order"},
				fields=["name", "idx", "date_received", "qty_received",
						"qty_rejected", "wastage_qty", "wastage_reason"],
				order_by="idx asc",
			)
			self.set_onload("processes", processes)
			self.set_onload("job_work_returns", returns)

	def validate(self):
		self.auto_populate_processes()
		self.validate_processes_required()
		self.assign_process_numbers()
		self.update_status_based_on_returns()

	def on_submit(self):
		self.create_stock_transfer_on_send()
		self.assign_process_numbers()
		self.create_initial_fabric_wastage_log()

	def on_update_after_submit(self):
		self.auto_create_fabric_wastage_logs_from_returns()
		self.reconcile_returns()

	def create_initial_fabric_wastage_log(self):
		"""Create an initial placeholder Fabric Wastage Log on JWO submission.

		This ensures every submitted JWO has at least one FWL entry.
		When returns with wastage are later recorded, additional FWLs
		are created by auto_create_fabric_wastage_logs_from_returns().
		"""
		# Skip if FWL already exists for this JWO
		if frappe.db.exists("Fabric Wastage Log", {"job_work_order": self.name}):
			return

		# Get first process's contractor
		contractor = None
		for p in self.get("processes") or []:
			if p.contractor:
				contractor = p.contractor
				break

		if not contractor:
			return

		try:
			fwl = frappe.new_doc("Fabric Wastage Log")
			fwl.job_work_order = self.name
			fwl.contractor = contractor
			fwl.date_logged = today()
			fwl.qty_sent = self.qty_sent
			fwl.wastage_qty = 0
			fwl.wastage_category = "Cutting Loss"
			fwl.remarks = "Auto-created on Job Work Order submission"
			fwl.raw_material_batch = self.raw_material_batch
			fwl.flags.ignore_permissions = True
			fwl.insert()
		except Exception:
			frappe.log_error(
				frappe.get_traceback(),
				frappe._("Initial Fabric Wastage Log creation failed for JWO: {0}").format(self.name),
			)

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
			for idx, process_name in enumerate(expected_processes, 1):
				row = self.append("processes", {})
				row.process_no = idx
				row.process_name = process_name
				row.status = "Not Started"
				row.qty_sent = self.qty_sent

	def assign_process_numbers(self):
		"""Assign sequential process numbers to all process rows."""
		for idx, p in enumerate(self.get("processes") or [], 1):
			p.process_no = idx

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

	def auto_create_fabric_wastage_logs_from_returns(self):
		"""Auto-create Fabric Wastage Log entries for any returns with wastage.

		This runs on every update after submit so that FWLs are always
		in sync with the returns data. Users no longer need to manually
		create Fabric Wastage Log entries.
		"""
		if not self.get("job_work_returns"):
			return

		for return_row in self.get("job_work_returns"):
			if not return_row.wastage_qty or return_row.wastage_qty <= 0:
				continue

			# Check if FWL already exists for this return row (match by qty+date to avoid duplicates)
			existing = frappe.db.exists("Fabric Wastage Log", {
				"job_work_order": self.name,
				"wastage_qty": return_row.wastage_qty,
				"date_logged": return_row.date_received or today(),
			})
			if existing:
				continue

			# Get first process's contractor for the FWL
			contractor = None
			for p in self.get("processes") or []:
				if p.contractor:
					contractor = p.contractor
					break

			try:
				fwl = frappe.new_doc("Fabric Wastage Log")
				fwl.job_work_order = self.name
				fwl.contractor = contractor
				fwl.date_logged = return_row.date_received or today()
				fwl.qty_sent = self.qty_sent
				fwl.wastage_qty = return_row.wastage_qty
				fwl.wastage_category = "Contractor Damage"
				fwl.remarks = return_row.wastage_reason or "Auto-generated from Job Work Order return"
				fwl.raw_material_batch = self.raw_material_batch
				fwl.flags.ignore_permissions = True
				fwl.insert()
			except Exception:
				frappe.log_error(
					frappe.get_traceback(),
					frappe._("Auto-create Fabric Wastage Log failed for JWO: {0}").format(self.name),
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



