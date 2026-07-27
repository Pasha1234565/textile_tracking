# Textile Tracking — Developer Guide

## Overview

Textile Tracking is a Frappe/ERPNext custom app (`textile_tracking`) built for textile and garment manufacturers to manage job work operations. It provides end-to-end tracking of fabric sent to external contractors for processing, including wastage logging, cost analysis, automated stock integration, cutting optimization, production scheduling, and full raw material-to-finished-roll traceability.

**Tech Stack:** Frappe Framework v15+ (Python/MySQL), ERPNext v15+ integration, jQuery client scripts, Jinja templating for web portals

**GIT Repository:** `https://github.com/Pasha1234565/textile_tracking.git`

---

## App Metadata (`hooks.py`)

| Key | Value |
|-----|-------|
| `app_name` | `textile_tracking` |
| `app_title` | `Textile` |
| `app_description` | Textile Tracking & Job Work Management Application |
| `app_publisher` | Your Company |
| `app_icon` | `octicon octicon-file-directory` |
| `app_color` | grey |
| `app_license` | MIT |

### Hooks Architecture

```python
fixtures = [8 fixture types: Workspace, DocType, Report, Workflow, Workflow State, Workflow Action, Role, Notification]
scheduler_events = {"daily": [3 tasks]}
website_route_rules = [dpp, loom_dashboard, supplier_portal]
after_migrate = [fix_child_table_parent_columns, create_wastage_chart]
before_request = [fix_child_table_parent_columns.try_fix_once]
```

---

## Project Structure

```
textile_tracking/
├── __init__.py                     # Version + auto child table fix
├── hooks.py                        # App hooks, fixtures, scheduler, routes
├── modules.txt                     # Module registration: "Textile"
├── patches.txt                     # Migration patch sequence (5 patches)
├── commands.py                     # CLI commands + demo data (8 demo creators)
├── setup.py                        # Package setup
├── requirements.txt                # Python dependencies
├── MANIFEST.in                     # Package manifest
├── README.md                       # Project readme
├── DEVELOPER_GUIDE.md              # This file
├── USER_GUIDE.md                   # End-user guide
├── patches/
│   ├── __init__.py
│   ├── create_textile_tracking_module.py   # pre_model_sync: creates Module Def
│   ├── setup_workflow_notifications.py     # post: workflow, roles, notifications
│   ├── fix_child_table_parent_columns.py   # post: ALTER TABLE child table columns
│   ├── add_demo_data.py                    # post: delegates to commands.py
│   └── create_wastage_chart.py             # post: inserts chart into workspace
├── textile/                         # Main module package
│   ├── __init__.py
│   ├── api.py                       # Stock transfer/receipt creation
│   ├── tasks.py                     # 3 daily scheduled tasks
│   ├── doctype/                     # 18 DocType definitions
│   │   ├── job_contractor/          # Master: Job Contractor
│   │   ├── loom/                    # Master: Loom/Machine
│   │   ├── raw_material_batch/       # Master: Raw Material Batch
│   │   ├── fabric_roll/             # Transaction: Fabric Roll (submittable)
│   │   ├── pattern_template/        # Master: Pattern Template
│   │   ├── machine_output_log/      # Transaction: Machine Output Log
│   │   ├── job_work_order/          # Transaction: Job Work Order (submittable, workflow)
│   │   ├── fabric_wastage_log/      # Transaction: Fabric Wastage Log
│   │   ├── cutting_plan/            # Transaction: Cutting Plan (submittable)
│   │   ├── production_schedule/     # Transaction: Production Schedule (submittable)
│   │   └── vendor_delivery_schedule/ # Transaction: Vendor Delivery Schedule (submittable)
│   │   (Child tables: contractor_rate_item, job_work_order_process, job_work_return,
│   │    cutting_plan_item, pattern_piece, fabric_roll_daily_production, process_history_entry)
│   ├── report/                      # 5 Report definitions
│   │   ├── contractor_wastage_trend/
│   │   ├── true_cost_per_piece_by_contractor/
│   │   ├── overdue_job_work_orders/
│   │   ├── cutting_efficiency/
│   │   └── lot_genealogy/
│   └── workspace/│   └── Textile Tracking/        # Workspace with 4 shortcuts, 6 card sections, 1 chart
└── www/                             # 3 Web portals
    ├── dpp.html + dpp.py            # Digital Product Passport
    ├── loom_dashboard.html + .py    # Factory Floor Dashboard
    └── supplier_portal.html + .py   # Supplier Collaboration Portal
```

