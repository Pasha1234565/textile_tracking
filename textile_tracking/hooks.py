from __future__ import unicode_literals

app_name = "textile_tracking"
app_title = "Textile"
app_publisher = "Your Company"
app_description = "Textile Tracking & Job Work Management Application"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "info@example.com"
app_license = "MIT"

# Fixtures
# ------------------------------
fixtures = [
	{"dt": "Workspace", "filters": [["module", "=", "Textile"]]},
	{"dt": "DocType", "filters": [["module", "=", "Textile"]]},
	{"dt": "Report", "filters": [["module", "=", "Textile"]]},
	{"dt": "Workflow", "filters": [["document_type", "=", "Job Work Order"]]},
	{"dt": "Workflow State", "filters": [["name", "in", ["Draft", "Sent", "Partially Received", "Received", "Closed"]]]},
	{"dt": "Workflow Action", "filters": [["workflow_name", "=", "Job Work Order Workflow"]]},
	{"dt": "Role", "filters": [["name", "in", ["Job Work Manager", "Contractor Coordinator"]]]},
	{"dt": "Notification", "filters": [["document_type", "in", ["Job Work Order", "Fabric Wastage Log"]]]},
]

# DocType Class
# ------------------------------
doctype_class = {}

# Document Events
# ------------------------------
doc_events = {
	"Job Work Order": {
		"on_submit": "textile_tracking.textile.api.create_subcontract_transfer",
		"on_update_after_submit": "textile_tracking.textile.api.create_receipt_entry",
	}
}

# Scheduled Tasks
# ------------------------------
scheduler_events = {
	"daily": [
		"textile_tracking.textile.tasks.daily_update_contractor_wastage_stats",
		"textile_tracking.textile.tasks.daily_check_overdue_job_work_orders",
		"textile_tracking.textile.tasks.daily_notify_rate_card_expiring",
	]
}

# Permissions
# ------------------------------
# permission_query_conditions = {}

# Website
# ------------------------------

# Jinja
# ------------------------------
# jinja = {}

# Boot
# ------------------------------
# boot_session = boot_session
