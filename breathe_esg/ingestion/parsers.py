import csv
import io
from datetime import datetime
from core.models import DataSource
from core.models import ActivityRow, Tenant


# ── SAP Parser ──────────────────────────────────────────────
def parse_sap(file, data_source: DataSource):
    """
    SAP ME2M/MB51 flat file export (CSV).
    Handles fuel and procurement rows.
    """
    rows_created = 0
    errors = 0

    file.seek(0)
    decoded = file.read().decode('utf-8-sig')  # handles BOM from SAP exports
    reader = csv.DictReader(io.StringIO(decoded))

    FUEL_MATERIALS = ['DIESEL', 'PETROL', 'HSD', 'LDO', 'FURNACE OIL', 'CNG', 'LPG']

    for row in reader:
        try:
            material = row.get('Material Description', '').strip().upper()
            qty_str = row.get('Quantity', '0').replace(',', '').strip()
            unit = row.get('Unit', '').strip()
            plant = row.get('Plant', '').strip()
            doc_date = row.get('Posting Date', '').strip()
            vendor = row.get('Vendor', '').strip()
            amount = row.get('Amount', '').strip()

            # Normalize date
            activity_date = None
            for fmt in ('%d.%m.%Y', '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y'):
                try:
                    activity_date = datetime.strptime(doc_date, fmt).date()
                    break
                except ValueError:
                    continue

            # Determine category
            is_fuel = any(f in material for f in FUEL_MATERIALS)
            category = 'FUEL' if is_fuel else 'PROCUREMENT'
            scope = 1 if is_fuel else 3

            # Normalize quantity to liters
            quantity = float(qty_str) if qty_str else 0.0
            quantity_liters = None
            if is_fuel:
                if unit.upper() in ['L', 'LTR', 'LITRE', 'LITER']:
                    quantity_liters = quantity
                elif unit.upper() in ['KG', 'KGS']:
                    quantity_liters = quantity * 1.136  # approx diesel conversion
                elif unit.upper() in ['GAL', 'GALLON']:
                    quantity_liters = quantity * 3.785

            ActivityRow.objects.create(
                tenant=data_source.tenant,
                data_source=data_source,
                scope=scope,
                category=category,
                raw_quantity=qty_str,
                raw_unit=unit,
                raw_currency='INR',
                raw_date_str=doc_date,
                raw_reference=row.get('Document No', '').strip(),
                raw_payload=dict(row),
                quantity_liters=quantity_liters,
                activity_date=activity_date,
                location=plant,
                vendor=vendor,
                notes=f"Amount: {amount}",
                status='PENDING',
            )
            rows_created += 1

        except Exception as e:
            errors += 1
            continue

    return rows_created, errors


# ── Utility Parser ───────────────────────────────────────────
def parse_utility(file, data_source: DataSource):
    """
    Utility portal CSV export.
    Handles electricity billing data.
    """
    rows_created = 0
    errors = 0

    decoded = file.read().decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(decoded))

    for row in reader:
        try:
            meter_id = row.get('Meter ID', '').strip()
            billing_start = row.get('Billing Period Start', '').strip()
            billing_end = row.get('Billing Period End', '').strip()
            consumption = row.get('Consumption', '0').replace(',', '').strip()
            unit = row.get('Unit', 'kWh').strip()
            amount = row.get('Amount', '').strip()
            tariff = row.get('Tariff', '').strip()

            # Normalize date
            activity_date = None
            for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y'):
                try:
                    activity_date = datetime.strptime(billing_start, fmt).date()
                    break
                except ValueError:
                    continue

            # Normalize to kWh
            quantity = float(consumption) if consumption else 0.0
            quantity_kwh = None
            if unit.upper() in ['KWH', 'KW/H']:
                quantity_kwh = quantity
            elif unit.upper() == 'MWH':
                quantity_kwh = quantity * 1000
            elif unit.upper() == 'UNITS':
                quantity_kwh = quantity  # 1 unit = 1 kWh in India

            # Flag suspiciously high consumption
            flag_reason = ''
            if quantity_kwh and quantity_kwh > 100000:
                flag_reason = 'Consumption exceeds 100,000 kWh — verify meter reading'

            ActivityRow.objects.create(
                tenant=data_source.tenant,
                data_source=data_source,
                scope=2,
                category='ELECTRICITY',
                raw_quantity=consumption,
                raw_unit=unit,
                raw_currency='INR',
                raw_date_str=billing_start,
                raw_reference=meter_id,
                raw_payload=dict(row),
                quantity_kwh=quantity_kwh,
                activity_date=activity_date,
                location=meter_id,
                vendor=row.get('Utility Provider', '').strip(),
                notes=f"Billing: {billing_start} to {billing_end} | Tariff: {tariff} | Amount: {amount}",
                status='FLAGGED' if flag_reason else 'PENDING',
                flag_reason=flag_reason,
            )
            rows_created += 1

        except Exception as e:
            errors += 1
            continue

    return rows_created, errors