---

## DocType Architecture (18 Total)

### Complete DocType Inventory

| # | DocType | Type | Submittable | Naming | Title Field |
|---|---------|------|-------------|--------|-------------|
| 1 | Job Contractor | Master | No | `field:contractor_name` | contractor_name |
| 2 | Loom | Master | No | `field:machine_id` | machine_id |
| 3 | Raw Material Batch | Master | No | `naming_series: RMB-.YYYY.-.####` | batch_id |
| 4 | Fabric Roll | Transaction | **Yes** | `naming_series: FBR-.YYYY.-.####` | roll_number |
| 5 | Pattern Template | Master | No | `naming_series: PT-.YYYY.-.####` | template_name |
| 6 | Machine Output Log | Transaction | No | `naming_series: MOL-.YYYY.-.####` | — |
| 7 | Job Work Order | Transaction | **Yes** | `naming_series: JWO-.YYYY.-.####` | source_item |
| 8 | Fabric Wastage Log | Transaction | No | `naming_series: FWL-.YYYY.-.####` | contractor |
| 9 | Cutting Plan | Transaction | **Yes** | `naming_series: CP-.YYYY.-.####` | cutting_plan_name |
| 10 | Production Schedule | Transaction | **Yes** | `naming_series: PS-.YYYY.-.####` | — |
| 11 | Vendor Delivery Schedule | Transaction | **Yes** | `naming_series: VDS-.YYYY.-.####` | supplier_name |
| 12 | Contractor Rate Item | Child table | — | — | — |
| 13 | Job Work Order Process | Child table | — | — | — |
| 14 | Job Work Return | Child table | — | — | — |
| 15 | Cutting Plan Item | Child table | — | — | — |
| 16 | Pattern Piece | Child table | — | — | — |
| 17 | Fabric Roll Daily Production | Child table | — | — | — |
| 18 | Process History Entry | Child table | — | — | — |

### DocType Relationship Diagram

```
Raw Material Batch
├── storage_location, certification tracking
└── ──▶ Fabric Roll (via raw_material_batch field)
    ├── process_history (Table → Process History Entry)
    ├── daily_production (Table → Fabric Roll Daily Production)
    └── ──▶ Cutting Plan (via fabric_roll field)
        └── cutting_items (Table → Cutting Plan Item)
            └── ──▶ Pattern Template (via pattern_template link)

Pattern Template
└── pieces (Table → Pattern Piece)

Job Contractor
├── rate_card (Table → Contractor Rate Item)
├── contact fields
└── wastage analytics (read-only aggregates)

Job Work Order (Submittable, Workflow-enabled)
├── processes (Table → Job Work Order Process)
│   └── ──▶ Job Contractor (via contractor link)
├── job_work_returns (Table → Job Work Return)
├── ──▶ Raw Material Batch (optional link)
├── ──▶ Fabric Roll (auto-set on submit)
├── stock entries (sent/received)
└── ──▶ Fabric Wastage Log (via job_work_order link)

Loom
├── ──▶ Machine Output Log (via loom field)
└── ──▶ Production Schedule Item (via loom field)

Production Schedule
└── schedule_items (Table → Production Schedule Item)
    └── ──▶ Loom, Job Work Order

Vendor Delivery Schedule
└── ──▶ Supplier, Raw Material Batch
```

### DocType Details

#### 1. Job Contractor (`job_contractor`)
- **Table name:** `tabJob Contractor`
- **Naming:** `field:contractor_name` (unique, used as name)
- **Key fields:**
  - `supplier` — Optional link to ERPNext Supplier
  - `contractor_type` — Cutting/Stitching/Dyeing/Embroidery/Finishing
  - `status` — Active/Inactive
  - `default_wastage_allowance_pct` — Default 2.0%
  - `rate_card` — Child table of `Contractor Rate Item`
  - Aggregated analytics: `total_qty_sent`, `total_wastage_qty`, `wastage_percentage`, `last_updated`
