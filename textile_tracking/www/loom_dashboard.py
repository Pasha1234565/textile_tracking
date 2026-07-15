from __future__ import unicode_literals

import frappe
from frappe import _
from frappe.utils import today


def get_context(context):
	"""Build the loom dashboard data."""
	looms = frappe.db.get_all(
		"Loom",
		fields=[
			"name", "machine_id", "machine_type", "status",
			"speed_rpm", "location", "operator_name",
			"efficiency_pct", "meters_produced_today", "defects_today",
		],
		order_by="location ASC, machine_id ASC",
	)

	# Get today's schedule
	schedule = frappe.db.get_all(
		"Production Schedule",
		filters={"date": today(), "status": ["in", ["Planned", "In Progress"]]},
		fields=["name", "shift", "status"],
	)

	# Get today's output logs summary
	logs = frappe.db.sql("""
		SELECT loom, SUM(meters_produced) as total_meters,
			   SUM(defect_count) as total_defects,
			   SUM(runtime_minutes) as total_runtime
		FROM `tabMachine Output Log`
		WHERE log_date = %s
		GROUP BY loom
	""", today(), as_dict=True)

	log_map = {l.loom: l for l in logs}

	# Map output data to looms
	for loom in looms:
		log_data = log_map.get(loom.name, {})
		loom.log_meters = log_data.get("total_meters", 0) or 0
		loom.log_defects = log_data.get("total_defects", 0) or 0
		loom.log_runtime = log_data.get("total_runtime", 0) or 0

	context.looms = looms
	context.schedule = schedule
	context.title = _("Loom Dashboard")
	context.today_date = today()
	context.no_cache = 1
