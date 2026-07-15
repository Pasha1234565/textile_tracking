from __future__ import unicode_literals

from frappe.model.document import Document


class PatternTemplate(Document):
	def validate(self):
		self.calculate_total_area()

	def calculate_total_area(self):
		"""Calculate total area from all pattern pieces."""
		total = 0.0
		for piece in self.get("pieces", []):
			area_cm = (piece.width_cm or 0) * (piece.height_cm or 0)
			area_sq_m = area_cm / 10000  # Convert cm² to m²
			total += area_sq_m * (piece.qty_per_roll or 1)
		self.total_area_sq_m = round(total, 4)