- **Permissions:** System Manager (full), Job Work Manager (full), All (read)

#### 2. Loom (`loom`)
- **Table name:** `tabLoom`
- **Naming:** `field:machine_id` (unique)
- **Key fields:**
  - `machine_type` — Airjet/Rapier/Shuttle/Waterjet/Dobby/Jacquard/Circular Knitting/Flat Knitting/Other
  - `status` — Running/Idle/Under Maintenance/Breakdown/Offline
  - `speed_rpm`, `efficiency_pct` (read-only), `meters_produced_today` (read-only), `defects_today` (read-only)
  - `max_width_cm`, `manufacturer`, `installation_date`
  - `location`, `operator_name`
- **Permissions:** System Manager (full), Job Work Manager (full), All (read)

#### 3. Raw Material Batch (`raw_material_batch`)
- **Table name:** `tabRaw Material Batch`
- **Naming:** `naming_series: RMB-.YYYY.-.####`
- **Key fields:**
  - `batch_id` — Unique human-readable identifier (e.g., COT-2024-001)
  - `material_type` — Cotton/Polyester/Blended/Linen/Silk/Wool/Viscose/Nylon/Other
  - `supplier`, `supplier_batch_no`, `origin_country`
  - Certification: `certification_type` (GOTS/OEKO-TEX/BCI/Fair Trade/Organic/RCS/GRS/None), `organic_cert_id`, `gots_certified`
  - `received_date`, `quantity`, `uom`, `quality_grade`
  - `storage_location`, `storage_notes`

#### 4. Fabric Roll (`fabric_roll`)
- **Table name:** `tabFabric Roll`
- **Naming:** `naming_series: FBR-.YYYY.-.####`
- **Submittable:** Yes
- **Key fields:**
  - `roll_number` — Unique physical identifier
  - `status` — In Production/Completed/Quarantine/Dispatched
  - `source_item` — Link to Item
  - `production_stage` — Grey Fabric/Bleached/Dyed/Printed/Finished/Processed
  - Traceability: `raw_material_batch`, `job_work_order`, `contractor`
  - Garment details: `garment_type`, `garment_size`, `rolls_given_to_contractor`
  - Production estimates (read-only): `estimated_fabric_per_garment`, `estimated_garments_per_roll`, `total_estimated_garments`
  - Measurements: `length_meters`, `width_cm`, `weight_kg`
  - Quality: `grade` (Premium/A/B/C/Reject), `quality_status` (Passed/Quarantine/Failed), `production_date`
  - `daily_production` — Child table of `Fabric Roll Daily Production`
  - `qr_code_text` — Auto-generated Digital Product Passport URL
  - `process_history` — Child table of `Process History Entry`
  - Production summary (read-only): `actual_total_produced`, `wastage_percentage`
- **Server-side (`fabric_roll.py`):**
  - `validate()` — Generates QR, calculates production estimates, sums daily production
  - `on_submit()` — Updates JWO with fabric roll reference
  - `on_cancel()` — Clears JWO roll reference
  - Built-in fabric consumption database: ~40 entries (8 garment types × 5 sizes)

#### 5. Pattern Template (`pattern_template`)
- **Table name:** `tabPattern Template`
- **Naming:** `naming_series: PT-.YYYY.-.####`
- **Key fields:**
  - `template_name` — Unique
  - `fabric_item` — Link to Item
  - `pieces` — Child table of `Pattern Piece` (piece_name, width_cm, height_cm, qty_per_roll, fabric_direction)
  - `total_area_sq_m` — Read-only, auto-calculated

#### 6. Machine Output Log (`machine_output_log`)
- **Table name:** `tabMachine Output Log`
- **Naming:** `naming_series: MOL-.YYYY.-.####`
- **Key fields:**
  - `loom` — Link to Loom
  - `log_date`, `shift` (Morning/Evening/Night)
  - `meters_produced`, `runtime_minutes`, `defect_count`
  - `downtime_reason` — Mechanical Failure/Power Outage/Material Shortage/Operator Absence/Scheduled Maintenance/Changeover/Other

