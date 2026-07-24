# README

## Textile Tracking — Job Work & Fabric Traceability System

**App Name:** Textile Tracking (`textile_tracking`)
**Module:** Textile
**Domain:** Textile / Garment Manufacturing (Job Work)
**Required Apps:** Frappe v15, ERPNext v15 (Stock module, for Stock Entry integration)
**Repository:** https://github.com/Pasha1234565/textile_tracking.git

---

## TABLE OF CONTENTS

1. [Application Overview](#1-application-overview)
2. [System Architecture](#2-system-architecture)
3. [Getting Started](#3-getting-started)
4. [The Day-to-Day Workflow, Step by Step](#4-the-day-to-day-workflow-step-by-step)
5. [Traceability & Cutting Features](#5-traceability--cutting-features)
6. [Vendor Portal & Digital Product Passport](#6-vendor-portal--digital-product-passport)
7. [Reports](#7-reports)
8. [Workspace Navigation](#8-workspace-navigation)
9. [Scheduled Tasks & Automation](#9-scheduled-tasks--automation)
10. [Setup & Configuration (Fixtures)](#10-setup--configuration-fixtures)
11. [Demo Data](#11-demo-data)
12. [Troubleshooting](#12-troubleshooting)
13. [Appendix](#13-appendix)

---

## 1. APPLICATION OVERVIEW

### 1.1 Purpose
Textile Tracking is a Frappe/ERPNext application built for textile and garment manufacturers who send fabric or garments out to external contractors for job work (cutting, stitching, dyeing, embroidery, finishing) and need to track the full lifecycle of that material — from raw batch, through job work, to a finished, traceable roll. It covers:

- **Job Work Management** — sending fabric to contractors, tracking returns, wastage, and rejections per process
- **Raw Material & Fabric Roll Traceability** — batch-level tracking from supplier through to a rollable, QR-linked "Digital Product Passport"
- **Cutting & Pattern Management** — cutting plans, pattern templates, and cutting efficiency
- **Vendor/Supplier Coordination** — a self-service portal for suppliers to confirm or revise delivery schedules
- **Contractor Performance Analytics** — wastage trends, true cost per piece, and overdue-order tracking

### 1.2 Key Features
- **19 DocTypes** — 12 document/master DocTypes, 7 child tables
- **5 Submittable DocTypes** — Job Work Order, Fabric Roll, Cutting Plan, Production Schedule, Vendor Delivery Schedule
- **1 Workflow** — Job Work Order (Draft → Sent → Partially Received / Received → Closed)
- **2 Custom Roles** — Job Work Manager, Contractor Coordinator
- **3 Scheduled Daily Tasks** — contractor wastage stats, overdue order checks, stale rate card alerts
- **3 Public/Portal Web Pages** — Digital Product Passport (`/dpp`), Loom Dashboard (`/loom-dashboard`), Supplier Portal (`/supplier-portal`)
- **5 Reports** — wastage trend, cutting efficiency, lot genealogy, overdue orders, true cost per piece
- **Automatic Stock Integration** — submitting a Job Work Order creates a Material Transfer Stock Entry (when Stock is enabled); logging a full return creates a Material Receipt

---

## 2. SYSTEM ARCHITECTURE

### 2.1 Technology Stack
- **Framework:** Frappe v15 / ERPNext v15
- **Database:** MariaDB
- **Automated Tasks:** Frappe Scheduler (daily)
- **Optional Dependency:** ERPNext Stock module (for automatic Stock Entry creation on submit/return)

### 2.2 DocType Structure

| # | DocType Name | Type | Card Section | Submittable |
|---|---------------|------|---------------|:-----------:|
| 1 | Job Contractor | Document | Master Data | ❌ |
| 2 | Contractor Rate Item | Child Table | — | ❌ |
| 3 | Job Work Order | Document | Production | ✅ |
| 4 | Job Work Order Process | Child Table | — | ❌ |
| 5 | Job Work Return | Child Table | — | ❌ |
| 6 | Fabric Wastage Log | Document | Cutting & Waste | ❌ |
| 7 | Raw Material Batch | Document | Traceability | ❌ |
| 8 | Fabric Roll | Document | Traceability | ✅ |
| 9 | Fabric Roll Daily Production | Child Table | — | ❌ |
| 10 | Process History Entry | Child Table | — | ❌ |
| 11 | Loom | Document | Master Data | ❌ |
| 12 | Machine Output Log | Document | — | ❌ |
| 13 | Cutting Plan | Document | Cutting & Waste | ✅ |
| 14 | Cutting Plan Item | Child Table | — | ❌ |
| 15 | Pattern Template | Document | Cutting & Waste | ❌ |
| 16 | Pattern Piece | Child Table | — | ❌ |
| 17 | Production Schedule | Document | Production | ✅ |
| 18 | Production Schedule Item | Child Table | — | ❌ |
| 19 | Vendor Delivery Schedule | Document | Vendor Portal | ✅ |

### 2.3 Naming Series Convention

| DocType | Prefix | Format |
|---|---|---|
| Job Contractor | — | By fieldname (`contractor_name`) |
| Job Work Order | JWO | `JWO-.YYYY.-.####` |
| Fabric Wastage Log | FWL | `FWL-.YYYY.-.####` |
| Raw Material Batch | RMB | `RMB-.YYYY.-.####` |
| Fabric Roll | FBR | `FBR-.YYYY.-.####` |
| Loom | — | By fieldname (`machine_id`) |
| Machine Output Log | MOL | `MOL-.YYYY.-.####` |
| Cutting Plan | CP | `CP-.YYYY.-.####` |
| Pattern Template | PT | `PT-.YYYY.-.####` |
| Production Schedule | PS | `PS-.YYYY.-.####` |
| Vendor Delivery Schedule | VDS | `VDS-.YYYY.-.####` |

### 2.4 Data Flow Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                        WORKFLOW OVERVIEW                              │
├──────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  🧵 JOB WORK CYCLE                                                    │
│  ┌────────────┐   ┌──────────────┐   ┌───────────────┐  ┌──────────┐ │
│  │Job Contractor│─▶│ Job Work     │─▶│  Job Work      │─▶│ Fabric   │ │
│  │ (Rate Card)  │  │ Order (JWO)  │  │  Returns       │  │ Wastage  │ │
│  └────────────┘   └──────┬───────┘   └───────────────┘  │  Log     │ │
│                          │ on submit                     └──────────┘ │
│                          ▼                                            │
│                  ┌──────────────┐   on full return   ┌──────────────┐│
│                  │ Stock Entry  │◀────────────────────│ Stock Entry  ││
│                  │ (Transfer)   │                      │ (Receipt)   ││
│                  └──────────────┘                      └──────────────┘│
│                                                                        │
│  📦 TRACEABILITY                                                      │
│  ┌───────────────┐   ┌──────────┐   ┌───────────────┐                │
│  │ Raw Material  │──▶│  Fabric  │──▶│  Digital       │                │
│  │  Batch        │   │  Roll    │   │  Product       │                │
│  │               │   │          │   │  Passport (/dpp)│               │
│  └───────────────┘   └──────────┘   └───────────────┘                │
│                                                                        │
│  ✂️ CUTTING & PATTERNS                                                │
│  Pattern Template ──▶ Cutting Plan ──▶ Cutting Efficiency (Report)    │
│                                                                        │
│  🚚 VENDOR COORDINATION                                               │
│  Raw Material Batch ──▶ Vendor Delivery Schedule ──▶ Supplier Portal  │
│                                                                        │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 3. GETTING STARTED

### 3.1 Installation
```bash
# From the bench directory
bench get-app https://github.com/Pasha1234565/textile_tracking.git
bench --site your-site.com install-app textile_tracking
bench --site your-site.com migrate
```

### 3.2 Role Setup
Two roles are created automatically on the first migrate after install (via the `setup_workflow_notifications` patch):
1. **Job Work Manager** — Full operational access: create/write orders, submit/cancel/amend, manage contractors and rate cards
2. **Contractor Coordinator** — Create/read/write access on Job Work Orders and Fabric Roll records; no submit/amend rights

### 3.3 Stock Integration (Optional)
If the ERPNext Stock module is enabled and a default warehouse is configured (**Stock Settings → Default Warehouse**, or at least one non-group, non-disabled Warehouse exists), the app will automatically:
- Create a **Material Transfer** Stock Entry when a Job Work Order is submitted
- Create a **Material Receipt** Stock Entry once returns fully account for the quantity sent

If Stock isn't set up, Job Work Orders still function normally — the Stock Entry step is skipped silently and logged as an error if it fails.

### 3.4 Initial Configuration
Before using the app day-to-day, set up your masters:
1. **Job Contractors** — every contractor you subcontract work to, with their rate card
2. **Looms** — if you're tracking in-house loom output via Machine Output Log
3. **Pattern Templates** — if you plan to use Cutting Plans

---

## 4. THE DAY-TO-DAY WORKFLOW, STEP BY STEP

This is the sequence you'll follow for essentially every piece of work you send out. It's worth reading through once in full before you start using the app live.

### Step 1 — Create a Job Contractor

Before any work can be sent out, the contractor receiving it needs to exist in the system.

1. Go to **Textile Tracking → Master Data → Job Contractor**.
2. Click **+ Add Job Contractor**.
3. Fill in the **Contractor Name** (required, and must be unique), the **Contractor Type** (the process they perform — Cutting, Stitching, Dyeing, Embroidery, or Finishing), and their **Status** (Active or Inactive).
4. Set the **Default Wastage Allowance (%)** — for example, 2%.
5. Add their **Email**, **Phone**, and **Address**.
6. In the **Rate Card** section, add one row per process they perform: the **Subcontract Process** (e.g. Stitching), the **Rate Per Piece** (e.g. ₹15.00), and the date the rate becomes **Effective From**.
7. Click **Save**.

> **Wastage Analytics** on this form (Total Qty Sent, Total Wastage Qty, Wastage %) are read-only — they're kept up to date automatically by the daily `daily_update_contractor_wastage_stats` job, not entered by hand.

### Step 2 — Create a Job Work Order

Now you're ready to actually send fabric out for processing.

1. Click the **New Job Work Order** shortcut on the dashboard.
2. Choose the **Garment Type** and, optionally, the **Source Item** — the fabric or garment being sent.
3. Enter the **Qty Sent** (pieces or meters).
4. In the **Processes** table, add a row and choose the **Contractor**, the **Subcontract Process** (e.g. Cutting), and the agreed **Rate Per Piece**.
5. **Date Sent** on that row defaults to today; set the **Expected Return Date** to when you expect the work back.
6. If this order is part of a traceable batch, link the **Raw Material Batch** and/or **Fabric Roll** in the Traceability section.
7. The order starts life with **Status = Draft**. Click **Save**.

### Step 3 — Log Returns

When the contractor sends processed items back — in full or in part:

1. Open the Job Work Order.
2. Go to the **Job Work Returns** table.
3. Click **+ Add Row**.
4. Enter the **Date Received**, the **Qty Received** (good pieces), **Qty Rejected** (received but not up to standard), **Wastage Qty** (pieces lost or damaged), and a short **Wastage Reason**.
5. Click **Save**.

**Behind the scenes:** if your site has stock features enabled, submitting the order automatically creates a Stock Entry (Material Transfer) so your inventory records stay in sync with what's physically left the building.

### Step 4 — Submit the Order

When you physically hand the fabric over to the contractor, make this official in the system:

1. Open the Job Work Order.
2. Click **Submit**.
3. The status automatically changes to **Sent** (driven by the Job Work Order Workflow — see [§4.1](#41-order-status-workflow) below).


**Behind the scenes:** once the total quantity received across all returns covers what was sent, the app creates a Stock Entry (Material Receipt) so the processed goods are received back into your company warehouse, and the order's status advances to **Received**.

### Step 5 — Log Wastage (whenever it applies)

If any wastage occurred, it needs its own Fabric Wastage Log entry — separate from the return itself:

1. Go to **Fabric Wastage Log → + Add**.
2. Link the relevant **Job Work Order**; the **Contractor** field auto-fills from it.
3. Set the **Date Logged** and enter the **Qty Sent** (matching the order) and **Wastage Qty**.
4. The **Wastage %** is computed for you automatically.
5. Choose a **Wastage Category**: **Cutting Loss** (normal, expected waste), **Contractor Damage** (caused by the contractor), **Transit Damage** (damaged in transport), or **Quality Reject** (rejected for poor quality).
6. Add any **Remarks** that explain the circumstances.
7. Click **Save**.

> A wastage entry above 15% automatically triggers a **High Wastage Alert** notification to the record owner. Wastage logs also feed the daily contractor stats job and the **Contractor Wastage Trend** report.

### 4.1 Order Status Workflow

Job Work Order status is governed by the **Job Work Order Workflow**:

```
Draft ──(Send to Contractor)──▶ Sent
Sent ──(Partial Return Received)──▶ Partially Received
Sent ──(Full Return Received)──▶ Received
Partially Received ──(Partial Return Received)──▶ Partially Received
Partially Received ──(Full Return Received)──▶ Received
Received ──(Close Order)──▶ Closed
```

Draft → Sent is open to any user; **Job Work Manager** is required to move an order through Partially Received, Received, or Closed.

---

## 5. TRACEABILITY & CUTTING FEATURES

### 5.1 Raw Material Batch → Fabric Roll
1. Log incoming material as a **Raw Material Batch** (supplier, material type, origin, certifications, quality grade, received date).
2. Create a **Fabric Roll** linked to that batch as it moves through production, capturing production stage, contractor, dimensions, weight, grade, and quality status.
3. Each processing step can be recorded as a **Process History Entry** row on the roll, building a full genealogy from raw batch to finished roll.

### 5.2 Cutting Plans & Patterns
1. Define reusable **Pattern Templates**, each made up of individual **Pattern Pieces**.
2. Create a **Cutting Plan** against a fabric roll or batch, listing planned pieces in **Cutting Plan Item** rows.
3. Submit the plan once cutting is complete; efficiency (planned vs. actual yield) is available via the **Cutting Efficiency** report.

### 5.3 Loom & Machine Output
For in-house production, register each **Loom** (by Machine ID) and log daily throughput via **Machine Output Log**, viewable on the **Loom Dashboard** (`/loom-dashboard`) web page.

---

## 6. VENDOR PORTAL & DIGITAL PRODUCT PASSPORT

### 6.1 Digital Product Passport (`/dpp/<roll_id>`)
A public web page that renders full traceability for a given Fabric Roll: its raw material batch, certifications, job work processes, and process history — suitable for a QR code printed on the finished product. No login is required to view it, so treat the roll ID as effectively public once printed.

### 6.2 Supplier Portal (`/supplier-portal`)
A self-service page for users with the **Supplier** role:
- Requires login; shows a message prompting sign-in for guests.
- Matches the logged-in user to a **Supplier** record by email, then lists all of that supplier's **Vendor Delivery Schedule** rows.
- Suppliers can revise the **Revised Delivery Date**, update **Status** (Confirmed / Delayed / Shipped), and add **Supplier Notes** directly from the portal.

---

## 7. REPORTS

| Report | Type | Based On | Purpose |
|---|---|---|---|
| Contractor Wastage Trend | Query Report | Fabric Wastage Log | Wastage % over time, by contractor |
| Cutting Efficiency | Script Report | Cutting Plan | Planned vs. actual cutting yield |
| Lot Genealogy | Script Report | Raw Material Batch | Full batch → roll → job work trace |
| Overdue Job Work Orders | Query Report | Job Work Order | Orders past their expected return date |
| True Cost Per Piece by Contractor | Script Report | Job Work Order | Rate + wastage-adjusted true unit cost |

---

## 8. WORKSPACE NAVIGATION

**Shortcuts (top row):**
- 📦 New Job Work Order
- 🧵 Fabric Rolls
- 📥 Raw Material Batch
- ✂️ Cutting Plan

**Cards:**
- **Traceability** — Raw Material Batch, Fabric Roll
- **Production** — Job Work Order, Production Schedule, Machine Output Log
- **Master Data** — Job Contractor, Loom
- **Cutting & Waste** — Cutting Plan, Pattern Template, Fabric Wastage Log
- **Vendor Portal** — Vendor Delivery Schedule
- **Reports** — Contractor Wastage Trend, True Cost Per Piece by Contractor, Overdue Job Work Orders, Cutting Efficiency, Lot Genealogy

**Chart:**
- **Wastage Trend Overview** — line chart of wastage over time, sourced from the Contractor Wastage Trend report

---

## 9. SCHEDULED TASKS & AUTOMATION

Three tasks run daily via the Frappe Scheduler:

| Task | What it does |
|---|---|
| `daily_update_contractor_wastage_stats` | Recalculates each active Job Contractor's aggregated wastage fields from all their Fabric Wastage Log entries |
| `daily_check_overdue_job_work_orders` | Scans all open orders for processes past their Expected Return Date and raises a "Process Overdue" notification |
| `daily_notify_rate_card_expiring` | Flags contractor rate card rows that have been in effect for 90+ days without an update, so rates can be reviewed |

> Make sure the scheduler is enabled on your site: `bench --site your-site.com scheduler enable`

---

## 10. SETUP & CONFIGURATION (FIXTURES)

The following are set up automatically post-install/migrate (via `pre_model_sync` / `post_model_sync` patches):

- **Module Def** — "Textile" module registered against the app
- **Roles** — Job Work Manager, Contractor Coordinator
- **Workflow** — Job Work Order Workflow, with its 5 states and 6 transitions
- **Notifications** — Job Work Overdue Alert (email + system), High Wastage Alert (system, wastage_pct > 15%)
- **Workspace Chart** — Wastage Trend Overview, linked to the Textile Tracking workspace

Standard Frappe fixtures (Workspace, DocType, Report, Workflow, Workflow State, Workflow Action, Role, Notification — all filtered to this app's module) are also exported for redeployment across sites.

---

## 11. DEMO DATA

Demo data can be seeded via the bench console command:

```bash
bench --site your-site.com insert-demo-data
```

This creates sample **Job Contractors** (with rate cards), **Job Work Orders**, **Fabric Wastage Logs**, **Raw Material Batches**, **Fabric Rolls**, **Looms**, **Pattern Templates**, and **Vendor Deliveries**, enough to explore every workflow above without manual data entry. It also runs automatically once as part of the `add_demo_data` post-model-sync patch on install.

---

## 12. TROUBLESHOOTING

| Issue | Cause | Solution |
|---|---|---|
| App not found during install | App not in `apps.txt` | `echo "textile_tracking" >> sites/apps.txt` |
| `(1054, "Unknown column 'parent' in WHERE")` on a child table | Schema sync didn't create standard child-table columns | Handled automatically post-migrate and on first request; to force it manually run `bench --site your-site.com execute textile_tracking.patches.fix_child_table_parent_columns.execute` |
| Wastage Trend Overview chart missing from workspace | Chart link wasn't created | `bench --site your-site.com execute textile_tracking.patches.create_wastage_chart.execute` |
| Job Work Order Workflow / custom roles missing | Patch didn't run (e.g. fresh site restored from backup) | `bench --site your-site.com execute textile_tracking.patches.setup_workflow_notifications.execute` |
| Scheduled tasks not running | Scheduler disabled | `bench --site your-site.com scheduler enable` |
| No Stock Entry created on submit/return | Stock module not set up, or no default/available warehouse | Set **Stock Settings → Default Warehouse**, or ensure at least one enabled, non-group Warehouse exists. Check the Error Log for details |
| Supplier can't see any deliveries in the portal | Their user isn't linked to a Supplier record | Set the **Supplier**'s `email` (or `email_id`) field to match the user's login email |
| Fixture data not loading | Fixtures not synced | `bench --site your-site.com migrate` |

---

## 13. APPENDIX

### A. Role Permissions

| Role | Job Contractor | Job Work Order | Fabric Roll / Raw Material Batch | Cutting Plan | Vendor Delivery Schedule | Submit/Amend |
|---|:---:|:---:|:---:|:---:|:---:|:---:|
| Job Work Manager | Full Access | Full Access | Full Access | Full Access | Read/Write | ✅ |
| Contractor Coordinator | Read | Create/Read/Write | Read/Write (Fabric Roll) | — | — | ❌ |
| Supplier | — | — | — | — | Read/Write | ❌ |
| System Manager | Full Access | Full Access | Full Access | Full Access | Full Access | ✅ |

### B. Key DocType Field Reference

#### Job Work Order
| Field | Type | Notes |
|---|---|---|
| Garment Type | Select | Shirt, T-Shirt, Skirt, Saree, Blouse, Kurta, Jeans, Dress, Dupatta, Fabrics (Roll) |
| Source Item | Link → Item | Optional |
| Qty Sent | Float | Required |
| Status | Select | Draft / Sent / Partially Received / Received / Closed, driven by the Workflow |
| Processes | Table → Job Work Order Process | Contractor, process, rate, and dates live here |
| Raw Material Batch / Fabric Roll | Link | For traceability |
| Job Work Returns | Table → Job Work Return | Date received, qty received/rejected/wastage |
| Total Received Qty / Total Wastage Qty | Float | Read-only, aggregated |
| Stock Entry Sent / Received | Link → Stock Entry | Read-only, auto-populated |

#### Fabric Wastage Log
| Field | Type | Notes |
|---|---|---|
| Job Work Order | Link | Optional |
| Contractor | Link → Job Contractor | Required, auto-fills from Job Work Order |
| Date Logged | Date | Required |
| Qty Sent / Wastage Qty | Float | Required |
| Wastage % | Percent | Auto-calculated |
| Wastage Category | Select | Cutting Loss / Contractor Damage / Transit Damage / Quality Reject |
| Raw Material Batch | Link | Optional, for traceability |

### C. Related Documents
- Frappe Framework Documentation: https://frappeframework.com/docs
- ERPNext Stock Module: https://docs.erpnext.com/docs/user/manual/en/stock

### D. Repository
- **Repository:** https://github.com/Pasha1234565/textile_tracking.git

---

*End of README*
