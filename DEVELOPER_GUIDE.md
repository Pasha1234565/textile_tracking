# Textile Tracking — Developer Guide

## Overview

Textile Tracking is a Frappe/ERPNext custom app (`textile_tracking`) built for textile and garment manufacturers to manage job work operations. It provides end-to-end tracking of fabric sent to external contractors for processing, including wastage logging, cost analysis, and automated stock integration.

**Tech Stack:** Frappe Framework (Python/MySQL), ERPNext integration, jQuery client scripts

---

## Project Structure

```
textile_tracking/
├── hooks.py                          # App hooks, fixtures, doc_events, scheduler
├── modules.txt                       # Module registration
├── patches.txt                       # Migration patch sequence
├── patches/
│   ├── __init__.py
│   ├── create_textile_tracking_module.py
│   ├── setup_workflow_notifications.py
│   └── add_demo_data.py
├── commands.py                       # CLI commands for demo data
├── textile/                          # Main module package
│   ├── __init__.py
│   ├── api.py                        # Stock transfer hooks
│   ├── tasks.py                      # Scheduled background jobs
│   ├── doctype/
│   │   ├── job_contractor/           # DocType: Job Contractor
│   │   │   ├── __init__.py
│   │   │   ├── job_contractor.json
│   │   │   └── job_contractor.py
│   │   ├── job_work_order/           # DocType: Job Work Order
│   │   │   ├── __init__.py
│   │   │   ├── job_work_order.json
│   │   │   └── job_work_order.py
│   │   ├── job_work_return/          # Child Table: Job Work Return
│   │   │   ├── __init__.py
│   │   │   ├── job_work_return.json
│   │   │   └── job_work_return.py
│   │   ├── contractor_rate_item/     # Child Table: Contractor Rate Item
│   │   │   ├── __init__.py
│   │   │   ├── contractor_rate_item.json
│   │   │   └── contractor_rate_item.py
│   │   └── fabric_wastage_log/       # DocType: Fabric Wastage Log
│   │       ├── __init__.py
│   │       ├── fabric_wastage_log.json
│   │       ├── fabric_wastage_log.py
│   │       └── fabric_wastage_log.js
│   ├── report/
│   │   ├── contractor_wastage_trend/ # Report: Wastage % Trend
│   │   │   ├── contractor_wastage_trend.json
│   │   │   └── contractor_wastage_trend.py
│   │   ├── true_cost_per_piece_by_contractor/  # Report: True Cost Per Piece by Contractor
│   │   │   ├── __init__.py
│   │   │   ├── true_cost_per_piece_by_contractor.json
│   │   │   └── true_cost_per_piece_by_contractor.py
│   │   └── overdue_job_work_orders/  # Report: Overdue Orders
│   │       ├── __init__.py
│   │       └── overdue_job_work_orders.json
│   └── workspace/
│       └── Textile Tracking/
│           └── Textile Tracking.json # Workspace configuration
```

---

## DocType Architecture

### DocType Relationship Diagram

```
Job Contractor
├── rate_card (Table → Contractor Rate Item)
│   ├── subcontract_process (Select)
│   ├── rate_per_piece (Currency)
│   └── effective_from (Date)
├── contact fields (email, phone, address)
└── wastage analytics (read-only aggregates)

Job Work Order (Submittable, Workflow-enabled)
├── contractor (Link → Job Contractor)
├── source_item (Link → Item)
├── subcontract_process (Select)
├── job_work_returns (Table → Job Work Return)
│   ├── qty_received (Float)
│   ├── qty_rejected (Float)
│   ├── wastage_qty (Float)
│   ├── wastage_reason (Small Text)
│   └── date_received (Date)
├── dates (date_sent, expected_return_date)
├── status (Draft/Sent/Partially Received/Received/Closed)
└── stock_entry tracking (sent/received)

Fabric Wastage Log
├── job_work_order (Link → Job Work Order)
├── contractor (Link → Job Contractor)
├── wastage fields (qty, pct, category)
├── date_logged (Date)
└── remarks (Small Text)
```

### DocType Details

#### Job Contractor (`job_contractor`)
- **Naming:** `field:contractor_name` (name is unique)
- **Table name:** `tabJob Contractor`
- **Key fields:**
  - `supplier` — Optional link to ERPNext Supplier for integration
  - `contractor_type` — Cutting/Stitching/Dyeing/Embroidery/Finishing
  - `default_wastage_allowance_pct` — Used as benchmark for alerts
  - `rate_card` — Child table of `Contractor Rate Item`
  - Analytics fields — Auto-populated by daily scheduler
- **Server-side validation:** Prevents duplicate processes in rate card

