from __future__ import unicode_literals

import frappe


def execute():
	"""Insert demo data by delegating to commands.py."""
	from textile_tracking.commands import insert_demo_data

	insert_demo_data()
	print("Demo data patch completed")
