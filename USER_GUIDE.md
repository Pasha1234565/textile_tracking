# Textile Tracking — User Guide

## Welcome!

Textile Tracking is a Frappe/ERPNext app that helps textile and garment manufacturers manage their **job work operations**. If your business sends fabric or garments to external contractors for processing (cutting, stitching, dyeing, embroidery, finishing), this app helps you:

- Track every piece of fabric you send out and receive back
- Record and categorize fabric wastage by cause
- Compare contractor performance through wastage reports
- Calculate the true cost per piece including wastage
- Get automatic alerts when orders are overdue or wastage is too high

---

## Getting Started

### First Login

1. Log into your ERPNext/Frappe site
2. You'll see the **Textile Tracking** workspace on the desk. Click it to open the main dashboard.

![The workspace has shortcut buttons, cards, and a wastage trend chart.]

### The Dashboard

The Textile Tracking workspace is your home base. It has:

**Shortcuts (top row of buttons):**
- 📦 **New Job Work Order** — Create a new order immediately
- 📋 **Fabric Wastage Log** — View all wastage records
- 📊 **Contractor Wastage Trend** — Open the wastage analysis report
- ⚠️ **Overdue Orders** — See which orders are past their return date

**Cards (middle section):**
- **Transactions** — Quick access to Job Work Orders and Wastage Logs
- **Master Data** — Manage your Job Contractors
- **Reports** — Open analytics reports

**Chart (bottom):**
- **Wastage Trend Overview** — A line chart showing wastage percentage over time

---

## Understanding the Core Concepts

### What is a Job Contractor?

A **Job Contractor** is an external party (workshop, factory, individual) that performs a specific process on your fabric or garments. For example:
- **Kashmir Stitching Works** — handles stitching
- **Raj Cutting Services** — handles cutting
- **Sara Dyeing House** — handles dyeing

Each contractor has:
- **Contact details** (email, phone, address)
- **A Rate Card** — what they charge per piece for each process
- **A Default Wastage Allowance** — the percentage of wastage you consider acceptable
- **Wastage Analytics** — automatically calculated from your logs

### What is a Job Work Order?

A **Job Work Order (JWO)** is the core transaction. It records:
- **What you sent:** which contractor, which fabric item, how many pieces
- **What process:** cutting, stitching, dyeing, embroidery, or finishing
- **When:** date sent and expected return date
- **Status:** Draft → Sent → Partially Received → Received → Closed

As returns come in, you log them in the **Job Work Returns** table within the order.

### What is a Fabric Wastage Log?

A **Fabric Wastage Log (FWL)** records any fabric waste that occurred during processing. Each entry:
- Is linked to a Job Work Order
- Records the quantity wasted and the percentage
- Categorizes the waste: Cutting Loss, Contractor Damage, Transit Damage, or Quality Reject
- Includes remarks explaining what happened

This is the most important feature — it lets you hold contractors accountable for waste by documenting the *reason* and *category*, not just the quantity.

---

## Step-by-Step Workflow

### Step 1: Create a Job Contractor

Before you can send work out, you need to set up your contractors.

1. Go to **Textile Tracking > Master Data > Contractor List**
2. Click **+ Add Job Contractor**
3. Fill in:
   - **Contractor Name** (required, unique)
   - **Contractor Type** — Select the process they perform
   - **Status** — Active or Inactive
   - **Default Wastage Allowance (%)** — e.g., 2%
   - **Email, Phone, Address** — Contact details
4. In the **Rate Card** section, add rows for each process they'll perform:
   - **Subcontract Process** — e.g., Stitching
   - **Rate Per Piece** — e.g., ₹15.00
   - **Effective From** — the date this rate applies from
5. Click **Save**

### Step 2: Create a Job Work Order

Now you're ready to send fabric for processing.

1. Click the **New Job Work Order** shortcut on the dashboard
2. Fill in:
   - **Contractor** — Select from your list
   - **Source Item** — The fabric/garment being sent (optional)
   - **Qty Sent** — Number of pieces or meters
   - **Subcontract Process** — e.g., Cutting
   - **Rate Per Piece** — Enter the agreed rate
   - **Date Sent** — Today (auto-filled)
   - **Expected Return Date** — When you expect the work back
3. The **Status** starts as **Draft**
4. Click **Save**

### Step 3: Submit the Order

When you physically hand over the fabric:

1. Open the Job Work Order
2. Click the **Workflow Actions** button (top-right)
3. Select **Send to Contractor**
4. The status changes to **Sent**

*Note: If stock features are enabled, this automatically creates a Stock Entry (Material Transfer) to track inventory movement.*

### Step 4: Log Returns

When the contractor returns the processed items:

