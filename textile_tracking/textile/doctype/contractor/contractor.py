from __future__ import unicode_literals

import frappe
from frappe.model.document import Document


class Contractor(Document):
	def validate(self):
		self.validate_rate_card()

	def validate_rate_card(self):
		"""Ensure no duplicate processes in rate card."""
		if self.get("rate_card"):
			processes = []
			for row in self.rate_card:
				if row.process in processes:
					frappe.throw(
						frappe._("Process {0} is already defined in the rate card. Please remove the duplicate.").format(
							frappe.bold(row.process)
						)
					)
				processes.append(row.process)
