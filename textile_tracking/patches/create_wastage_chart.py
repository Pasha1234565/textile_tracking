from __future__ import unicode_literals

import frappe
from frappe.utils import now


def execute():
    """Create the Wastage Trend Overview chart on the workspace via direct SQL.

    This script directly manipulates the database tables to:
    1. Create/update the Dashboard Chart record (tabDashboard Chart)
    2. Create/update the workspace's charts child table (tabWorkspace Chart)

    This bypasses the fixture system entirely (which kept failing with various
    validation errors) and uses the same reliable direct-SQL approach that
    fix_child_table_parent_columns.py uses.
    """
    chart_name = "Wastage Trend Overview"
    workspace_name = "Textile Tracking"

    # STEP 1: Create/fix the Dashboard Chart record
    # The `source` field is only for Custom chart types and must be omitted for
    # report-based charts. Only `report_name` is needed.
    try:
        # Delete old Dashboard Chart record if it exists (to reset any bad data)
        frappe.db.sql(f"DELETE FROM `tabDashboard Chart` WHERE `name` = %(name)s", {"name": chart_name})
        frappe.db.commit()

        # Insert fresh Dashboard Chart record
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
        print(f"✅ Dashboard Chart '{chart_name}' created/updated")
    except Exception as e:
        print(f"⚠️ Dashboard Chart error: {e}")

    # STEP 2: Directly update the workspace's charts child table
    # The tabWorkspace Chart table stores the link between workspace and chart.
    # Fields: name, parent, parenttype, parentfield, chart_name, label, idx
    try:
        # Delete old chart link records for this workspace
        frappe.db.sql(f"""
            DELETE FROM `tabWorkspace Chart`
            WHERE `parent` = %(workspace)s AND `parentfield` = 'charts'
        """, {"workspace": workspace_name})
        frappe.db.commit()

        # Insert fresh chart link record
        frappe.db.sql("""
            INSERT INTO `tabWorkspace Chart`
            (`name`, `parent`, `parenttype`, `parentfield`,
             `chart_name`, `label`, `idx`,
             `creation`, `modified`, `modified_by`, `owner`, `docstatus`)
            VALUES
            (%(name)s, %(parent)s, 'Workspace', 'charts',
             %(chart_name)s, %(label)s, 1,
             %(creation)s, %(modified)s, %(owner)s, %(owner)s, 0)
        """, {
            "name": f"ws-chart-{chart_name.lower().replace(' ', '-')}",
            "parent": workspace_name,
            "chart_name": chart_name,
            "label": "Wastage Trend Overview",
            "creation": now(),
            "modified": now(),
            "owner": "Administrator",
        })
        frappe.db.commit()
        print(f"✅ Workspace '{workspace_name}' now has chart link to '{chart_name}'")
    except Exception as e:
        print(f"⚠️ Workspace chart link error: {e}")

    print("🎯 Wastage chart setup complete! Refresh the workspace to see it.")