#### 7. Job Work Order (`job_work_order`)
- **Table name:** `tabJob Work Order`
- **Naming:** `naming_series: JWO-.YYYY.-.####`
- **Submittable:** Yes
- **Workflow:** Yes (5 states, 6 transitions)
- **Key fields:**
  - `garment_type` — Shirt/T-Shirt/Skirt/Saree/Blouse/Kurta/Jeans/Dress/Dupatta/Fabrics (Roll)
  - `source_item` — Link to Item
  - `qty_sent` — Float (required)
  - `status` — Read-only: Draft/Sent/Partially Received/Received/Closed
  - `processes` — Child table of `Job Work Order Process` (process_name, contractor, date_sent, expected_return_date, actual_return_date, status, qty_sent, rate_per_piece, notes)
  - Traceability: `raw_material_batch`, `fabric_roll` (read-only)
  - `job_work_returns` — Child table of `Job Work Return` (date_received, qty_received, qty_rejected, wastage_qty, wastage_reason)
  - Costing: `total_received_qty`, `total_wastage_qty` (read-only)
  - `stock_entry_sent`, `stock_entry_received` — Links to Stock Entry
- **Server-side (`job_work_order.py`):**
  - `validate()` — Auto-populates processes, validates requirements, updates status from returns, checks close conditions
  - `on_submit()` — Creates stock transfer
  - `on_update_after_submit()` — Creates receipt stock entry, reconciles returns
  - `GARMENT_PROCESS_MAP` — 10 garment types mapped to process sequences
  - `validate_close_conditions()` — Blocks closing if wastage exists without Fabric Wastage Log

#### 8. Fabric Wastage Log (`fabric_wastage_log`)
- **Table name:** `tabFabric Wastage Log`
- **Naming:** `naming_series: FWL-.YYYY.-.####`
- **Key fields:**
  - `job_work_order` — Link to JWO
  - `contractor` — Auto-fetched from JWO
  - `date_logged` — Date (default Today)
  - `qty_sent`, `wastage_qty`, `wastage_pct` (read-only, computed)
  - `wastage_category` — Cutting Loss/Contractor Damage/Transit Damage/Quality Reject
  - `remarks`, `raw_material_batch`
- **Server-side (`fabric_wastage_log.py`):**
  - `validate()` — Calculates wastage percentage
  - `on_update()` — Updates contractor wastage stats
  - `on_trash()` — Updates contractor wastage stats
  - `before_insert()` — Auto-fetches contractor and batch from linked JWO
  - `on_update_after_submit()` — Sends high wastage alert if >15%
- **Client-side (`fabric_wastage_log.js`):**
  - Real-time wastage % calculation on field changes
  - Auto-fill contractor from linked JWO

#### 9. Cutting Plan (`cutting_plan`)
- **Table name:** `tabCutting Plan`
- **Naming:** `naming_series: CP-.YYYY.-.####`
- **Submittable:** Yes
- **Key fields:**
  - `cutting_plan_name`, `fabric_roll` (Link)
  - `roll_length_meters`, `roll_width_cm` (fetch from Fabric Roll)
  - `cutting_items` — Child table of `Cutting Plan Item` (pattern_template, piece_name, width_cm, height_cm, qty_planned, qty_cut, x_position, y_position)
  - `total_fabric_used`, `estimated_waste_pct` (read-only)

#### 10. Production Schedule (`production_schedule`)
- **Table name:** `tabProduction Schedule`
- **Naming:** `naming_series: PS-.YYYY.-.####`
- **Submittable:** Yes
- **Key fields:**
  - `date`, `shift` (Morning/Evening/Night)
  - `status` — Draft/Planned/In Progress/Completed/Cancelled
  - `schedule_items` — Child table of `Production Schedule Item` (loom, job_work_order, fabric_item, target_meters, start_time, end_time, notes)

#### 11. Vendor Delivery Schedule (`vendor_delivery_schedule`)
- **Table name:** `tabVendor Delivery Schedule`
- **Naming:** `naming_series: VDS-.YYYY.-.####`
- **Submittable:** Yes
- **Key fields:**
  - `supplier` (Link to Supplier), `supplier_name` (fetch)
  - `raw_material_batch` (Link)
  - `original_delivery_date`, `revised_delivery_date`
  - `qty_expected`, `uom`, `status` (Pending/Confirmed/Shipped/Delayed/Delivered/Cancelled)
  - `supplier_notes`, `last_updated_by_supplier`

