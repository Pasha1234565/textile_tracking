from __future__ import unicode_literals

import frappe
from frappe.model.document import Document


class RawMaterialBatch(Document):
	def validate(self):
		self.set_batch_id_from_series()

	def set_batch_id_from_series(self):
		"""Auto-generate batch_id from naming series if not provided."""
		if not self.batch_id:
			self.batch_id = self.name
