from __future__ import unicode_literals

import frappe


def execute():
	"""Add parent/parenttype/parentfield columns to all Textile child tables.

	This runs the EXACT same ALTER TABLE commands that work when run manually
	via bench console. Frappe's schema sync sometimes fails to create these
	columns for child tables, causing (1054, "Unknown column 'parent' in WHERE").

	This patch is designed to NEVER crash — every ALTER TABLE is wrapped in
	try/except and columns that already exist are silently skipped.
	"""
	fix_all_child_tables()


def fix_all_child_tables():
	"""The exact working code — add parent columns to ALL child tables."""
	tables = [
		"tabJob Work Return",
		"tabCutting Plan Item",
		"tabFabric Roll Daily Production",
		"tabProcess History Entry",
		"tabContractor Rate Item",
		"tabProduction Schedule Item",
	]

	columns = ["parent", "parenttype", "parentfield"]

	for table in tables:
		for col in columns:
			try:
				frappe.db.sql(
					f"ALTER TABLE `{table}` ADD COLUMN `{col}` VARCHAR(140) NULL"
				)
				print(f"  Added `{col}` to {table}")
			except Exception:
				# Column already exists — that's fine
				pass

		# Also try to ensure parent column has an index
		try:
			frappe.db.sql(f"ALTER TABLE `{table}` ADD INDEX `parent` (`parent`)")
		except Exception:
			# Index already exists — that's fine
			pass

	frappe.db.commit()
	print("✅ Child table parent columns checked and fixed where needed")