---

## Workflow Configuration

### Job Work Order Workflow

Created programmatically in `patches/setup_workflow_notifications.py`:

**States (5):**
| State | Allowed Editor |
|-------|---------------|
| Draft | All |
| Sent | All |
| Partially Received | Job Work Manager |
| Received | Job Work Manager |
| Closed | Job Work Manager |

**Transitions (6):**
| From | Action | To |
|------|--------|----|
| Draft | Send to Contractor | Sent |
| Sent | Partial Return Received | Partially Received |
| Sent | Full Return Received | Received |
| Partially Received | Partial Return Received | Partially Received |
| Partially Received | Full Return Received | Received |
| Received | Close Order | Closed |

---

## Stock Integration (ERPNext)

The app integrates with ERPNext's stock system through `textile_tracking.textile.api`:

### `api.py` Functions

**`create_subcontract_transfer(job_work_order)`**
- Triggered: `on_submit` of Job Work Order
- Creates: Stock Entry type "Material Transfer"
- Transfers: `source_item` from default warehouse to contractor
- Error handling: Logs error, does not block workflow

**`create_receipt_entry(job_work_order)`**
- Triggered: `on_update_after_submit` when status is Received/Partially Received
- Creates: Stock Entry type "Material Receipt"
- Receives: Total `qty_received` from returns into default warehouse
- Idempotent: Checks `stock_entry_received` to prevent duplicates

---

## Scheduled Tasks (`tasks.py`)

Three daily background jobs:

| Function | Interval | Description |
|----------|----------|-------------|
| `daily_update_contractor_wastage_stats()` | Daily | Aggregates FWL data per active contractor → updates analytics fields |
| `daily_check_overdue_job_work_orders()` | Daily | Finds processes past `expected_return_date` for non-closed JWOs → creates Notification Log |
| `daily_notify_rate_card_expiring()` | Daily | Flags rate cards 90+ days old → creates Notification Log for review |

---

## Reports (5)

### 1. Contractor Wastage Trend (`report_type: "Query Report"`)
- **SQL:** Groups `tabFabric Wastage Log` by contractor and month
- **Columns:** contractor, month, qty_sent, wastage_qty, wastage_pct
- **Chart:** Line chart with region fill
- **Python:** `contractor_wastage_trend.py` provides formatted columns + chart config

### 2. True Cost Per Piece by Contractor (`report_type: "Script Report"`)
- **SQL:** Joins `tabJob Work Order Process` + `tabJob Work Return`
- **Filters:** contractor, from_date, to_date
- **Columns:** contractor, process_name, total_qty_sent/received, total_wastage_qty, wastage_pct, rate_per_piece, labor_cost, wastage_cost, **true_cost_per_piece**
- **Chart:** Bar chart comparing Rate Per Piece vs True Cost Per Piece
- **Logic:** `True Cost = (Labor Cost + Wastage Cost) / Qty Received`

### 3. Overdue Job Work Orders (`report_type: "Query Report"`)
- **SQL:** Filters `tabJob Work Order` where `status NOT IN ('Received', 'Closed')` AND `expected_return_date < CURDATE()`
- **Columns:** JWO link, garment_type, source_item, qty_sent, processes (concatenated), contractors, earliest expected return, max days overdue, status

### 4. Cutting Efficiency (`report_type: "Script Report"`)
- **SQL:** From `tabCutting Plan` with roll measurements joined
- **Filters:** from_date, to_date, fabric_roll
- **Columns:** cutting_plan, fabric_roll, roll_length/width, total_area, fabric_used, est_waste_pct, creation_date, status
- **Chart:** Bar chart with Est. Waste % + Fabric Used per plan

### 5. Lot Genealogy (`report_type: "Script Report"`)
- **Filters:** raw_material_batch, fabric_roll
- **Logic:** Builds traceability tree from batch → fabric rolls, or from roll → batch (reverse)
- **Columns:** Type, ID, material_name, party, quantity, date, grade_status, certification, level
- **3 modes:** filter by batch (forward trace), filter by roll (backward trace), no filter (all batches with roll counts)

---

## Roles & Permissions

Two custom roles created by `patches/setup_workflow_notifications.py`:

