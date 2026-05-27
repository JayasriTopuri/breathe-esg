# MODEL.md — Data Model Documentation

## Overview
Breathe ESG ingests emissions activity data from three source types (SAP, Utility, Travel), normalizes it, and surfaces it for analyst review before audit lock.

---

## Entities

### 1. Tenant
Multi-tenancy anchor. Every object in the system belongs to a tenant (client company).

| Field | Type | Notes |
|-------|------|-------|
| id | AutoField | Primary key |
| name | CharField | Company name |
| slug | SlugField | Unique identifier |
| created_at | DateTimeField | Auto-set on creation |

---

### 2. DataSource
One record per ingestion run. Tracks which file was uploaded, when, by whom, and how many rows succeeded or failed.

| Field | Type | Notes |
|-------|------|-------|
| id | AutoField | Primary key |
| tenant | FK → Tenant | Which client |
| source_type | CharField | SAP / UTILITY / TRAVEL |
| ingest_mode | CharField | FILE_UPLOAD (default) |
| raw_file | FileField | Original uploaded file |
| ingested_at | DateTimeField | Auto-set |
| ingested_by | FK → User | Who uploaded |
| row_count | IntegerField | Rows successfully parsed |
| error_count | IntegerField | Rows that failed parsing |
| status | CharField | PENDING / PROCESSING / DONE / FAILED |

---

### 3. ActivityRow
Central normalized table. One row = one emission-relevant activity event.

| Field | Type | Notes |
|-------|------|-------|
| id | AutoField | Primary key |
| tenant | FK → Tenant | Multi-tenancy |
| data_source | FK → DataSource | Source-of-truth tracking |
| scope | IntegerField | 1 / 2 / 3 |
| category | CharField | FUEL / ELECTRICITY / FLIGHT / HOTEL / GROUND_TRANSPORT / PROCUREMENT |
| raw_quantity | CharField | Original value as-is |
| raw_unit | CharField | Original unit as-is |
| raw_currency | CharField | Original currency |
| raw_date_str | CharField | Original date string |
| raw_reference | CharField | Document/meter/report ID |
| raw_payload | JSONField | Full original row preserved |
| quantity_kwh | FloatField | Normalized electricity |
| quantity_liters | FloatField | Normalized fuel |
| quantity_km | FloatField | Normalized travel distance |
| activity_date | DateField | Parsed and normalized date |
| location | CharField | Plant code / meter ID / route |
| vendor | CharField | Supplier name |
| notes | TextField | Extra context |
| status | CharField | PENDING / FLAGGED / APPROVED / REJECTED |
| flag_reason | TextField | Why it was flagged |
| reviewed_by | FK → User | Analyst who reviewed |
| reviewed_at | DateTimeField | When reviewed |
| locked | BooleanField | True = approved and sent to audit |
| created_at | DateTimeField | Auto-set |
| updated_at | DateTimeField | Auto-updated |

---

### 4. AuditLog
Append-only log. Written on every status change.

| Field | Type | Notes |
|-------|------|-------|
| id | AutoField | Primary key |
| activity_row | FK → ActivityRow | Which row changed |
| changed_by | FK → User | Who made the change |
| changed_at | DateTimeField | Auto-set |
| field_changed | CharField | Which field |
| old_value | TextField | Previous value |
| new_value | TextField | New value |
| action | CharField | Description of action |

---

## Multi-Tenancy
Every model (DataSource, ActivityRow) has a FK to Tenant. All queries filter by tenant_id. This ensures one client never sees another client's data.

---

## Scope 1/2/3 Categorization

| Category | Scope | Reason |
|----------|-------|--------|
| FUEL | 1 | Direct combustion by the company |
| ELECTRICITY | 2 | Indirect — purchased from grid |
| FLIGHT | 3 | Business travel, value chain |
| HOTEL | 3 | Business travel, value chain |
| GROUND_TRANSPORT | 3 | Business travel, value chain |
| PROCUREMENT | 3 | Purchased goods and services |

---

## Unit Normalization

| Source | Raw Unit | Normalized To | Logic |
|--------|----------|---------------|-------|
| SAP Fuel | L, KG, GAL | quantity_liters | KG×1.136 for diesel, GAL×3.785 |
| Utility | kWh, MWh, Units | quantity_kwh | MWh×1000, Units=kWh (India standard) |
| Travel | Airport codes | quantity_km | Haversine formula on known airport coordinates |

Raw values are always preserved in raw_quantity, raw_unit, and raw_payload (JSONField).

---

## Source-of-Truth Tracking
Every ActivityRow has a FK to DataSource, which records the original file, upload time, and uploader. This means any row can be traced back to exactly which file it came from and when.

---

## Audit Trail
AuditLog is append-only — rows are never deleted or updated, only inserted. Every status change on an ActivityRow writes a new AuditLog entry with old and new values, the user, and timestamp. Once a row is APPROVED, locked=True prevents further edits.

---

## What I Would Add With More Time
- EmissionFactor table (kgCO2e per unit, by category/region/year)
- Row-level version history (not just status changes)
- Bulk approve/reject
- API-based ingestion for SAP OData and Concur OAuth