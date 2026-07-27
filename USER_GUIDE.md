# Textile Tracking — User Guide

## Welcome!

**Textile Tracking** is a Frappe/ERPNext app that helps textile and garment manufacturers manage their **job work operations**. If your business sends fabric or garments to external contractors for processing (cutting, stitching, dyeing, embroidery, finishing), this app helps you:

- ✅ Track every piece of fabric you send out and receive back
- ✅ Record and categorize fabric wastage by cause
- ✅ Compare contractor performance through wastage reports
- ✅ Calculate the true cost per piece including wastage
- ✅ Get automatic alerts when orders are overdue or wastage is too high
- ✅ Trace raw materials from supplier to finished fabric roll
- ✅ Manage factory floor machines and production schedules
- ✅ View a live loom dashboard and supplier portal

---

## Getting Started

### First Login

1. Log into your ERPNext/Frappe site
2. You'll see the **Textile Tracking** workspace on the desk. Click it to open the main dashboard.

### The Workspace Dashboard

The Textile Tracking workspace is your home base. It has organized sections:

**Quick Actions (Shortcuts):**
- 🆕 **New Job Work Order** — Create a new order immediately
- 📦 **Fabric Rolls** — Manage finished fabric inventory
- 📦 **Raw Material Batch** — Track incoming materials
- ✂️ **Cutting Plan** — Plan fabric cutting layouts

**Card Sections:**
- **Traceability** — Raw Material Batches, Fabric Rolls
- **Production** — Job Work Orders, Production Schedules, Machine Output Logs
- **Master Data** — Job Contractors, Looms
- **Cutting & Waste** — Cutting Plans, Pattern Templates, Fabric Wastage Logs
- **Vendor Portal** — Vendor Delivery Schedules
- **Reports & Analytics** — All 5 reports + Wastage Trend chart

---

## Understanding the Core Concepts

### What is a Job Contractor?

A **Job Contractor** is an external party (workshop, factory, individual) that performs a specific process on your fabric. For example:
- **Kashmir Stitching Works** — handles stitching
- **Raj Cutting Services** — handles cutting
- **Sara Dyeing House** — handles dyeing
- **Punjab Embroidery** — handles embroidery
- **Finishing Masters** — handles finishing

Each contractor has:
- **Contact details** (email, phone, address)
- **A Rate Card** — what they charge per piece for each process
- **A Default Wastage Allowance** — the % of wastage you consider acceptable
- **Wastage Analytics** — automatically calculated from your logs

### What is a Job Work Order?

A **Job Work Order (JWO)** is the core transaction. It records:
- **What you sent:** which item, how many pieces
- **Garment type:** Shirt, T-Shirt, Saree, etc.
- **Multiple processes:** Each JWO can have multiple processes (e.g., Cutting → Stitching → Finishing), each with its own contractor and dates
- **Status lifecycle:** Draft → Sent → Partially Received → Received → Closed

When returns come in, you log them in the **Job Work Returns** table.

### What is a Fabric Wastage Log?

A **Fabric Wastage Log (FWL)** records fabric waste that occurred during processing. Each entry:
- Links to a Job Work Order
- Records quantity wasted and percentage
- Categorizes the waste: Cutting Loss, Contractor Damage, Transit Damage, Quality Reject
- Tracks which contractor was responsible

### What is a Raw Material Batch?

A **Raw Material Batch (RMB)** tracks incoming raw materials from suppliers:
- Material type (Cotton, Polyester, Silk, etc.)
- Country of origin and supplier details
- Certifications (GOTS, OEKO-TEX, Fair Trade, BCI)
- Storage location in your warehouse
- Can be traced forward to Fabric Rolls

### What is a Fabric Roll?

A **Fabric Roll** represents a finished roll of fabric:
- Physical dimensions (length, width, weight)
- Quality grade and status
- Linked to the raw material batch that produced it
- Linked to the Job Work Order that processed it
- Has a **Digital Product Passport** with a QR code
- Tracks daily garment production from the roll

---

## Step-by-Step Workflow

### Step 1: Create a Job Contractor

1. Go to **Textile Tracking > Master Data > Job Contractor**
2. Click **+ Add Job Contractor**
3. Fill in:
   - **Contractor Name** (required, unique)
   - **Contractor Type** — Select the process they perform
   - **Status** — Active or Inactive
   - **Default Wastage Allowance (%)** — e.g., 2%
   - **Email, Phone, Address**
4. In the **Rate Card** section, add rows for each process:
   - **Subcontract Process** — e.g., Stitching
   - **Rate Per Piece** — e.g., ₹15.00
   - **Effective From** — Date this rate applies from
5. Click **Save**

### Step 2: Add a Raw Material Batch

