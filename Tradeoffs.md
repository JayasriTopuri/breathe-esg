# TRADEOFFS.md — What I Deliberately Did Not Build

## 1. Emission Factor Computation
**What it is:** Multiplying normalized activity data (liters, kWh, km) by kgCO2e factors to produce actual carbon numbers.

**Why I didn't build it:**
- Emission factors vary by region, year, and fuel type
- Factors need client validation before use in audit submissions
- Wrong factors are worse than no factors — they produce incorrect audit numbers
- This is a separate domain problem that deserves its own model (EmissionFactor table with source, year, region, version)

**What I built instead:** Clean normalized quantities (liters, kWh, km) that are ready for factor multiplication once factors are agreed upon.

---

## 2. PDF Bill Parsing
**What it is:** Extracting utility data directly from PDF electricity bills using OCR.

**Why I didn't build it:**
- PDF layouts differ per utility provider — MSEDCL, Tata Power, BESCOM all have different formats
- OCR is unreliable on scanned bills
- Format changes in bills break parsers silently — dangerous for audit data
- Maintenance cost is high

**What I built instead:** CSV portal export ingestion — more reliable, easier to audit, and what facilities teams already do.

---

## 3. Real-Time API Polling
**What it is:** Automatically pulling data from SAP OData, Concur API, or utility APIs on a schedule.

**Why I didn't build it:**
- SAP OData requires RFC configuration and IT cooperation
- Concur/Navan APIs require OAuth 2.0 enterprise provisioning
- Utility APIs are non-standard across providers
- File upload is more auditable — you know exactly what data came in and when

**What I built instead:** File upload with source tracking — every ingestion run is recorded with the original file, timestamp, and uploader. This is actually better for audit purposes.