| Role | Desk Access | Key Permissions |
|------|------------|-----------------|
| **System Manager** | Full | All doctypes, all operations |
| **Job Work Manager** | Full | Full CRUD + submit/amend/cancel on all transaction doctypes. Rate card visibility. |
| **Contractor Coordinator** | Limited | Create/read on JWO, FWL, Fabric Roll. No delete. No rate card visibility. |

Permission rules are defined per-DocType in each JSON file's `permissions` array.

---

## Web Portals (3)

### 1. Digital Product Passport (`/dpp/<roll_id>`)
- **Files:** `www/dpp.html` (extends `templates/web.html`), `www/dpp.py`
- **Route:** `/dpp/<roll_id>` → `www/dpp.html`
- **Context:** Fetches Fabric Roll → Raw Material Batch → JWO Processes → Process History
- **Features:** Fabric details, measurements, raw material origin with certification badges, JWO process table, manufacturing timeline, QR code (Google Charts API), EU 2027 compliance footer

### 2. Factory Floor Dashboard (`/loom-dashboard`)
- **Files:** `www/loom_dashboard.html`, `www/loom_dashboard.py`
- **Route:** `/loom-dashboard` → `www/loom_dashboard.html`
- **Context:** Fetches all looms with today's output logs, today's production schedules
- **Features:** Summary stats cards (Running/Idle/Down/Avg Efficiency/Total Meters), per-machine cards with status indicator, metrics grid, today's schedule panel, responsive grid layout

### 3. Supplier Collaboration Portal (`/supplier-portal`)
- **Files:** `www/supplier_portal.html`, `www/supplier_portal.py`
- **Route:** `/supplier-portal` → `www/supplier_portal.html`
- **Context:** Checks session → finds supplier by email → fetches delivery schedules
- **Features:** Login gate, supplier stats, delivery schedule table, inline update forms with date/status/notes, status badges (Pending/Confirmed/Shipped/Delayed/Delivered/Cancelled)

---

## Patch Sequence (`patches.txt`)

Patches run in two phases:

**pre_model_sync:**
| Patch | Purpose |
|-------|---------|
| `create_textile_tracking_module` | Creates the "Textile" Module Def in `tabModule Def` |

**post_model_sync:**
| Patch | Purpose |
|-------|---------|
| `setup_workflow_notifications` | Creates 2 roles, workflow, 2 notification templates |
| `fix_child_table_parent_columns` | Runs ALTER TABLE to add parent/parenttype/parentfield on all child tables |
| `add_demo_data` | Delegates to `commands.insert_demo_data()` for demo records |
| `create_wastage_chart` | Inserts the Wastage Trend Overview chart into the workspace |

### Child Table Fix Strategy

The `fix_child_table_parent_columns.py` patch is critical because Frappe's schema sync sometimes fails to create parent columns. The fix:
1. Runs via `after_migrate` hook (every `bench migrate`)
2. Runs via `before_request` hook (first HTTP request) — most reliable because `frappe.db` is always connected
3. Runs on `__init__.py` import (when app is first loaded)
4. Uses `_child_tables_fixed` global flag to prevent re-runs within process lifetime
5. Targets 7 child tables: `tabContractor Rate Item`, `tabJob Work Order Process`, `tabJob Work Return`, `tabCutting Plan Item`, `tabPattern Piece`, `tabFabric Roll Daily Production`, `tabProcess History Entry`

---

## Fixtures (`hooks.py`)

The following records are shipped as fixtures:

```python
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
```

---

## Demo Data System (`commands.py`)

The `commands.insert_demo_data()` function inserts demo records using **raw SQL** to bypass DocType controller resolution issues.

### What it creates:
- **5 Job Contractors** (Kashmir Stitching Works, Raj Cutting Services, Sara Dyeing House, Punjab Embroidery, Finishing Masters) with rate cards
- **5 Job Work Orders** in various statuses with multi-process children
- **3 Fabric Wastage Logs** with different categories
- **3 Raw Material Batches** with GOTS/OEKO-TEX/Fair Trade certifications
- **2 Fabric Rolls** with process history entries
- **8 Looms/Machines** (Airjet, Rapier, Shuttle, Dobby, Circular Knitting, Waterjet)
- **5 Machine Output Logs** for running looms
- **1 Pattern Template** (T-Shirt Basic with 4 pieces)
- **1 Cutting Plan** linked to a fabric roll
- **2 Vendor Delivery Schedules** (Pending + Confirmed)
- **1 Demo Supplier** (Organic Cotton Supplier)
- **1 Demo Item** (Cotton Fabric - Demo)

