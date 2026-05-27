# DECISIONS.md — Design Decisions & Tradeoffs

## SAP — Fuel & Procurement Data

### Format Chosen: Flat CSV (ME2M/MB51 export)
SAP has multiple integration options: IDocs (XML), OData services, BAPIs, and flat file exports.

**Why flat CSV:**
- IDocs require SAP middleware (ALE/EDI) — not realistic for a prototype onboarding
- OData needs IT cooperation and RFC configuration on the SAP side
- BAPI calls require direct SAP system access
- Flat file exports (MB51 for material movements, ME2M for purchase orders) are what a sustainability lead can actually produce without IT involvement — they just run a transaction and export

**What I handled:**
- Material movements with fuel materials (Diesel, Petrol, HSD, LDO, Furnace Oil, CNG, LPG)
- Procurement rows for non-fuel materials
- Date formats: DD.MM.YYYY (SAP default), with fallbacks for YYYY-MM-DD and MM/DD/YYYY
- Units: L, KG, GAL with conversion to liters for fuel
- BOM handling (utf-8-sig) for German SAP configurations

**What I ignored:**
- Multi-currency procurement (assumed INR)
- Plant hierarchy lookups
- German column headers (Menge, Werk, etc.) — would need a column mapping config

**What I'd ask the PM:**
- Can their SAP team run MB51/ME2M and export CSV? Or do they need IT involvement?
- What plants are in scope?
- Are there multiple company codes?

---

## Utility — Electricity Data

### Format Chosen: Portal CSV Export
Utility data comes in three forms: PDF bills, portal CSV exports, and Green Button API.

**Why portal CSV:**
- PDF parsing requires OCR — fragile, format changes break it
- Green Button API exists but is US-centric; Indian utilities (Tata Power, MSEDCL, BESCOM) don't support it
- Portal CSV export is what a facilities team actually does — log into the utility portal, select date range, export

**What I handled:**
- Meter ID, billing period start/end, consumption, unit, tariff, utility provider
- Units: kWh, MWh, Units (1 Unit = 1 kWh, Indian standard)
- Billing periods that don't align to calendar months — stored as-is with start/end dates
- Auto-flagging rows with consumption > 100,000 kWh for analyst review

**What I ignored:**
- Multi-tariff bills (peak/off-peak)
- Reactive power charges
- PDF bill parsing

**What I'd ask the PM:**
- Which utility providers are in scope?
- Do they have portal access for all meters?
- How many meters per facility?

---

## Travel — Corporate Travel Data

### Format Chosen: CSV Export from Concur/Navan
Corporate travel platforms expose data via OAuth APIs and CSV exports.

**Why CSV export:**
- Concur API requires OAuth 2.0 + enterprise provisioning — needs IT and Concur admin access
- Navan API similarly requires setup
- CSV export is what a travel admin can produce in minutes — standard expense report export

**What I handled:**
- Flights, hotels, ground transport (car, taxi, train, Uber)
- Airport code to distance conversion using Haversine formula
- Known airport coordinates for major Indian and international airports
- Auto-flagging flights with unknown airport codes

**What I ignored:**
- Car rental emissions (distance unknown without odometer data)
- Rail emissions factors
- Hotel nights to emissions conversion (needs property-level data)

**What I'd ask the PM:**
- Which travel platform do they use — Concur, Navan, or internal?
- Do they have airport codes or just city names?
- Is personal travel mixed in with business travel?

---

## Review Workflow Decisions

### Why file upload instead of API pull?
File upload is auditable — you know exactly what file was ingested, when, and by whom. API pulls are harder to reproduce for audit purposes.

### Why SQLite for prototype?
SQLite is zero-config and sufficient for a prototype. Production would use PostgreSQL.

### Why no authentication on review endpoints?
Prototype decision — removed auth to allow React frontend to call APIs without session management. Production would require proper JWT or session auth.

### Why lock rows on approval?
Once a row is approved and sent to auditors, it must not change. Locking prevents accidental edits after sign-off.

---

## Ambiguities I Resolved

1. **Scope for procurement** — chose Scope 3 (purchased goods) per GHG Protocol
2. **Unit for electricity in India** — "Units" = kWh is standard per Indian utility billing
3. **Distance for travel** — used Haversine on airport coordinates; flagged unknown codes
4. **Tenant ID hardcoded in frontend** — prototype decision; production would use login session

---

## What I'd Ask the PM

1. Is the SAP team willing to run exports, or do we need automated pulls?
2. Which utility portals are in use — do they all support CSV export?
3. Is Concur or Navan the travel platform?
4. What emission factors should we use — IPCC, GHG Protocol, or client-specific?
5. Who are the analysts — internal team or client-side?
6. What's the SLA for review before audit submission?