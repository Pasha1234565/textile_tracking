from __future__ import unicode_literals
import frappe


def execute():
	"""Create Module Def for Textile Tracking if it doesn't exist."""
	if not frappe.db.exists("Module Def", "Textile Tracking"):
		module_def = frappe.get_doc(
			{
				"doctype": "Module Def",
				"module_name": "Textile Tracking",
				"app_name": "textile_tracking",
			}
		)
		module_def.insert()
		frappe.db.commit()
		print("Created 'Textile Tracking' Module Def")
	else:
		print("'Textile Tracking' Module Def already exists")
