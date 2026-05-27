# SOURCES.md — Research & Sample Data Documentation

## 1. SAP — Fuel & Procurement

### What I Researched
- SAP MB51 (Material Document List) transaction — used for material movements including fuel consumption
- SAP ME2M (Purchase Orders by Material) — used for procurement data
- SAP flat file exports produce CSV with columns: Document No, Posting Date, Material Description, Quantity, Unit, Plant, Vendor, Amount
- SAP systems in Indian configurations often use DD.MM.YYYY date format
- Some SAP configurations export German headers (Menge = Quantity, Werk = Plant, Buchungsdatum = Posting Date)
- Units vary: L (liters), KG (kilograms), GAL (gallons), EA (each for non-fuel items)

### What My Sample Data Looks Like
- 10 rows covering fuel (Diesel, Petrol, Furnace Oil, LPG, CNG, HSD) and procurement (Office Supplies, Safety Equipment)
- Dates in DD.MM.YYYY format (SAP default)
- Mix of units: L and KG
- Three plants: PLANT01, PLANT02, PLANT03
- Indian vendors: Indian Oil Corp, BPCL, HPCL, Gujarat Gas

### What Would Break in Production
- German column headers — need a column mapping config per client
- Multiple company codes in one export — need company code filter
- Material numbers instead of descriptions — need material master lookup table
- Amounts in multiple currencies — need currency normalization
- Large exports (100k+ rows) — need chunked processing

---

## 2. Utility — Electricity

### What I Researched
- Indian utility portal exports (Tata Power, MSEDCL, BESCOM, APEPDCL) produce CSV with: Meter ID, Billing Period, Consumption, Unit, Amount, Tariff
- Indian utilities measure consumption in "Units" where 1 Unit = 1 kWh — this is standard across all Indian utilities
- Billing periods do NOT align to calendar months — a bill might cover 28 days or 35 days
- Multiple meters per facility are common — each meter has its own billing cycle
- Tariff categories: Commercial HT, Commercial LT, Industrial, Residential

### What My Sample Data Looks Like
- 8 rows across 4 meters (MTR-001 to MTR-004)
- Two billing periods: January and February 2026
- Mix of units: kWh and Units
- Multiple utility providers: Tata Power, MSEDCL, BESCOM, APEPDCL
- One deliberately high reading (125,000 kWh) to trigger auto-flagging

### What Would Break in Production
- Utility portal login required — no automated export without credentials
- PDF bills instead of CSV — common for smaller facilities
- Multi-tariff bills (peak/off-peak split) — single consumption field doesn't capture this
- Billing period misalignment — 35-day bills create gaps in monthly reporting
- Meter ID changes when meters are replaced — breaks historical continuity

---

## 3. Corporate Travel — Flights, Hotels, Ground Transport

### What I Researched
- Concur expense report CSV export contains: Report ID, Traveler Name, Expense Type, Travel Date, Origin, Destination, Amount, Currency, Vendor
- Navan (formerly TripActions) has similar export format
- Expense types vary: Air, Flight, Airline (all mean flights), Hotel, Lodging, Car, Taxi, Train, Ground
- Airport codes are IATA 3-letter codes (DEL, BOM, BLR, etc.)
- Distance is not always provided — must be computed from airport codes using Haversine formula
- Hotel stays recorded as nights, not distance
- Ground transport rarely has distance data

### What My Sample Data Looks Like
- 10 rows covering flights (domestic and international), hotels, car/taxi, train
- IATA airport codes for major Indian airports (DEL, BOM, BLR, HYD, MAA) and international (LHR, DXB)
- Mix of domestic (IndiGo, SpiceJet) and international (Air India, Emirates) carriers
- One train booking (IRCTC) to test ground transport parsing
- Amounts in INR

### What Would Break in Production
- City names instead of airport codes — "Mumbai" vs "BOM" — need fuzzy matching
- Multi-leg flights recorded as single rows — distance calculation wrong
- Personal expenses mixed with business travel — no automated way to filter
- International amounts in foreign currency — need exchange rate API
- Hotel chains with multiple properties in same city — location ambiguous