from __future__ import unicode_literals

import frappe
from frappe.model.document import Document


class CuttingPlan(Document):
	def validate(self):
		# Only run algorithm when cutting items change to avoid recalculating on every save
		prev = self.get_doc_before_save()
		if prev:
			old_items = [(i.piece_name, i.width_cm, i.height_cm, i.qty_planned) for i in prev.get("cutting_items", [])]
			new_items = [(i.piece_name, i.width_cm, i.height_cm, i.qty_planned) for i in self.get("cutting_items", [])]
			if old_items != new_items:
				self.run_nesting_algorithm()
		else:
			# New document
			self.run_nesting_algorithm()

	def on_submit(self):
		self.update_roll_status()

	def on_cancel(self):
		self.reset_roll_status()

	def run_nesting_algorithm(self):
		"""Simple 2D bin-packing (guillotine) algorithm for cutting optimization.

		Uses a MaxRects heuristic to place rectangular pieces on a fabric roll
		to minimize waste. The roll is treated as a 2D bin where width = roll width
		and length = roll length.
		"""
		if not self.get("cutting_items"):
			return

		roll_width = self.roll_width_cm or 150  # Default if not set
		roll_length_cm = (self.roll_length_meters or 50) * 100  # Convert to cm

		# Collect all pieces with their quantities
		pieces = []
		for item in self.get("cutting_items"):
			for _ in range(item.qty_planned or 1):
				pieces.append({
					"name": item.piece_name or "Piece",
					"w": item.width_cm or 10,
					"h": item.height_cm or 10,
					"qty": 1,
				})

		if not pieces:
			return

		# Sort pieces by area descending (largest first) for better packing
		pieces.sort(key=lambda p: p["w"] * p["h"], reverse=True)

		# Simple MaxRects algorithm
		free_rects = [{"x": 0, "y": 0, "w": roll_width, "h": roll_length_cm}]
		placed = []
		total_placed_area = 0.0

		for piece in pieces:
			best_score = float("inf")
			best_rect = None
			best_idx = -1

			for i, rect in enumerate(free_rects):
				if rect["w"] >= piece["w"] and rect["h"] >= piece["h"]:
					# Score = leftover area (heuristic: minimize waste)
					score = (rect["w"] - piece["w"]) * (rect["h"] - piece["h"])
					if score < best_score:
						best_score = score
						best_rect = i
						best_idx = i

			if best_rect is not None:
				rect = free_rects[best_rect]
				placed_x = rect["x"]
				placed_y = rect["y"]

				placed.append({
					"name": piece["name"],
					"x": placed_x,
					"y": placed_y,
					"w": piece["w"],
					"h": piece["h"],
				})

				total_placed_area += piece["w"] * piece["h"]

				# Split the free rectangle (vertical split, then horizontal)
				remainder_w = rect["w"] - piece["w"]
				remainder_h = rect["h"] - piece["h"]

				# Remove the used rectangle
				free_rects.pop(best_rect)

				# Add split rectangles
				if remainder_h > 0:
					free_rects.append({
						"x": rect["x"],
						"y": rect["y"] + piece["h"],
						"w": rect["w"],
						"h": remainder_h,
					})
				if remainder_w > 0:
					free_rects.append({
						"x": rect["x"] + piece["w"],
						"y": rect["y"],
						"w": remainder_w,
						"h": piece["h"],
					})

		# Calculate results
		roll_area = roll_width * roll_length_cm
		self.total_fabric_used = round(total_placed_area / 10000, 2)  # Convert cm² to m²

		if roll_area > 0:
			used_pct = (total_placed_area / roll_area) * 100
			self.estimated_waste_pct = round(100 - used_pct, 2)
		else:
			self.estimated_waste_pct = 0

		# Generate SVG layout preview
		self.layout_html = self.generate_layout_svg(placed, roll_width, roll_length_cm)

		# Update position data on cutting items
		for item in self.get("cutting_items"):
			for p in placed:
				if p["name"] == item.piece_name:
					item.x_position = p["x"]
					item.y_position = p["y"]
					break

	def generate_layout_svg(self, placed, width_cm, height_cm):
		"""Generate an SVG representation of the cutting layout."""
		scale = 2  # pixels per cm
		svg_w = width_cm * scale
		svg_h = height_cm * scale

		# Keep SVG manageable
		max_svg = 800
		if svg_w > max_svg:
			scale = max_svg / width_cm
			svg_w = max_svg
			svg_h = height_cm * scale

		colors = ["#2196F3", "#4CAF50", "#FF9800", "#E91E63", "#9C27B0",
				  "#00BCD4", "#FF5722", "#607D8B", "#CDDC39", "#795548"]

		pieces_svg = ""
		for i, p in enumerate(placed):
			x = p["x"] * scale
			y = p["y"] * scale
			w = p["w"] * scale
			h = p["h"] * scale
			color = colors[i % len(colors)]
			pieces_svg += (
				f'<rect x="{x}" y="{y}" width="{w}" height="{h}" '
				f'fill="{color}" opacity="0.7" stroke="#fff" stroke-width="1" rx="2"/>'
				f'<text x="{x + w/2}" y="{y + h/2}" text-anchor="middle" '
				f'dy="0.3em" font-size="10" fill="#fff" font-weight="500">'
				f'{p["name"]}</text>\n'
			)

		return (
			f'<svg width="{svg_w}" height="{svg_h}" '
			f'viewBox="0 0 {svg_w} {svg_h}" xmlns="http://www.w3.org/2000/svg">'
			f'<rect width="100%" height="100%" fill="#f8f9fa" rx="4"/>'
			f'<rect x="1" y="1" width="{svg_w-2}" height="{svg_h-2}" '
			f'fill="none" stroke="#dee2e6" stroke-width="2" rx="4"/>'
			f'{pieces_svg}'
			f'<text x="10" y="{svg_h-8}" font-size="11" fill="#6c757d">'
			f'Roll: {self.roll_width_cm or 150}cm x {self.roll_length_meters or 50}m | '
			f'Waste: {self.estimated_waste_pct or 0}%</text>'
			f'</svg>'
		)

	def update_roll_status(self):
		"""Update fabric roll status when cutting plan is submitted."""
		if self.fabric_roll:
			frappe.db.set_value("Fabric Roll", self.fabric_roll, "status", "In Production")

	def reset_roll_status(self):
		"""Reset fabric roll status when cutting plan is cancelled."""
		if self.fabric_roll:
			frappe.db.set_value("Fabric Roll", self.fabric_roll, "status", "Completed")
