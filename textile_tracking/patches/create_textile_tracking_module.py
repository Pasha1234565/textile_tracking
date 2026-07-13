from __future__ import unicode_literals
import frappe


def execute():
	"""Create Module Def for Textile if it doesn't exist."""
	if not frappe.db.exists("Module Def", "Textile"):
		module_def = frappe.get_doc(
			{
				"doctype": "Module Def",
				"module_name": "Textile",
				"app_name": "textile_tracking",
			}
		)
		module_def.insert()
		frappe.db.commit()
		print("Created 'Textile' Module Def")
	else:
		print("'Textile' Module Def already exists")
