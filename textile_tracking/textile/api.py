from __future__ import unicode_literals

import frappe
from frappe.utils import nowdate


def create_subcontract_transfer(job_work_order):
	"""Create Stock Entry: Material Transfer to Subcontractor.

	Triggered on submit of Job Work Order.
	Transfers raw material (source_item) from company warehouse to contractor.
	"""
	try:
		stock_entry = frappe.new_doc("Stock Entry")
		stock_entry.stock_entry_type = "Material Transfer"
		stock_entry.posting_date = nowdate()
		stock_entry.remarks = frappe._(
			"Job Work Transfer: {0} to {1} for process {2}"
		).format(job_work_order.name, job_work_order.contractor, job_work_order.subcontract_process)

		# Default source warehouse — uses the company's default warehouse
		source_warehouse = frappe.db.get_single_value(
			"Stock Settings", "default_warehouse"
		) or frappe.db.get_value(
			"Warehouse", {"is_group": 0, "disabled": 0}, "name"
		)

		stock_entry.append("items", {
			"item_code": job_work_order.source_item,
			"qty": job_work_order.qty_sent,
			"s_warehouse": source_warehouse,
			"t_warehouse": None,  # Will be the contractor's warehouse
			"allow_alternative_item": 0,
		})

		stock_entry.flags.ignore_permissions = True
		stock_entry.submit()
		frappe.db.set_value(
			"Job Work Order",
			job_work_order.name,
			"stock_entry_sent",
			stock_entry.name,
		)
		return stock_entry
	except Exception as e:
		frappe.log_error(
			frappe.get_traceback(),
			frappe._("Job Work Order Stock Transfer Failed: {0}").format(job_work_order.name),
		)
		return None


def create_receipt_entry(job_work_order):
	"""Create Stock Entry: Material Receipt from Subcontractor.

	Triggered when returns are logged on a submitted Job Work Order.
	Receives processed goods into company warehouse.
	Skips if a receipt Stock Entry already exists for this order.
	"""
	if not job_work_order.get("job_work_returns"):
		return

	# Prevent duplicate Stock Entries
	if hasattr(job_work_order, "stock_entry_received") and job_work_order.stock_entry_received:
		return

	try:
		total_received = sum(
			r.qty_received for r in job_work_order.job_work_returns if r.qty_received
		)
		if total_received <= 0:
			return

		target_warehouse = frappe.db.get_single_value(
			"Stock Settings", "default_warehouse"
		) or frappe.db.get_value(
			"Warehouse", {"is_group": 0, "disabled": 0}, "name"
		)

		stock_entry = frappe.new_doc("Stock Entry")
		stock_entry.stock_entry_type = "Material Receipt"
		stock_entry.posting_date = nowdate()
		stock_entry.remarks = frappe._(
			"Job Work Receipt: {0} from {1}, qty received: {2}"
		).format(
			job_work_order.name, job_work_order.contractor, total_received
		)

		stock_entry.append("items", {
			"item_code": job_work_order.source_item,
			"qty": total_received,
			"t_warehouse": target_warehouse,
			"s_warehouse": None,
			"allow_alternative_item": 0,
		})

		stock_entry.flags.ignore_permissions = True
		stock_entry.submit()

		# Track that we've created the receipt
		frappe.db.set_value(
			"Job Work Order",
			job_work_order.name,
			"stock_entry_received",
			stock_entry.name,
		)
		return stock_entry
	except Exception as e:
		frappe.log_error(
			frappe.get_traceback(),
			frappe._("Job Work Order Receipt Stock Entry Failed: {0}").format(
				job_work_order.name
			),
		)
		return None
