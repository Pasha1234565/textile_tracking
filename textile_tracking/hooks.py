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
# Note: on_submit and on_update_after_submit are handled directly
# in the JobWorkOrder DocType class (job_work_order.py).
# Hooks are NOT needed here and would cause double-triggering.
doc_events = {}

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
website_route_rules = [
	{"from_route": "/dpp/<roll_id>", "to_route": "dpp"},
	{"from_route": "/loom-dashboard", "to_route": "loom_dashboard"},
	{"from_route": "/supplier-portal", "to_route": "supplier_portal"},
]

# Jinja
# ------------------------------
# jinja = {}

# Run after every bench migrate to ensure child table columns exist
# ------------------------------
after_migrate = [
	"textile_tracking.patches.fix_child_table_parent_columns.execute",
	"textile_tracking.patches.create_wastage_chart.execute",
]

# Run on first HTTP request to fix child table parent columns
# ------------------------------
# before_request is the most reliable hook because frappe.db is always connected
# during HTTP requests. The cache flag prevents re-running on every request.
before_request = ["textile_tracking.patches.fix_child_table_parent_columns.try_fix_once"]

# Boot
# ------------------------------
# boot_session = boot_session