1. Go to **Textile Tracking > Traceability > Raw Material Batch**
2. Click **+ Add Raw Material Batch**
3. Fill in:
   - **Batch ID** — e.g., COT-2024-001
   - **Material Type** — Cotton, Polyester, etc.
   - **Supplier** — Link to your Supplier
   - **Country of Origin**
   - **Certification Type** — GOTS, OEKO-TEX, etc.
   - **Received Date, Quantity, UOM**
   - **Storage Location** — e.g., Aisle-B-Rack-3
4. Click **Save**

### Step 3: Create a Job Work Order

1. Click the **New Job Work Order** shortcut on the dashboard
2. Fill in:
   - **Garment Type** — Select from: Shirt, T-Shirt, Skirt, Saree, Blouse, Kurta, Jeans, Dress, Dupatta, Fabrics (Roll)
   - **Source Item** — The fabric/garment being sent
   - **Qty Sent** — Number of pieces or meters
   - **Raw Material Batch** — (Optional) Link to the batch used
3. The **Processes** table auto-populates based on garment type:
   - *Shirt* → Cutting, Stitching, Finishing
   - *Saree* → Cutting, Stitching, Dyeing, Embroidery, Finishing
   - *Jeans* → Cutting, Stitching, Dyeing, Finishing
   - *Fabrics (Roll)* → Dyeing, Finishing
4. For each process row, fill in:
   - **Contractor** — Who performs this process
   - **Date Sent** — When it was sent
   - **Expected Return** — When you expect it back
   - **Rate Per Piece** — Agreed rate
5. The **Status** starts as **Draft**
6. Click **Save**

> 💡 **Tip:** If you leave the Processes table empty and select a Garment Type, it auto-populates the right processes for that garment!

### Step 4: Submit the Order

When you physically hand over the fabric:

1. Open the Job Work Order
2. Click **Save** first if you just created it
3. Click **Submit** (or use Workflow Actions > Send to Contractor)
4. The status changes to **Sent**

*Note: If stock features are enabled, this automatically creates a Stock Entry (Material Transfer) to track inventory movement.*

### Step 5: Log Returns

When the contractor returns processed items:

1. Open the Job Work Order
2. Go to the **Returns** section
3. Click **+ Add Row** in the **Job Work Returns** table
4. Enter:
   - **Date Received**
   - **Qty Received** — Good pieces received
   - **Qty Rejected** — Pieces received but rejected for quality
   - **Wastage Qty** — Pieces lost/damaged during processing
   - **Wastage Reason** — Brief explanation
5. You can add multiple return entries (e.g., partial returns over several days)
6. Click **Save**

The system automatically tracks total received and total wastage quantities in the **Costing Summary** section.

### Step 6: Update JWO Status

After logging returns, update the workflow status:

- If you've received **some but not all**: Use **Partial Return Received**
- If you've received **everything**: Use **Full Return Received**
- The status changes to **Partially Received** or **Received**

### Step 7: Create a Fabric Wastage Log

Whenever there's wastage, create a Fabric Wastage Log:

1. Go to **Fabric Wastage Log > + Add**
2. Fill in:
   - **Job Work Order** — Link to the relevant order (contractor auto-fills)
   - **Contractor** — Auto-filled from the order
   - **Date Logged**
   - **Qty Sent** — Same as the order
   - **Wastage Qty** — Quantity wasted
   - **Wastage %** — Computed automatically
   - **Wastage Category** — Select the cause:
     - *Cutting Loss* — Normal cutting waste
     - *Contractor Damage* — Damage caused by the contractor
     - *Transit Damage* — Damage during transportation
     - *Quality Reject* — Rejected due to poor quality
   - **Remarks** — Explain what happened
3. Click **Save**

> ⚠️ **Important:** If wastage was recorded in the returns, you **must** create a Fabric Wastage Log before closing the Job Work Order. The system will block closing if wastage exists without a corresponding log.

### Step 8: Create a Fabric Roll

When fabric is finished and ready for inventory:

1. Go to **Fabric Rolls > + Add**
2. Fill in:
   - **Roll Number** — Physical roll identifier
   - **Fabric Item** — The finished item code
   - **Production Stage** — Grey/Bleached/Dyed/Printed/Finished
   - **Length, Width, Weight**
   - **Grade** — Premium/A/B/C/Reject
   - **Quality Status** — Passed/Quarantine/Failed
   - **Raw Material Batch** — Link to the source batch
   - **Job Work Order** — Link to the processing order
   - **Garment Type & Size** — What garment is being produced
3. In the **Daily Production** section, record production as garments are made
4. Click **Save** then **Submit**
5. A **Digital Product Passport** URL and QR code are auto-generated!

### Step 9: Close the Order

Once everything is returned and accounted for:

1. Open the Job Work Order
2. Click **Workflow Actions > Close Order**
3. The status changes to **Closed**