# ── Travel Parser ────────────────────────────────────────────
AIRPORT_COORDS = {
    'DEL': (28.5665, 77.1031),
    'BOM': (19.0896, 72.8656),
    'BLR': (13.1986, 77.7066),
    'HYD': (17.2403, 78.4294),
    'MAA': (12.9941, 80.1709),
    'CCU': (22.6520, 88.4463),
    'LHR': (51.4700, -0.4543),
    'JFK': (40.6413, -73.7781),
    'DXB': (25.2532, 55.3657),
    'SIN': (1.3644, 103.9915),
}

def haversine_km(coord1, coord2):
    import math
    lat1, lon1 = map(math.radians, coord1)
    lat2, lon2 = map(math.radians, coord2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return 6371 * 2 * math.asin(math.sqrt(a))

def parse_travel(file, data_source: DataSource):
    """
    Corporate travel CSV export (Concur/Navan style).
    Handles flights, hotels, ground transport.
    """
    rows_created = 0
    errors = 0

    decoded = file.read().decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(decoded))

    CATEGORY_MAP = {
        'AIR': 'FLIGHT', 'FLIGHT': 'FLIGHT', 'AIRLINE': 'FLIGHT',
        'HOTEL': 'HOTEL', 'LODGING': 'HOTEL', 'ACCOMMODATION': 'HOTEL',
        'CAR': 'GROUND_TRANSPORT', 'TAXI': 'GROUND_TRANSPORT',
        'TRAIN': 'GROUND_TRANSPORT', 'GROUND': 'GROUND_TRANSPORT',
        'UBER': 'GROUND_TRANSPORT', 'OLA': 'GROUND_TRANSPORT',
    }

    for row in reader:
        try:
            expense_type = row.get('Expense Type', '').strip().upper()
            category = None
            for key, val in CATEGORY_MAP.items():
                if key in expense_type:
                    category = val
                    break
            if not category:
                category = 'FLIGHT'  # default

            travel_date = row.get('Travel Date', '').strip()
            activity_date = None
            for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y'):
                try:
                    activity_date = datetime.strptime(travel_date, fmt).date()
                    break
                except ValueError:
                    continue

            origin = row.get('Origin', '').strip().upper()
            destination = row.get('Destination', '').strip().upper()
            amount = row.get('Amount', '0').replace(',', '').strip()
            currency = row.get('Currency', 'INR').strip()
            traveler = row.get('Traveler Name', '').strip()
            nights = row.get('Nights', '').strip()

            # Compute distance for flights
            quantity_km = None
            flag_reason = ''
            if category == 'FLIGHT':
                if origin in AIRPORT_COORDS and destination in AIRPORT_COORDS:
                    quantity_km = haversine_km(
                        AIRPORT_COORDS[origin],
                        AIRPORT_COORDS[destination]
                    )
                else:
                    flag_reason = f'Unknown airport code: {origin} or {destination}'

            ActivityRow.objects.create(
                tenant=data_source.tenant,
                data_source=data_source,
                scope=3,
                category=category,
                raw_quantity=amount,
                raw_unit='currency',
                raw_currency=currency,
                raw_date_str=travel_date,
                raw_reference=row.get('Report ID', '').strip(),
                raw_payload=dict(row),
                quantity_km=quantity_km,
                activity_date=activity_date,
                location=f"{origin} → {destination}" if destination else origin,
                vendor=row.get('Vendor', '').strip(),
                notes=f"Traveler: {traveler} | Nights: {nights}",
                status='FLAGGED' if flag_reason else 'PENDING',
                flag_reason=flag_reason,
            )
            rows_created += 1

        except Exception as e:
            errors += 1
            continue

    return rows_created, errors