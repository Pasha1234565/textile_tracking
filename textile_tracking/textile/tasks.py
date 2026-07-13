from __future__ import unicode_literals

import frappe
from frappe.utils import today, add_days

from textile_tracking.textile.doctype.fabric_wastage_log.fabric_wastage_log import (
	update_contractor_wastage_stats,
)


def daily_update_contractor_wastage_stats():
	"""Daily scheduler job: recalculate wastage stats for all active contractors.

	Runs once per day and updates every active contractor's aggregated
	wastage fields from all Fabric Wastage Log records.
	"""
	contractors = frappe.db.get_all("Contractor", filters={"status": "Active"}, pluck="name")

	for name in contractors:
		update_contractor_wastage_stats(name)

	frappe.db.commit()


def daily_check_overdue_job_work_orders():
	"""Daily scheduler: send notifications for overdue Job Work Orders."""
	overdue_orders = frappe.db.get_all(
		"Job Work Order",
		filters={
			"status": ["not in", ["Received", "Closed"]],
			"expected_return_date": ["<", today()],
		},
		fields=["name", "contractor", "expected_return_date"],
	)

	for jwo in overdue_orders:
		days_overdue = (frappe.utils.date_diff(today(), jwo.expected_return_date))

		# Create notification for system manager / owner
		notification = frappe.new_doc("Notification Log")
		notification.for_user = frappe.db.get_value(
			"User", {"user_type": "System User", "enabled": 1}, "name"
		)
		notification.title = frappe._("Job Work Order Overdue")
		notification.subject = frappe._(
			"Job Work Order {0} for contractor {1} is overdue by {2} day(s)."
		).format(jwo.name, jwo.contractor, days_overdue)
		notification.document_type = "Job Work Order"
		notification.document_name = jwo.name
		notification.insert(ignore_permissions=True)

	frappe.db.commit()


def daily_notify_rate_card_expiring():
	"""Daily scheduler: alert on rate cards that are 90+ days old (indicating potentially stale rates).

	Since Contractor Rate Item only has effective_from (not effective_to),
	this flags rates that haven't been updated in 90 days for review.
	"""
	ninety_days_ago = add_days(today(), -90)

	# Find rate card items that are 90+ days old without a newer rate
	stale_rates = frappe.db.sql("""
		SELECT
			cri.name,
			cri.parent as contractor,
			cri.process,
			cri.effective_from,
			cri.rate_per_piece
		FROM `tabContractor Rate Item` cri
		INNER JOIN `tabContractor` c ON c.name = cri.parent
		WHERE cri.effective_from <= %s
			AND c.status = 'Active'
		ORDER BY cri.parent, cri.process, cri.effective_from DESC
	""", ninety_days_ago, as_dict=True)

	for rate in stale_rates:
		notification = frappe.new_doc("Notification Log")
		notification.for_user = frappe.db.get_value(
			"User", {"user_type": "System User", "enabled": 1}, "name"
		)
		notification.title = frappe._("Rate Card Review Needed")
		notification.subject = frappe._(
			"Rate for {0} (Process: {1}) on contractor {2} has been effective since {3}. "
			"Current rate: {4}. Please review and update if needed."
		).format(
			rate.process,
			rate.contractor,
			rate.effective_from,
			rate.rate_per_piece
		)
		notification.document_type = "Contractor"
		notification.document_name = rate.contractor
		notification.insert(ignore_permissions=True)

	frappe.db.commit()