#### Job Work Order (`job_work_order`)
- **Naming:** `naming_series: JWO-.YYYY.-.####`
- **Submittable:** Yes (enables workflow transitions)
- **Workflow:** Yes (status managed by workflow actions)
- **Key fields:**
  - `status` — Read-only, driven entirely by workflow transitions
  - `source_item` — Optional link to Item (for stock integration)
  - `rate_per_piece` — Manually entered (not auto-fetched from rate card)
  - `job_work_returns` — Child table for logging receipts
  - `stock_entry_sent/stock_entry_received` — Track auto-generated Stock Entries
- **Server-side methods** (in `job_work_order.py`):
  - `validate()` — Updates status from returns, checks close conditions
  - `validate_close_conditions()` — Blocks closing if wastage exists without FWL
  - `on_submit()` — Triggers stock transfer creation
  - `on_update_after_submit()` — Triggers receipt stock entry

#### Fabric Wastage Log (`fabric_wastage_log`)
- **Naming:** `naming_series: FWL-.YYYY.-.####`
- **Key fields:**
  - `job_work_order` — Optional link to JWO
  - `contractor` — Auto-fetched from JWO if linked
  - `wastage_pct` — Read-only, computed as (wastage_qty / qty_sent) × 100
  - `wastage_category` — Select: Cutting Loss / Contractor Damage / Transit Damage / Quality Reject
- **Client-side script** (`fabric_wastage_log.js`):
  - Real-time `wastage_pct` calculation when qty/wastage changes
  - Auto-fills contractor from linked JWO
- **Server-side methods:**
  - `validate()` — Calculates wastage percentage
  - `on_update()` — Updates contractor wastage stats
  - `before_insert()` — Auto-fetches contractor from JWO

---

## Workflow Configuration

The Job Work Order uses Frappe's Workflow engine (created programmatically in `patches/setup_workflow_notifications.py`):

### States
| State | Allowed Editor |
|---|---|
| Draft | All |
| Sent | All |
| Partially Received | Job Work Manager |
| Received | Job Work Manager |
| Closed | Job Work Manager |

### Transitions
| From | Action | To |
|---|---|---|
| Draft | Send to Contractor | Sent |
| Sent | Partial Return Received | Partially Received |
| Sent | Full Return Received | Received |
| Partially Received | Partial Return Received | Partially Received |
| Partially Received | Full Return Received | Received |
| Received | Close Order | Closed |

---

## Stock Integration (ERPNext)

The app integrates with ERPNext's stock system through hooks defined in `hooks.py`:

```python
doc_events = {
    "Job Work Order": {
        "on_submit": "textile_tracking.textile.api.create_subcontract_transfer",
        "on_update_after_submit": "textile_tracking.textile.api.create_receipt_entry",
    }
}
```

### `api.py` Functions

**`create_subcontract_transfer(job_work_order)`**
- Triggered: On submit of JWO (Draft → Sent)
- Creates: Stock Entry type "Material Transfer"
- Transfers: `source_item` from default warehouse
- Tracks: Saves Stock Entry name in `stock_entry_sent` field
- Error handling: Logs error, doesn't block workflow

**`create_receipt_entry(job_work_order)`**
- Triggered: On update after submit (when status is Received/Partially Received)
- Creates: Stock Entry type "Material Receipt"
- Receives: Total qty_received from returns into default warehouse
- Idempotency: Checks `stock_entry_received` to prevent duplicates
- Error handling: Logs error, doesn't block the order

---

## Scheduled Tasks (`tasks.py`)

Three daily background jobs run via Frappe scheduler:

| Function | What it does |
|---|---|
| `daily_update_contractor_wastage_stats()` | Aggregates FWL data per contractor → updates analytics fields |
| `daily_check_overdue_job_work_orders()` | Finds orders past expected return date → creates Notification Log |
| `daily_notify_rate_card_expiring()` | Flags rate cards 90+ days old → creates Notification Log |

---

## Reports

### 1. Contractor Wastage Trend (`report_type: "Query Report"`)
- **SQL:** Joins `tabFabric Wastage Log` with `tabJob Contractor`
- **Columns:** contractor, month, qty_sent, wastage_qty, wastage_pct
- **Chart:** Line chart with wastage percentage over time
- **Python:** `contractor_wastage_trend.py` provides formatted columns and chart config

### 2. True Cost Per Piece (`report_type: "Script Report"`)
- **SQL:** Joins `tabJob Work Order` + `tabJob Work Return` + `tabContractor Rate Item`
- **Columns:** contractor, process, qty_sent/received, wastage, rate, labor cost, wastage cost, true cost
- **Chart:** Bar chart comparing Rate Per Piece vs True Cost Per Piece
- **Logic:** True Cost = (Labor Cost + Wastage Cost) / Qty Received
  - Labor Cost = Rate Per Piece × Qty Received
  - Wastage Cost = Wastage Qty × Raw Material Valuation Rate

