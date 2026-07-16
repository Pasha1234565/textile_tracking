from __future__ import unicode_literals

import frappe


def execute():
    """Create the Wastage Trend Overview Dashboard Chart if it doesn't exist.

    The workspace references this chart in its `charts` child table, and the
    chart card won't render on the workspace unless the Dashboard Chart
    document exists in the database. We create it here programmatically to
    avoid the "Cannot edit Standard charts" validation that blocks fixture
    imports.
    """
    chart_name = "Wastage Trend Overview"

    if frappe.db.exists("Dashboard Chart", chart_name):
        print(f"✅ Dashboard Chart '{chart_name}' already exists — skipping")
        return

    try:
        doc = frappe.get_doc({
            "doctype": "Dashboard Chart",
            "chart_name": chart_name,
            "chart_type": "Line",
            "source": "Report",
            "report_name": "Contractor Wastage Trend",
            "module": "Textile",
            "is_public": 1,
            "is_standard": 1,
            "filters_json": "{}",
            "timeseries": 0,
        })
        doc.insert(ignore_permissions=True)
        print(f"✅ Created Dashboard Chart '{chart_name}'")
    except Exception as e:
        print(f"⚠️ Could not create Dashboard Chart '{chart_name}': {e}")
