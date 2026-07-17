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
	contractors = frappe.db.get_all("Job Contractor", filters={"status": "Active"}, pluck="name")

	for name in contractors:
		update_contractor_wastage_stats(name)

	frappe.db.commit()


def daily_check_overdue_job_work_orders():
	"""Daily scheduler: send notifications for overdue Job Work Orders.

	Checks per-process expected_return_dates to find overdue processes.
	"""
	overdue_processes = frappe.db.sql("""
		SELECT
			jwp.parent as job_work_order,
			jwp.process_name,
			jwp.contractor,
			jwp.expected_return_date,
			jwo.status as jwo_status
		FROM `tabJob Work Order Process` jwp
		INNER JOIN `tabJob Work Order` jwo ON jwo.name = jwp.parent
		WHERE jwo.status NOT IN ('Received', 'Closed')
			AND jwp.status != 'Completed'
			AND jwp.expected_return_date IS NOT NULL
			AND jwp.expected_return_date < %s
		ORDER BY jwp.expected_return_date ASC
	""", today(), as_dict=True)

	for proc in overdue_processes:
		days_overdue = frappe.utils.date_diff(today(), proc.expected_return_date)

		notification = frappe.new_doc("Notification Log")
		notification.for_user = frappe.db.get_value(
			"User", {"user_type": "System User", "enabled": 1}, "name"
		)
		notification.title = frappe._("Process Overdue")
		notification.subject = frappe._(
			"Job Work Order {0} - Process '{1}' for contractor {2} is overdue by {3} day(s)."
		).format(proc.job_work_order, proc.process_name, proc.contractor or "N/A", days_overdue)
		notification.document_type = "Job Work Order"
		notification.document_name = proc.job_work_order
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
		notification.document_type = "Job Contractor"
		notification.document_name = rate.contractor
		notification.insert(ignore_permissions=True)

	frappe.db.commit()