---

## Managing Factory Operations

### Loom / Machine Management

**Creating a Loom:**
1. Go to **Textile Tracking > Master Data > Loom**
2. Click **+ Add Loom**
3. Fill in: Machine ID, Type (Airjet, Rapier, etc.), Status, Speed, Location, Operator

**Logging Machine Output:**
1. Go to **Machine Output Log > + Add Machine Output Log**
2. Select the loom, date, shift
3. Enter meters produced, runtime minutes, defect count
4. Optionally record downtime reason

### Production Scheduling

1. Go to **Production Schedule > + Add Production Schedule**
2. Set the date and shift
3. Add schedule items linking looms, job work orders, and target meters
4. Set start/end times for each item
5. Submit when finalized

### Cutting Plans

1. Go to **Cutting Plan > + Add Cutting Plan**
2. Select the fabric roll (measurements auto-fetch)
3. Add cutting items with pattern templates and planned quantities
4. Submit to finalize

### Pattern Templates

1. Go to **Pattern Template > + Add Pattern Template**
2. Define the template name and fabric item
3. Add pattern pieces with width, height, and quantity per roll
4. Set fabric direction (Along Grain, Cross Grain, Biased)

---

## Web Portals

### 🔍 Digital Product Passport

Every Fabric Roll has a **Digital Product Passport** — a public web page showing the complete lifecycle of the fabric.

