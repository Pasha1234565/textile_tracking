from __future__ import unicode_literals

__version__ = "0.1.0"

# Global flag to ensure child table fix runs only once per process lifetime
_child_tables_fixed = False


def ensure_child_tables_fixed():
	"""Run the working ALTER TABLE fix once when the app is loaded.

	Frappe's schema sync sometimes fails to create `parent`, `parenttype`,
	and `parentfield` columns for child tables. This runs the exact same
	ALTER TABLE commands that work when executed manually via bench console.

	The fix is idempotent — it silently skips columns that already exist.
	"""
	global _child_tables_fixed
	if _child_tables_fixed:
		return

	import frappe

	try:
		from textile_tracking.patches.fix_child_table_parent_columns import (
			fix_all_child_tables,
		)

		fix_all_child_tables()
		_child_tables_fixed = True
		print("Child table parent columns verified")
	except Exception:
		# Frappe may not be initialized yet — will retry on after_migrate hook
		pass


# Auto-run on app import during frappe app initialization
try:
	ensure_child_tables_fixed()
except Exception:
	pass
