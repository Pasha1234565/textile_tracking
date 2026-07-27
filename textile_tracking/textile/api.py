from __future__ import unicode_literals

import frappe
from frappe.utils import nowdate


@frappe.whitelist()
def get_process_data(docname):
	"""Fetch Job Work Order child table data for reliable client-side display."""
	processes = frappe.get_all(
		"Job Work Order Process",
		filters={"parent": docname, "parenttype": "Job Work Order"},
		fields=["*"],
		order_by="idx asc",
	)
	returns = frappe.get_all(
		"Job Work Return",
		filters={"parent": docname, "parenttype": "Job Work Order"},
		fields=["*"],
		order_by="idx asc",
	)
	return {"processes": processes, "job_work_returns": returns}


@frappe.whitelist()
def diagnose_jwo(docname):
	"""Diagnose why child table data isn't loading for a JWO.

	Call from browser: /api/method/textile_tracking.textile.api.diagnose_jwo?docname=JWO-2026-0034
	"""
	result = {}

	# Check if document exists
	doc = frappe.db.get_value("Job Work Order", docname, ["name", "docstatus", "creation"])
	if not doc:
		return {"error": f"Document {docname} not found"}
	result["doc_info"] = {"name": doc[0], "docstatus": doc[1], "creation": str(doc[2])}

	# Check table structure
	try:
		cols = frappe.db.sql("DESCRIBE `tabJob Work Order Process`")
		result["process_table_columns"] = [c[0] for c in cols]
	except Exception as e:
		result["process_table_error"] = str(e)

	try:
		cols = frappe.db.sql("DESCRIBE `tabJob Work Return`")
		result["return_table_columns"] = [c[0] for c in cols]
	except Exception as e:
		result["return_table_error"] = str(e)

	# Check ALL rows in process table (no filter)
	try:
		all_processes = frappe.db.sql("""
			SELECT name, parent, parenttype, parentfield, process_name, idx
			FROM `tabJob Work Order Process`
			LIMIT 20
		""", as_dict=True)
		result["all_processes_count"] = len(all_processes)
		result["sample_processes"] = all_processes[:5]
	except Exception as e:
		result["all_processes_error"] = str(e)

	# Check specific parent match
	try:
		matched = frappe.db.sql("""
			SELECT COUNT(*) as cnt FROM `tabJob Work Order Process`
			WHERE parent = %s AND parenttype = 'Job Work Order'
		""", docname)
		result["parent_matched_count"] = matched[0][0] if matched else 0
	except Exception as e:
		result["parent_match_error"] = str(e)

	# Check rows where parent is NULL
	try:
		null_parent = frappe.db.sql("""
			SELECT COUNT(*) as cnt FROM `tabJob Work Order Process`
			WHERE parent IS NULL OR parent = ''
		""")
		result["null_parent_count"] = null_parent[0][0] if null_parent else 0
	except Exception as e:
		result["null_parent_error"] = str(e)

	# Try without parenttype filter
	try:
		loose_match = frappe.db.sql("""
			SELECT COUNT(*) as cnt FROM `tabJob Work Order Process`
			WHERE parent = %s
		""", docname)
		result["loose_parent_match"] = loose_match[0][0] if loose_match else 0
	except Exception as e:
		result["loose_match_error"] = str(e)

	return result


def _get_first_process_contractor(job_work_order):
	"""Helper: get the first process's contractor."""
	processes = job_work_order.get("processes") or []
	for p in processes:
		if p.contractor:
			return p.contractor
	return None


def _get_first_process_name(job_work_order):
	"""Helper: get the first process name."""
	processes = job_work_order.get("processes") or []
	for p in processes:
		return p.process_name
	return ""


def create_subcontract_transfer(job_work_order):
	"""Create Stock Entry: Material Transfer to Subcontractor.

	Triggered on submit of Job Work Order.
	Transfers raw material (source_item) from company warehouse to the
	first process's contractor.
	"""
	contractor = _get_first_process_contractor(job_work_order)
	process_name = _get_first_process_name(job_work_order)

	if not contractor:
		return None

	try:
		stock_entry = frappe.new_doc("Stock Entry")
		stock_entry.stock_entry_type = "Material Transfer"
		stock_entry.posting_date = nowdate()
		stock_entry.remarks = frappe._(
			"Job Work Transfer: {0} to {1} for process {2}"
		).format(job_work_order.name, contractor, process_name)

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

	contractor = _get_first_process_contractor(job_work_order)

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
			job_work_order.name, contractor or "Contractor", total_received
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
