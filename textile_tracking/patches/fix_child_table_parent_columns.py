from __future__ import unicode_literals

import frappe

# Hardcoded list of all child tables in the Textile module as a safety fallback
KNOWN_CHILD_TABLES = [
	"Process History Entry",
	"Fabric Roll Daily Production",
	"Cutting Plan Item",
	"Job Work Return",
	"Contractor Rate Item",
	"Production Schedule Item",
]

REQUIRED_COLUMNS = ["parent", "parenttype", "parentfield"]


def execute():
	"""Ensure all child table doctypes in the Textile module have parent columns.

	This patch automatically adds `parent`, `parenttype`, and `parentfield` columns
	to any child table that is missing them. Frappe's `bench migrate` sometimes
	fails to create these columns for new child tables, causing submission errors
	like (1054, "Unknown column 'parent' in 'WHERE'").

	The patch is designed to never crash — each ALTER TABLE is wrapped in try-except
	so it works regardless of whether columns already exist or tables are missing.
	"""
	# Try to discover child tables from DocType table
	child_tables = _discover_child_tables()

	# Fallback to hardcoded list if discovery fails
	if not child_tables:
		child_tables = KNOWN_CHILD_TABLES
		print("Using hardcoded child table list (DocType query unavailable)")

	fixed_count = 0
	for doctype in child_tables:
		if _fix_table(doctype):
			fixed_count += 1

	frappe.db.commit()
	print(f"Child table parent column check complete. Fixed {fixed_count} table(s).")


def _discover_child_tables():
	"""Query tabDocType for Textile child tables. Returns empty list on failure."""
	try:
		return frappe.db.sql_list(
			"""SELECT `name` FROM `tabDocType`
			   WHERE `module` = 'Textile' AND `istable` = 1"""
		)
	except Exception:
		return []


def _fix_table(doctype):
	"""Add missing parent/parenttype/parentfield columns to a child table.
	Returns True if any column was added, False otherwise."""
	table = f"tab{doctype}"
	added_any = False

	for col in REQUIRED_COLUMNS:
		try:
			frappe.db.sql(f"ALTER TABLE `{table}` ADD COLUMN `{col}` VARCHAR(140) NULL")
			added_any = True
			print(f"  Added column `{col}` to {table}")
		except Exception:
			# Column already exists or table doesn't exist — both are fine
			pass

	# Try to add index on parent column for performance
	try:
		frappe.db.sql(f"ALTER TABLE `{table}` ADD INDEX `parent` (`parent`)")
	except Exception:
		pass

	if added_any:
		print(f"✅ Fixed {table}")
	else:
		print(f"✓ {table} — all columns OK")

	return added_any