**Access:** `/dpp/<roll_id>` (e.g., http://your-site/dpp/FBR-2024-0001)

**What it shows:**
- Fabric details (roll number, item, grade, quality, stage)
- Measurements (length, width, weight)
- Raw material origin (batch ID, material type, country, certifications)
- Job Work Order processes (each process, contractor, dates, status)
- Manufacturing timeline (chronological process history)
- QR code for physical verification
- EU 2027 compliance statement

**Use cases:**
- Share with customers to prove sustainable sourcing
- Attach to physical fabric rolls via QR code sticker
- Provide transparency for certification (GOTS, OEKO-TEX, Fair Trade)

### 🏭 Factory Floor Dashboard

**Access:** `/loom-dashboard`

A live dashboard showing your entire factory floor:

**Summary stats:**
- 🟢 **Running** — Number of machines currently running
- 🟡 **Idle** — Machines idle
- 🔴 **Down/Maintenance** — Machines under maintenance or breakdown
- 📊 **Avg Efficiency** — Average efficiency across all looms
- 📏 **Total Meters Today** — Total production today

**Per-machine cards show:**
- Machine ID and type
- Status with color indicator (green/yellow/red)
- Today's meters produced
- Current RPM
- Efficiency %
- Defect count
- Location
- Today's production schedule

**Use cases:**
- Display on a TV in the factory floor
- Quick morning check-in
- Identify idle or problematic machines

### 🤝 Supplier Collaboration Portal

**Access:** `/supplier-portal`

A portal for your raw material suppliers to update delivery schedules:

**Features:**
- 🔒 Login with Frappe user account
- 👤 Automatically identifies the supplier from your user profile
- 📦 View all your delivery schedules in a table
- ✏️ Update delivery dates inline
- 📋 Change status: Confirmed → Delayed → Shipped
- 📝 Add notes explaining delays
- 📊 Stats dashboard: total deliveries, pending updates

**Use cases:**
- Suppliers can update delivery dates without calling or emailing
- Reduces manual data entry by your team
- Real-time visibility into incoming materials
- Suppliers take ownership of their delivery commitments

---

## Reports

### 1. Contractor Wastage Trend

Shows wastage percentage trends for each contractor over time.

**How to use:**
1. Go to **Textile Tracking > Reports > Contractor Wastage Trend**
2. The report shows a line chart and data table
3. Use this to identify which contractors consistently exceed acceptable wastage levels

### 2. True Cost Per Piece by Contractor

This is your most powerful report. It calculates the **real cost** of working with each contractor by factoring in both labor and waste.

**The math:**
```
Labor Cost    = Qty Received × Rate Per Piece
Wastage Cost  = Wastage Qty × Raw Material Value
True Cost     = (Labor Cost + Wastage Cost) ÷ Qty Received
```

**How to use:**
1. Go to **Textile Tracking > Reports > True Cost Per Piece by Contractor**
2. Filter by contractor or date range
3. Compare the bar chart: **blue bar** is the rate, **red bar** is the true cost
4. A big gap means the contractor's wastage is significantly increasing your costs

### 3. Overdue Job Work Orders

Shows all orders past their expected return date.

**Columns:** JWO, Garment Type, Source Item, Qty Sent, Processes chain, Contractors, Earliest Expected Return, Days Overdue, Status

**How to use:**
1. Go to **Textile Tracking > Reports > Overdue Job Work Orders**
2. Follow up with contractors on overdue orders
3. Daily check is recommended

### 4. Cutting Efficiency

Analyzes cutting plan performance.

**Columns:** Cutting Plan, Fabric Roll, Dimensions, Total Area, Fabric Used, Est. Waste %, Status

**Chart:** Bar chart comparing Est. Waste % and Fabric Used per plan

### 5. Lot Genealogy

Complete traceability tree from raw material to finished fabric.

**Three modes:**
- **Filter by Raw Material Batch** → Shows the batch + all fabric rolls produced from it
- **Filter by Fabric Roll** → Shows the roll + its source raw material batch
- **No filter** → Shows all batches with their fabric roll counts

**Use cases:**
- Recall management: find all fabric rolls from a problematic batch
- Quality investigation: trace a defective roll back to its raw material
- Audit: provide complete chain of custody

---

## Notifications & Alerts

The app automatically sends notifications for:

| Alert | When | Where |
|-------|------|-------|
| 🕐 **Order Overdue** | 1 day after expected return date (if still open) | System Notification (bell icon) |
| ⚠️ **High Wastage** | When wastage > 15% on a log | System Notification |
| 💰 **Rate Card Review** | When a rate is 90+ days old | System Notification to review pricing |
| 📋 **Daily Stats Update** | Every day (scheduled) | Updates contractor wastage analytics |

You can see your notifications in the bell icon (🔔) at the top-right of any Frappe page.

---

## Roles & Permissions

| Role | What they can do |
|------|-----------------|
| **System Manager** | Full access to everything |
| **Job Work Manager** | Full CRUD on all doctypes. Can submit, amend, cancel Job Work Orders. Can see contractor rate cards. |
| **Contractor Coordinator** | Can create and read Job Work Orders, Fabric Wastage Logs, Fabric Rolls. **Cannot** delete records or see contractor rate cards. |

Your System Administrator should assign these roles in **Setup > Users and Permissions > Role Assignment Manager**.

---

## Daily Tasks for the Shop Floor Manager

**Every morning, check:**

1. 🔔 **Notifications** — Any overdue orders or high wastage alerts?
2. 📊 **Overdue Orders Report** — Who hasn't returned fabric yet?
3. 📋 **Fabric Wastage Log** — Enter any wastage from yesterday's returns
4. 🏭 **Loom Dashboard** — Check which machines are running/idle/down

**Every week, review:**

1. 📊 **Contractor Wastage Trend** — Are any contractors trending worse?
2. 📊 **True Cost Per Piece** — Which contractors cost more than their rate suggests?
3. 💰 **Rate Cards** — Update any contractor rates that have changed

**Every month, audit:**

1. 📊 **True Cost Per Piece Report** — Prepare cost analysis for management
2. 👥 **Contractor Performance** — Decide which contractors to keep, renegotiate, or replace
3. 📜 **Lot Genealogy** — Run traceability audits for compliance

---

## Fabric Roll Production Tracking

### Garment Production Estimates

When you set up a Fabric Roll with garment type and size, the system automatically calculates:

- **Estimated Fabric Per Garment** — Based on a built-in consumption database
- **Estimated Garments Per Roll** — Roll length ÷ fabric per garment
- **Total Estimated Garments** — Est. per roll × rolls given to contractor

### Daily Production Logging

In the **Daily Production** table on the Fabric Roll:
1. Click **+ Add Row**
2. Enter the date and number of garments produced
3. Add optional notes

### Wastage Calculation

The system automatically compares:
- **Estimated garments** (from roll length and garment type)
- **Actual garments produced** (sum of daily production entries)
- **Wastage %** = ((Estimated - Actual) ÷ Estimated) × 100

---

## Troubleshooting

### Common Issues

| Problem | Likely Cause | Solution |
|---------|-------------|----------|
| **Can't see Textile Tracking workspace** | Missing role assignment | Contact System Admin for proper role |
| **Can't close an order** | Wastage exists without a Fabric Wastage Log | Create the wastage log first |
| **Processes table is empty** | Garment type not selected | Select a garment type to auto-populate |
| **Stock Entry not created** | Stock Settings not configured | Enable subcontractor transfer in Stock Settings |
| **Digital Product Passport shows error** | Invalid roll ID | Check the URL has the correct Fabric Roll name |
| **Supplier portal shows "Login Required"** | Not logged in | Log in with your Frappe account |
| **Loom dashboard empty** | No looms created | Add looms in Master Data > Loom |
| **Rate not showing on JWO** | Rate not set in process row | Rates are manually entered per process |

### Getting Help

- Contact your **System Administrator** for role assignments and configuration
- Check the **Developer Guide** for technical troubleshooting
- Submit issues to your development team with screenshots and error messages