### 3. Overdue Job Work Orders (`report_type: "Query Report"`)
- **SQL:** Filters `tabJob Work Order` where `status NOT IN ('Received', 'Closed')` AND `expected_return_date < CURDATE()`
- **Columns:** JWO link, contractor, item, qty, process, dates, days overdue, status
- **Serves as:** Daily operational report for follow-ups

---

## Roles & Permissions

Two custom roles are created by `patches/setup_workflow_notifications.py`:

| Role | Desk Access | Restrictions |
|---|---|---|
| **Job Work Manager** | Full | No restrictions on job work doctypes |
| **Contractor Coordinator** | Limited | No delete permission on any doctype. No access to Contractor rate cards (rate visibility restricted to managers). |

Permissions are set directly in each DocType's JSON file under the `permissions` array.

---

## Fixtures (`hooks.py`)

The following records are exported as fixtures and shipped with the app:

```python
fixtures = [
    {"dt": "Workspace", "filters": [["module", "=", "Textile"]]},
    {"dt": "DocType", ...},
    {"dt": "Report", ...},
    {"dt": "Workflow", ...},
    {"dt": "Workflow State", ...},
    {"dt": "Workflow Action", ...},
    {"dt": "Role", ...},
    {"dt": "Notification", ...},
]
```

When deploying to a new site, these fixtures are installed automatically during `install-app`.

---

## Patch Sequence (`patches.txt`)

Patches run in two phases:

**pre_model_sync** (before DocType sync):
- `create_textile_tracking_module` — Creates the "Textile" Module Def if missing

**post_model_sync** (after DocType sync):
- `setup_workflow_notifications` — Creates roles, workflow, notifications programmatically
- `add_demo_data` — Delegates to `commands.insert_demo_data()` for demo records

---

## Demo Data System (`commands.py`)

The `commands.insert_demo_data()` function inserts demo records using **raw SQL** to bypass Frappe's DocType controller (which can fail in environments with conflicting app modules).

**What it creates:**
- 5 Job Contractors with rate cards
- 5 Job Work Orders in various statuses
- 3 Fabric Wastage Logs linked to orders

**Run via bench console:**
```python
import textile_tracking.commands
textile_tracking.commands.insert_demo_data()
```

**Design decisions:**
- Uses `frappe.db.sql()` instead of `frappe.get_doc().insert()` to avoid controller resolution issues
- Commits after each section for transaction safety
- Rolls back on child table failures to clear MySQL aborted transaction state
- Checks for existing data before inserting (idempotent)

---

## Known Limitations & Future Work

### Current gaps (from the spec):
1. **Payment Reconciliation** — No link between Job Work Orders and Payment Entries yet
2. **Multi-level Job Work** — Subcontracting by contractors is not modeled
3. **WhatsApp Notifications** — High wastage alerts could be routed to WhatsApp via API
4. **Contractor Rate Card History** — Standard list view is sufficient, no custom report needed

### Technical notes:
- The `subcontract_process` field was renamed from `process` to avoid conflicting with Frappe's `Meta.process()` method
- The `Job Contractor` DocType was renamed from `Contractor` to avoid conflicts with the `workforce_manager` app which defines its own `Contractor` DocType
- Child table `Contractor Rate Item` may require manual `ALTER TABLE` if the `parent` column was not created during migration (due to earlier failed migrations)

---

## Setup Instructions for Developers

### Install the app

```bash
# From your frappe-bench directory
bench get-app https://github.com/Pasha1234565/textile_tracking.git
bench --site yoursite.localhost install-app textile_tracking
bench --site yoursite.localhost migrate
```

### Add demo data

```bash
bench --site yoursite.localhost console
```
```python
import textile_tracking.commands
textile_tracking.commands.insert_demo_data()
```

### If you encounter a controller resolution error

If `frappe.get_doc({"doctype": "Job Contractor", ...})` fails with a module import error, it means the database has stale DocType records. Fix by:

1. Uninstalling and reinstalling the app:
```bash
bench --site yoursite.localhost uninstall-app textile_tracking
bench --site yoursite.localhost install-app textile_tracking
```

2. Or manually fixing the DocType's module field in the database.

### If child table is missing columns

If `INSERT INTO tabContractor Rate Item` fails with "Unknown column 'parent'", add the missing columns:
```python
frappe.db.sql("ALTER TABLE `tabContractor Rate Item` ADD COLUMN `parent` varchar(255) DEFAULT NULL")
frappe.db.sql("ALTER TABLE `tabContractor Rate Item` ADD COLUMN `parenttype` varchar(255) DEFAULT NULL")
frappe.db.sql("ALTER TABLE `tabContractor Rate Item` ADD COLUMN `parentfield` varchar(255) DEFAULT NULL")
```
