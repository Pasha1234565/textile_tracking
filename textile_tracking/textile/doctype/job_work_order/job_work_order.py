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
		"""Ensure child table data is always loaded on document fetch.

		This runs EVERY time the document is loaded from the database.
		We directly reload child table data and set it on the document
		to ensure it's included in the serialized response sent to the client.
		"""
		if self.get("__islocal"):
			return

		try:
			# Reload processes from database
			processes = frappe.db.get_all(
				"Job Work Order Process",
				filters={"parent": self.name, "parenttype": "Job Work Order"},
				fields=["*"],
				order_by="idx asc",
			)

			# Reload returns from database
			returns = frappe.db.get_all(
				"Job Work Return",
				filters={"parent": self.name, "parenttype": "Job Work Order"},
				fields=["*"],
				order_by="idx asc",
			)

			if processes:
				self.set("processes", processes)
			if returns:
				self.set("job_work_returns", returns)

		except Exception:
			frappe.log_error(
				frappe.get_traceback(),
				frappe._("Failed to reload child data on JWO load: {0}").format(self.name),
			)

	def validate(self):
		self.auto_populate_processes()
		self.validate_processes_required()
		self.assign_process_numbers()
		self.update_status_based_on_returns()

		# ── CRITICAL FIX: Explicitly set parent/parenttype/parentfield on all child rows ──
		# This ensures child table rows are saved with correct parent references.
		# Frappe's ORM sometimes fails to set these columns for unknown reasons
		# (schema caching issues, timing with before_request hooks, etc.)
		self._ensure_child_parent_columns()

	def on_update(self):
		"""After every save/update, ensure child table parent columns are set.

		on_update() runs AFTER Frappe's ORM has saved child rows to the database.
		For new documents, validate() runs BEFORE the document gets its name,
		so _ensure_child_parent_columns() can't work. on_update() is the correct
		place because:
		1. The document name is always set (already saved)
		2. Child rows exist in the database (the ORM just inserted them)
		3. We can use raw SQL to fix any rows saved with NULL parent

		This is the definitive fix for the NULL parent column issue.
		"""
		if self.get("__islocal") or not self.name:
			return
		self._fix_child_table_parent_columns_in_db()

	def on_submit(self):
		self.create_stock_transfer_on_send()
		self.assign_process_numbers()
		self.create_initial_fabric_wastage_log()

	def on_update_after_submit(self):
		self.auto_create_fabric_wastage_logs_from_returns()
		self.reconcile_returns()

	def _ensure_child_parent_columns(self):
		"""Explicitly set parent, parenttype, and parentfield on child Document objects.

		This runs in validate() as a best-practice, but for NEW documents
		validate() runs before the name is assigned, so this is a no-op.
		The definitive fix is in _fix_child_table_parent_columns_in_db()
		which runs in on_update() with raw SQL after the ORM has saved.
		"""
		if not self.name:
			return

		for table_field in self.meta.get_table_fields():
			rows = self.get(table_field.fieldname) or []
			for row in rows:
				row.parent = self.name
				row.parenttype = self.doctype
				row.parentfield = table_field.fieldname

	def _fix_child_table_parent_columns_in_db(self):
		"""Use raw SQL to fix child rows with NULL/missing parent columns.

		This runs in on_update(), AFTER Frappe's ORM has saved child rows
		to the database. Since both validate() and the ORM's internal save
		mechanism may set parent columns when self.name is still None
		(for new documents), child rows end up with NULL parent.

		This method directly updates those rows in the database using
		the unique 'name' column of each child row, so there is no
		ambiguity about which rows belong to which document.
		"""
		if not self.name:
			return

		for table_field in self.meta.get_table_fields():
			rows = self.get(table_field.fieldname) or []
			names = [row.name for row in rows if row.name]
			if not names:
				continue

			child_table = frappe.unscrub(table_field.options)
			# Use dynamic placeholders for the IN clause — Frappe's MySQL driver
			# doesn't reliably convert a Python list for %(names)s syntax.
			placeholders = ",".join(["%s"] * len(names))
			params = [self.name, self.doctype, table_field.fieldname] + names
			try:
				frappe.db.sql(
					f"""UPDATE `tab{child_table}`
						SET parent = %s,
							parenttype = %s,
							parentfield = %s
						WHERE name IN ({placeholders})""",
					params,
				)
			except Exception:
				frappe.log_error(
					frappe.get_traceback(),
					frappe._("Failed to fix parent columns for {0}").format(child_table),
				)

	def create_initial_fabric_wastage_log(self):
		"""Create an initial placeholder Fabric Wastage Log on JWO submission."""
		if frappe.db.exists("Fabric Wastage Log", {"job_work_order": self.name}):
			return

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

		existing_processes = [p.process_name for p in self.get("processes") or []]
		expected_processes = GARMENT_PROCESS_MAP.get(self.garment_type, [])

		if not existing_processes:
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
		"""Validate that at least one process row exists."""
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
		"""Auto-create Fabric Wastage Log entries for any returns with wastage."""
		if not self.get("job_work_returns"):
			return

		for return_row in self.get("job_work_returns"):
			if not return_row.wastage_qty or return_row.wastage_qty <= 0:
				continue

			existing = frappe.db.exists("Fabric Wastage Log", {
				"job_work_order": self.name,
				"wastage_qty": return_row.wastage_qty,
				"date_logged": return_row.date_received or today(),
			})
			if existing:
				continue

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
		"""Create Stock Entry for material transfer to subcontractor."""
		try:
			if not frappe.db.has_column("Stock Settings", "allow_material_transfer_to_subcontractor"):
				return

			if frappe.db.get_single_value("Stock Settings", "allow_material_transfer_to_subcontractor"):
				from textile_tracking.textile.api import create_subcontract_transfer
				create_subcontract_transfer(self)
		except Exception:
			pass

	def reconcile_returns(self):
		"""Create Stock Entry for material receipt from subcontractor."""
		try:
			if self.status in ("Received", "Partially Received"):
				from textile_tracking.textile.api import create_receipt_entry
				create_receipt_entry(self)
		except Exception:
			pass
