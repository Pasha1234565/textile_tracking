from __future__ import unicode_literals

import frappe
from frappe.model.document import Document


class FabricWastageLog(Document):
	def validate(self):
		self.calculate_wastage_pct()

	def on_update(self):
		update_contractor_wastage_stats(self.contractor)

	def on_trash(self):
		update_contractor_wastage_stats(self.contractor)

	def calculate_wastage_pct(self):
		"""Compute wastage percentage."""
		if self.qty_sent and self.qty_sent > 0:
			self.wastage_pct = round((self.wastage_qty / self.qty_sent) * 100, 2)
		else:
			self.wastage_pct = 0.0

	def before_insert(self):
		"""Auto-fetch contractor and raw material batch from Job Work Order if linked."""
		if self.job_work_order:
			jwo = frappe.db.get_value(
				"Job Work Order",
				self.job_work_order,
				["contractor", "raw_material_batch"],
				as_dict=True,
			)
			if jwo:
				if not self.contractor:
					self.contractor = jwo.contractor
				if not self.raw_material_batch:
					self.raw_material_batch = jwo.raw_material_batch

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