### Design decisions:
- Uses `frappe.db.sql()` instead of `frappe.get_doc().insert()` to avoid controller issues
- Commits after each section for transaction safety
- Rolls back on child table failures to clear MySQL aborted transaction state
- Checks for existing data before inserting (idempotent)
- Two-phase: Phase 1 (core data), Phase 2 (new feature data like looms, patterns)

### CLI Command:
```bash
bench --site your-site.local insert-demo-data
```

### Console:
```python
exec(open("../apps/textile_tracking/textile_tracking/commands.py").read())
insert_demo_data()
```

---

## Garment Process Mapping

```python
GARMENT_PROCESS_MAP = {
    "Shirt": ["Cutting", "Stitching", "Finishing"],
    "T-Shirt": ["Cutting", "Stitching", "Finishing"],
    "Skirt": ["Cutting", "Stitching", "Finishing"],
    "Saree": ["Cutting", "Stitching", "Dyeing", "Embroidery", "Finishing"],
    "Blouse": ["Cutting", "Stitching", "Finishing"],
    "Kurta": ["Cutting", "Stitching", "Finishing"],
    "Jeans": ["Cutting", "Stitching", "Dyeing", "Finishing"],
    "Dress": ["Cutting", "Stitching", "Embroidery", "Finishing"],
    "Dupatta": ["Cutting", "Dyeing", "Finishing"],
    "Fabrics (Roll)": ["Dyeing", "Finishing"],
}
```

### Fabric Consumption Database

Built into `fabric_roll.py` — ~40 entries mapping `(garment_type, size)` → meters:

| Garment | S | M | L | XL | XXL |
|---------|---|---|---|---|-----|
| Shirt | 1.2 | 1.4 | 1.6 | 1.8 | 2.0 |
| T-Shirt | 0.8 | 1.0 | 1.2 | 1.4 | 1.6 |
| Saree | 5.5 | 5.5 | 5.5 | 5.5 | 5.5 |
| Kurta | 1.5 | 1.7 | 1.9 | 2.1 | 2.3 |
| Suit Set | 2.5 | 2.8 | 3.1 | 3.4 | 3.7 |

---

## Known Limitations & Future Work

### Current Gaps
1. **Payment Reconciliation** — No link between Job Work Orders and Payment Entries
2. **Multi-level Job Work** — Subcontracting by contractors is not modeled
3. **WhatsApp Notifications** — High wastage alerts could be routed to WhatsApp
4. **Contractor Rate Card History** — No custom report for rate changes over time
5. **Cutting Layout Optimization** — Layout positions (x/y) are stored but no optimization algorithm implemented

### Technical Notes
- The `subcontract_process` field was renamed from `process` to avoid conflicting with Frappe's `Meta.process()` method
- The `Job Contractor` DocType was renamed from `Contractor` to avoid conflicts with `workforce_manager` app
- Child tables require manual ALTER TABLE if parent columns are missing — auto-fix runs via hooks
- Stock integration gracefully skips when Stock Settings or modules are unavailable

---

## Setup Instructions for Developers

```bash
# Install
cd ~/frappe-bench
bench get-app --skip-assets https://github.com/Pasha1234565/textile_tracking.git
bench --site your-site.local install-app textile_tracking
bench build
bench --site your-site.local migrate
bench --site your-site.local clear-cache

# Demo data
bench --site your-site.local insert-demo-data

# Enable developer mode
bench --site your-site.local set-config developer_mode 1

# Watch for frontend changes
bench watch
```

### Troubleshooting Installation

| Error | Solution |
|-------|----------|
| `LinkValidationError` | Re-run `install-app` |
| Controller resolution error | Re-install the app: `uninstall-app` then `install-app` |
| Missing child table columns | Run `bench migrate` twice |
| Workspace blocks broken | `bench clear-cache`, `bench clear-website-cache`, restart |
