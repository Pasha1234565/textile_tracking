from __future__ import unicode_literals

import frappe
from frappe.model.document import Document
from frappe.utils import today


class Loom(Document):
	def validate(self):
		self.update_daily_metrics()

	def update_daily_metrics(self):
		"""Calculate daily performance from output logs."""
		logs = frappe.db.get_all(
			"Machine Output Log",
			filters={"loom": self.name, "log_date": today()},
			fields=["meters_produced", "defect_count", "runtime_minutes"],
		)
		total_meters = sum(l.meters_produced or 0 for l in logs)
		total_defects = sum(l.defect_count or 0 for l in logs)
		total_runtime = sum(l.runtime_minutes or 0 for l in logs)

		self.meters_produced_today = total_meters
		self.defects_today = total_defects

		# Efficiency: assume 24h = 1440 min potential runtime
		if total_runtime > 0:
			self.efficiency_pct = round((total_runtime / 1440) * 100, 1)
		else:
			self.efficiency_pct = 0.0
