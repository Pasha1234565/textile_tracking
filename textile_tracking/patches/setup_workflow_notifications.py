from __future__ import unicode_literals

import frappe
from frappe.utils import now


def execute():
	"""Setup Workflow, Roles, and Notifications for Textile Tracking app."""
	create_roles()
	create_workflow()
	create_notifications()


def create_roles():
	"""Create custom roles."""
	for role_name in ("Job Work Manager", "Contractor Coordinator"):
		if not frappe.db.exists("Role", role_name):
			role = frappe.new_doc("Role")
			role.role_name = role_name
			role.desk_access = 1
			role.is_custom = 1
			role.insert(ignore_permissions=True)
			print(f"Created Role: {role_name}")


def create_workflow():
	"""Create Job Work Order workflow."""
	if frappe.db.exists("Workflow", "Job Work Order Workflow"):
		print("Workflow 'Job Work Order Workflow' already exists")
		return

	workflow = frappe.new_doc("Workflow")
	workflow.workflow_name = "Job Work Order Workflow"
	workflow.document_type = "Job Work Order"
	workflow.is_active = 1
	workflow.send_email_alert = 0

	# Workflow States
	states = [
		{
			"state": "Draft",
			"allow_edit": "All",
			"update_field": "status",
			"update_value": "Draft",
		},
		{
			"state": "Sent",
			"allow_edit": "All",
			"update_field": "status",
			"update_value": "Sent",
		},
		{
			"state": "Partially Received",
			"allow_edit": "Job Work Manager",
			"update_field": "status",
			"update_value": "Partially Received",
		},
		{
			"state": "Received",
			"allow_edit": "Job Work Manager",
			"update_field": "status",
			"update_value": "Received",
		},
		{
			"state": "Closed",
			"allow_edit": "Job Work Manager",
			"update_field": "status",
			"update_value": "Closed",
		},
	]

	for state_data in states:
		workflow.append("states", state_data)

	# Workflow Transitions
	transitions = [
		{
			"state": "Draft",
			"action": "Send to Contractor",
			"next_state": "Sent",
			"allowed": "Job Work Manager",
		},
		{
			"state": "Sent",
			"action": "Partial Return Received",
			"next_state": "Partially Received",
			"allowed": "Job Work Manager",
		},
		{
			"state": "Sent",
			"action": "Full Return Received",
			"next_state": "Received",
			"allowed": "Job Work Manager",
		},
		{
			"state": "Partially Received",
			"action": "Partial Return Received",
			"next_state": "Partially Received",
			"allowed": "Job Work Manager",
		},
		{
			"state": "Partially Received",
			"action": "Full Return Received",
			"next_state": "Received",
			"allowed": "Job Work Manager",
		},
		{
			"state": "Received",
			"action": "Close Order",
			"next_state": "Closed",
			"allowed": "Job Work Manager",
		},
	]

	for transition_data in transitions:
		workflow.append("transitions", transition_data)

	workflow.insert(ignore_permissions=True)
	print("Created Workflow: Job Work Order Workflow")


def create_notifications():
	"""Create Notification records."""
	notifications = [
		{
			"name": "Job Work Overdue Alert",
			"subject": "Job Work Order {{ doc.name }} is overdue",
			"document_type": "Job Work Order",
			"event": "Days After",
			"days_before": 0,
			"days_after": 1,
			"condition": 'doc.status not in ["Received", "Closed"]',
			"channel": ["System Notification", "Email"],
			"recipients": [
				{
					"receiver_by_document_field": "owner",
				}
			],
			"send_system_notification": 1,
			"send_email": 1,
			"enabled": 1,
		},
		{
			"name": "High Wastage Alert",
			"subject": "High Wastage: {{ doc.wastage_pct }}% recorded",
			"document_type": "Fabric Wastage Log",
			"event": "New",
			"condition": "doc.wastage_pct > 15",
			"channel": ["System Notification"],
			"recipients": [
				{
					"receiver_by_document_field": "owner",
				}
			],
			"send_system_notification": 1,
			"send_email": 0,
			"enabled": 1,
		},
	]

	for notif_data in notifications:
		name = notif_data.pop("name")
		if frappe.db.exists("Notification", name):
			print(f"Notification '{name}' already exists")
			continue

		notif = frappe.new_doc("Notification")
		notif.update(notif_data)
		notif.name = name
		notif.insert(ignore_permissions=True)
		print(f"Created Notification: {name}")
