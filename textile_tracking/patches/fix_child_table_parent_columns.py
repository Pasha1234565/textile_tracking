from __future__ import unicode_literals

import frappe


def execute():
	"""Ensure all child table doctypes in the Textile module have parent columns.

	When new child tables are added via doctype JSON, `bench migrate` sometimes
	fails to create the `parent`, `parenttype`, and `parentfield` columns in the
	database. This patch detects and fixes that so submissions don't fail with
	(1054, "Unknown column 'parent' in 'WHERE'").
	"""
	# Use raw SQL to query child tables — `frappe.get_all` with `is_table` filter
	# may not work because the database column is `istable` (Frappe naming convention).
	child_tables = frappe.db.sql_list(
		"""SELECT `name` FROM `tabDocType`
		   WHERE `module` = 'Textile' AND `istable` = 1"""
	)

	if not child_tables:
		print("No child tables found in Textile module")
		return

	for doctype in child_tables:
		table_name = f"tab{doctype}"
		try:
			missing = []
			for col in ("parent", "parenttype", "parentfield"):
				if not frappe.db.has_column(doctype, col):
					missing.append(col)

			if missing:
				alter_parts = []
				for col in missing:
					if col == "parent":
						alter_parts.append(
							f"ADD COLUMN `parent` VARCHAR(140) NULL"
						)
					elif col == "parenttype":
						alter_parts.append(
							f"ADD COLUMN `parenttype` VARCHAR(140) NULL"
						)
					elif col == "parentfield":
						alter_parts.append(
							f"ADD COLUMN `parentfield` VARCHAR(140) NULL"
						)

				# Add index on parent for performance
				if "parent" in missing:
					alter_parts.append("ADD INDEX `parent` (`parent`)")

				sql = f"ALTER TABLE `{table_name}` {', '.join(alter_parts)}"
				frappe.db.sql(sql)
				print(
					f"Added missing columns to {table_name}: {', '.join(missing)}"
				)
			else:
				print(f"{table_name} — all parent columns exist")
		except Exception as e:
			print(f"Could not fix {table_name}: {e}")

	frappe.db.commit()
	print("Child table parent column check complete")
