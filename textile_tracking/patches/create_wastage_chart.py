from __future__ import unicode_literals

import frappe
from frappe.utils import now


def execute():
    """Create the Wastage Trend Overview Dashboard Chart via direct SQL.

    The workspace references this chart in its `charts` child table, and the
    chart card won't render on the workspace unless the Dashboard Chart
    document exists in the database.

    The `source` field is a Link to `Dashboard Chart Source` and is ONLY used
    when chart_type='Custom'. For report-based charts, only `report_name`
    is needed and `source` should be empty.
    """
    chart_name = "Wastage Trend Overview"

    # Delete old record if it exists with wrong data (e.g. source='Report')
    if frappe.db.exists("Dashboard Chart", chart_name):
        old = frappe.get_doc("Dashboard Chart", chart_name)
        print(f"🗑️ Deleting old Dashboard Chart '{chart_name}' (had source='{old.source}')")
        frappe.delete_doc("Dashboard Chart", chart_name, ignore_permissions=True)
        frappe.db.commit()

    try:
        # `source` field is intentionally omitted — it's only for Custom chart types.
        # For report-based charts, only `report_name` is needed.
        frappe.db.sql("""
            INSERT INTO `tabDashboard Chart`
            (`name`, `chart_name`, `chart_type`,
             `report_name`, `module`, `is_public`, `is_standard`,
             `filters_json`, `timeseries`,
             `creation`, `modified`, `modified_by`, `owner`, `docstatus`)
            VALUES
            (%(name)s, %(chart_name)s, %(chart_type)s,
             %(report_name)s, %(module)s, %(is_public)s, %(is_standard)s,
             %(filters_json)s, %(timeseries)s,
             %(creation)s, %(modified)s, %(owner)s, %(owner)s, 0)
        """, {
            "name": chart_name,
            "chart_name": chart_name,
            "chart_type": "Line",
            "report_name": "Contractor Wastage Trend",
            "module": "Textile",
            "is_public": 1,
            "is_standard": 0,
            "filters_json": "{}",
            "timeseries": 0,
            "creation": now(),
            "modified": now(),
            "owner": "Administrator",
        })
        frappe.db.commit()
        print(f"✅ Created Dashboard Chart '{chart_name}'")
    except Exception as e:
        print(f"⚠️ Could not create Dashboard Chart '{chart_name}': {e}")