1. Open the Job Work Order
2. Go to the **Returns** section
3. Click **+ Add Row** in the **Job Work Returns** table
4. Enter:
   - **Date Received**
   - **Qty Received** — Good pieces received
   - **Qty Rejected** — Pieces received but rejected for quality
   - **Wastage Qty** — Pieces lost/damaged during processing
   - **Wastage Reason** — Brief explanation
5. Click **Save**

### Step 5: Update Status

After logging returns, update the status through the workflow:

- If you've received **some but not all**: Select **Partial Return Received**
- If you've received **everything**: Select **Full Return Received**

The system automatically tracks how much has been received vs sent.

### Step 6: Log Wastage (if applicable)

Whenever there's wastage, create a Fabric Wastage Log:

1. Go to **Fabric Wastage Log > + Add**
2. Fill in:
   - **Job Work Order** — Link to the relevant order
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
   - **Remarks** — Any notes
3. Click **Save**

> ⚠️ **Important:** If wastage was recorded in the returns, you **must** create a Fabric Wastage Log before closing the Job Work Order. The system will block closing if wastage exists without a corresponding log.

### Step 7: Close the Order

Once everything is returned and accounted for:

1. Open the Job Work Order
2. Click **Workflow Actions > Close Order**
3. The status changes to **Closed**

---

## Reports

### 1. Contractor Wastage Trend

Shows wastage percentage trends for each contractor over time.

**How to use:**
1. Go to **Textile Tracking > Reports > Contractor Wastage Trend**
2. The report automatically shows a line chart and data table
3. Use filters to narrow by contractor or date range
4. Use this to identify which contractors consistently exceed acceptable wastage levels

### 2. True Cost Per Piece by Contractor

This is your most powerful report. It calculates the **real cost** of working with each contractor by factoring in:

- **Labor Cost** = Quantity Received × Rate Per Piece
- **Wastage Cost** = Wastage Quantity × Raw Material Value
- **True Cost Per Piece** = (Labor Cost + Wastage Cost) ÷ Quantity Received

**How to use:**
1. Go to **Textile Tracking > Reports > True Cost Per Piece**
2. Filter by contractor or date range
3. Compare the bar chart: the blue bar is the rate, the red bar is the true cost
4. A big gap between blue and red means the contractor's wastage is significantly increasing your costs

### 3. Overdue Job Work Orders

Shows all orders past their expected return date.

**How to use:**
1. Open **Textile Tracking > Reports > Overdue Orders**
2. The report lists every order that's still "Sent" or "Partially Received" past the expected date
3. Follow up with contractors immediately

---

## Notifications & Alerts

The app automatically sends notifications for:

| Alert | When | What happens |
|---|---|---|
| **Order Overdue** | 1 day after expected return date (if still open) | System notification + Email to the owner |
| **High Wastage** | When wastage > 15% on a log | System notification appears |
| **Rate Card Review** | When a rate is 90+ days old | System notification to review pricing |

You can see your notifications in the bell icon (🔔) at the top-right of any Frappe page.

---

## Roles & Permissions

There are two custom roles in this app:

| Role | What they can do |
|---|---|
| **Job Work Manager** | Full access — Create, Read, Update, Delete everything. Can see contractor rate cards. Can submit/amend/cancel Job Work Orders. |
| **Contractor Coordinator** | Limited access — Can create and read Job Work Orders and Fabric Wastage Logs. **Cannot** delete records or see contractor rate cards (prevents rate visibility disputes). |

Your System Administrator should assign these roles in **Setup > Users and Permissions > Role Assignment Manager**.

---

## Daily Tasks for the Shop Floor Manager

**Every morning, check:**

1. **🔔 Notifications** — Any overdue orders or high wastage alerts?
2. **📊 Overdue Orders Report** — Who hasn't returned fabric yet?
3. **📋 Fabric Wastage Log** — Enter any wastage from yesterday's returns

**Every week, review:**

1. **📊 Contractor Wastage Trend** — Are any contractors trending worse?
2. **📊 True Cost Per Piece** — Which contractors are actually costing more than their rate suggests?
3. **💰 Rate Cards** — Update any contractor rates that have changed

**Every month, audit:**

1. **📊 True Cost Per Piece Report** — Prepare cost analysis for management
2. **👥 Contractor Performance** — Decide which contractors to keep, renegotiate, or replace

---

## Troubleshooting

**Q: I can't see the Textile Tracking workspace**
A: Make sure you have the appropriate role assigned (Job Work Manager or Contractor Coordinator).

**Q: The system won't let me close an order**
A: Check if there's wastage recorded in the returns but no Fabric Wastage Log. Create the log first, then close.

**Q: A contractor's rate isn't showing up**
A: Rate cards need to be added manually on the Job Contractor form. Go to the contractor, add their rates in the Rate Card section, and save.

**Q: The Stock Entry isn't being created**
A: Stock Entry creation requires Stock Settings to allow material transfer to subcontractors. Check with your System Administrator.
