from __future__ import unicode_literals

import frappe
from frappe.model.document import Document


class ProductionSchedule(Document):
	def on_submit(self):
		self.update_loom_statuses()

	def on_cancel(self):
		self.clear_loom_statuses()

	def update_loom_statuses(self):
		"""Set loom statuses when schedule is confirmed."""
		for item in self.get("schedule_items", []):
			if item.loom:
				frappe.db.set_value("Loom", item.loom, "status", "Running")

	def clear_loom_statuses(self):
		"""Reset loom statuses when schedule is cancelled."""
		for item in self.get("schedule_items", []):
			if item.loom:
				frappe.db.set_value("Loom", item.loom, "status", "Idle")
