from __future__ import unicode_literals

app_name = "textile_tracking"
app_title = "Textile Tracking"
app_publisher = "Your Company"
app_description = "Textile Tracking Application"
app_icon = "octicon octicon-file-directory"
app_color = "grey"
app_email = "info@example.com"
app_license = "MIT"

# Apps
# ------------------------------

# Fixtures
# ------------------------------
fixtures = [
	{"dt": "Workspace", "filters": [["module", "=", "Textile Tracking"]]},
	{"dt": "DocType", "filters": [["module", "=", "Textile Tracking"]]},
	{"dt": "Report", "filters": [["module", "=", "Textile Tracking"]]}
]

# DocType Class
# ------------------------------
# Override standard doctype classes
# doctype_class = {}

# Document Events
# ------------------------------
# doc_events = {}

# Scheduled Tasks
# ------------------------------
scheduler_events = {
	"daily": [
		"textile_tracking.tasks.daily_update_contractor_wastage_stats"
	]
}

# Permissions
# ------------------------------
# permission_query_conditions = {}

# Website
# ------------------------------
# Website specific stuff

# Jinja
# ------------------------------
# Add methods to the Jinja environment
# jinja = {}

# Boot
# ------------------------------
# boot_session = boot_session

# JSON Template
# ------------------------------
# json_template = {}
