from __future__ import unicode_literals

import frappe
from frappe.model.document import Document
from frappe.utils import flt


class FabricWastageLog(Document):
	def validate(self):
		"""Auto-calculate wastage from linked JWO when available."""
		self._auto_calculate_wastage_from_jwo()
		self.calculate_wastage_pct()

	def on_update(self):
		update_contractor_wastage_stats(self.contractor)

	def on_trash(self):
		update_contractor_wastage_stats(self.contractor)

	def _auto_calculate_wastage_from_jwo(self):
		"""Calculate wastage_qty = qty_sent - total_qty_received from linked JWO.

		Only calculates when returns actually exist to avoid overriding the
		initial placeholder (wastage_qty=0) on submission before any returns
		are recorded.
		"""
		if not self.job_work_order:
			return

		# Fetch all returns for this JWO
		returns = frappe.get_all(
			"Job Work Return",
			filters={"parent": self.job_work_order, "parenttype": "Job Work Order"},
			fields=["qty_received"],
		)

		# Don't calculate if no returns exist yet (keep initial wastage_qty=0)
		if not returns:
			return

		total_received = sum(flt(r.qty_received) for r in returns)
		calculated_wastage = max(flt(self.qty_sent) - total_received, 0)

		self.wastage_qty = calculated_wastage
		self.remarks = frappe._(
			"Auto-calculated: {0} sent - {1} received = {2} wasted"
		).format(self.qty_sent, total_received, calculated_wastage)

	def calculate_wastage_pct(self):
		"""Compute wastage percentage: (wastage_qty / qty_sent) × 100."""
		if self.qty_sent and self.qty_sent > 0:
			self.wastage_pct = round((self.wastage_qty / self.qty_sent) * 100, 2)
		else:
			self.wastage_pct = 0.0

	def before_insert(self):
		"""Auto-fetch contractor from first JWO process and raw material batch from JWO if linked."""
		if self.job_work_order:
			# Get raw_material_batch from JWO
			jwo_batch = frappe.db.get_value(
				"Job Work Order",
				self.job_work_order,
				"raw_material_batch",
			)
			if jwo_batch and not self.raw_material_batch:
				self.raw_material_batch = jwo_batch

			# Get first process's contractor from JWO processes
			if not self.contractor:
				first_contractor = frappe.db.get_value(
					"Job Work Order Process",
					{"parent": self.job_work_order, "parenttype": "Job Work Order"},
					"contractor",
					order_by="idx asc",
				)
				if first_contractor:
					self.contractor = first_contractor

	def on_update_after_submit(self):
		"""Trigger high wastage alert if applicable."""
		if self.wastage_pct and self.wastage_pct > 15:
			self.send_high_wastage_alert()

	def send_high_wastage_alert(self):
		"""Create a system notification for high wastage."""
		notification = frappe.new_doc("Notification Log")
		notification.for_user = frappe.session.user
		notification.title = frappe._("High Wastage Alert")
		notification.subject = frappe._(
			"High wastage of {0}% recorded on Fabric Wastage Log {1}"
		).format(self.wastage_pct, self.name)
		notification.document_type = "Fabric Wastage Log"
		notification.document_name = self.name
		notification.insert(ignore_permissions=True)


def update_contractor_wastage_stats(contractor_name):
	"""Aggregate wastage data for a single contractor from Fabric Wastage Log."""
	stats = frappe.db.sql("""
		SELECT
			COALESCE(SUM(qty_sent), 0) as total_qty_sent,
			COALESCE(SUM(wastage_qty), 0) as total_wastage_qty
		FROM `tabFabric Wastage Log`
		WHERE contractor = %s
	""", contractor_name, as_dict=True)[0]

	total_qty_sent = stats.total_qty_sent
	total_wastage_qty = stats.total_wastage_qty
	wastage_pct = 0
	if total_qty_sent > 0:
		wastage_pct = round((total_wastage_qty / total_qty_sent) * 100, 2)

	frappe.db.set_value("Job Contractor", contractor_name, {
		"total_qty_sent": total_qty_sent,
		"total_wastage_qty": total_wastage_qty,
		"wastage_percentage": wastage_pct,
		"last_updated": frappe.utils.today()
	})
