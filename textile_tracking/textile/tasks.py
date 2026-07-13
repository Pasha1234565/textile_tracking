from __future__ import unicode_literals

import frappe

from textile_tracking.textile.doctype.fabric_wastage_log.fabric_wastage_log import (
	update_contractor_wastage_stats,
)


def daily_update_contractor_wastage_stats():
	"""Daily scheduler job: recalculate wastage stats for all active contractors.

	This runs once per day and updates every active contractor's aggregated
	wastage fields (total_qty_sent, total_wastage_qty, wastage_percentage)
	from all Fabric Wastage Log records.
	"""
	contractors = frappe.db.get_all("Contractor", filters={"status": "Active"}, pluck="name")

	for name in contractors:
		update_contractor_wastage_stats(name)

	frappe.db.commit()
