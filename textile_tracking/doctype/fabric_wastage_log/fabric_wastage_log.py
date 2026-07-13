from __future__ import unicode_literals

import frappe
from frappe.model.document import Document


class FabricWastageLog(Document):
	def on_update(self):
		"""Update contractor wastage stats when a log is created or modified."""
		update_contractor_wastage_stats(self.contractor)


	def on_trash(self):
		"""Update contractor wastage stats when a log is deleted."""
		update_contractor_wastage_stats(self.contractor)


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

	frappe.db.set_value("Contractor", contractor_name, {
		"total_qty_sent": total_qty_sent,
		"total_wastage_qty": total_wastage_qty,
		"wastage_percentage": wastage_pct,
		"last_updated": frappe.utils.today()
	})
