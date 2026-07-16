from __future__ import unicode_literals

import frappe
from frappe.model.document import Document

# --- Standard fabric consumption estimates (in meters) for a ~150cm wide fabric ---
# Keyed by (garment_type, size). Saree is fixed-length regardless of size.
FABRIC_REQUIREMENT = {
	("Shirt", "S"): 1.2,
	("Shirt", "M"): 1.4,
	("Shirt", "L"): 1.6,
	("Shirt", "XL"): 1.8,
	("Shirt", "XXL"): 2.0,
	("T-Shirt", "S"): 0.8,
	("T-Shirt", "M"): 1.0,
	("T-Shirt", "L"): 1.2,
	("T-Shirt", "XL"): 1.4,
	("T-Shirt", "XXL"): 1.6,
	("Blouse", "S"): 0.7,
	("Blouse", "M"): 0.8,
	("Blouse", "L"): 0.9,
	("Blouse", "XL"): 1.0,
	("Blouse", "XXL"): 1.1,
	("Kurta", "S"): 1.5,
	("Kurta", "M"): 1.7,
	("Kurta", "L"): 1.9,
	("Kurta", "XL"): 2.1,
	("Kurta", "XXL"): 2.3,
	("Saree", "S"): 5.5,
	("Saree", "M"): 5.5,
	("Saree", "L"): 5.5,
	("Saree", "XL"): 5.5,
	("Saree", "XXL"): 5.5,
	("Suit Set", "S"): 2.5,
	("Suit Set", "M"): 2.8,
	("Suit Set", "L"): 3.1,
	("Suit Set", "XL"): 3.4,
	("Suit Set", "XXL"): 3.7,
	("Trouser / Pant", "S"): 1.0,
	("Trouser / Pant", "M"): 1.1,
	("Trouser / Pant", "L"): 1.2,
	("Trouser / Pant", "XL"): 1.3,
	("Trouser / Pant", "XXL"): 1.5,
	("Skirt", "S"): 0.8,
	("Skirt", "M"): 0.9,
	("Skirt", "L"): 1.0,
	("Skirt", "XL"): 1.1,
	("Skirt", "XXL"): 1.2,
}


class FabricRoll(Document):
	def validate(self):
		self.set_roll_number_from_series()
		self.generate_qr_data()
		self.calculate_production_estimates()
		self.calculate_actual_production_summary()

	def on_submit(self):
		self.update_job_work_order_with_roll()

	def on_cancel(self):
		self.clear_job_work_order_roll_reference()

	def set_roll_number_from_series(self):
		"""Auto-generate roll_number from naming series if not provided."""
		if not self.roll_number:
			self.roll_number = self.name

	def generate_qr_data(self):
		"""Generate Digital Product Passport data string for QR code."""
		# Build a URL-friendly passport string
		site_url = frappe.utils.get_url()
		self.qr_code_text = f"{site_url}/dpp/{self.name}"

	def get_fabric_requirement(self):
		"""Return the standard fabric requirement in meters for the selected garment type and size."""
		if not self.garment_type or not self.garment_size:
			return 0
		return FABRIC_REQUIREMENT.get((self.garment_type, self.garment_size), 0)

	def calculate_production_estimates(self):
		"""Calculate estimated garments per roll and total estimated garments."""
		fabric_per_garment = self.get_fabric_requirement()
		self.estimated_fabric_per_garment = fabric_per_garment

		if fabric_per_garment > 0 and self.length_meters:
			self.estimated_garments_per_roll = frappe.utils.flt(
				self.length_meters / fabric_per_garment, 0
			)
		else:
			self.estimated_garments_per_roll = 0

		rolls = self.rolls_given_to_contractor or 1
		self.total_estimated_garments = frappe.utils.flt(
			self.estimated_garments_per_roll * rolls, 0
		)

	def calculate_actual_production_summary(self):
		"""Sum daily production entries and compute wastage percentage."""
		total = 0
		if self.daily_production:
			for entry in self.daily_production:
				total += frappe.utils.cint(entry.garments_produced)
		self.actual_total_produced = total

		# Wastage % = ((estimated - actual) / estimated) × 100
		if self.total_estimated_garments > 0:
			self.wastage_percentage = frappe.utils.flt(
				((self.total_estimated_garments - total) / self.total_estimated_garments) * 100,
				1,
			)
		else:
			self.wastage_percentage = 0

	def update_job_work_order_with_roll(self):
		"""Link this Fabric Roll back to the Job Work Order for traceability."""
		if self.job_work_order:
			frappe.db.set_value(
				"Job Work Order",
				self.job_work_order,
				"fabric_roll",
				self.name,
			)

	def clear_job_work_order_roll_reference(self):
		"""Clear the fabric_roll reference on the JWO when this roll is cancelled."""
		if self.job_work_order:
			frappe.db.set_value(
				"Job Work Order",
				self.job_work_order,
				"fabric_roll",
				None,
			)
