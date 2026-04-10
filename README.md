# ✈ SkySearch — Airline Flight Web Application

A Flask + PostgreSQL web app that lets users search for flights by route and date range, and view seat availability for any flight.

---

## Tech Stack

- **Backend**: Python 3, Flask
- **Database**: PostgreSQL (existing `ps2` database, `airline_hw` schema)
- **Frontend**: HTML + CSS + vanilla JavaScript (no frameworks)
- **DB Driver**: psycopg2

---

## Project Structure

```
your_folder/
├── app.py               ← Flask backend, all routes and DB queries
├── requirements.txt     ← Python dependencies
└── templates/
    ├── index.html       ← Search form + flight results table
    └── detail.html      ← Flight detail page with seat map
```

---

## Prerequisites

- Python 3.8 or higher installed
- PostgreSQL running locally on port 5432
- Database `ps2` exists with schema `airline_hw`
- Schema has these 6 tables: `airport`, `aircraft`, `flightservice`, `flight`, `passenger`, `booking`

---

## Setup & Run

**Step 1 — Go into your project folder:**
```bash
cd /path/to/your_folder
```

**Step 2 — Create and activate a virtual environment:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Step 3 — Install dependencies:**
```bash
pip install flask psycopg2-binary
```

**Step 4 — Run the app:**
```bash
python app.py
```

**Step 5 — Open in browser:**
```
http://127.0.0.1:5000
```

> Keep the terminal open while using the app. Closing it stops the server.

---

## Database Connection

The connection is configured in `app.py`:

```python
DATABASE_URL = "postgresql://postgres:mypassword123@localhost:5432/ps2"

def get_db():
    conn = psycopg2.connect(DATABASE_URL, options="-c search_path=airline_hw")
    return conn
```

- **Host**: localhost
- **Port**: 5432
- **Database**: ps2
- **Schema**: airline_hw
- **User**: postgres
- **Password**: mypassword123

To change any of these, edit the `DATABASE_URL` line and/or the `search_path` value in `app.py`.

---

## Database Schema

```
Airport      (airport_code PK, name, city, country)
Aircraft     (plane_type PK, capacity)
FlightService(flight_number PK, airline_name, origin_code FK, dest_code FK, departure_time, duration)
Flight       (flight_number PK FK, departure_date PK, plane_type FK)
Passenger    (pid PK, passenger_name)
Booking      (pid PK FK, flight_number PK FK, departure_date PK FK, seat_number)
```

- All departure times are in GMT
- `duration` is stored as PostgreSQL `interval` type (handled automatically by the app)

---

## Features

### a) Search Form (Home Page)
- Dropdown to select origin airport
- Dropdown to select destination airport
- Date range picker (from date / to date)
- Search button triggers a live fetch — no page reload

### b) Flight Results
Displays a table with:
- Flight number
- Airline name
- Origin and destination codes + city names
- Departure date
- Departure time (GMT)
- Flight duration

All flights in the date range are shown regardless of whether they are fully booked.

### c) Flight Detail Page
Click any flight row to see:
- Full flight info (aircraft type, route, times)
- Total seat capacity of the plane
- Number of available seats
- Capacity fill bar (turns red when over 80% full)
- Visual seat map (dark = booked, light = available, hover for passenger name)
- Passenger manifest table with seat numbers

---

## API Routes

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/` | Home page with search form |
| GET | `/search?origin=&dest=&date_from=&date_to=` | Returns JSON list of matching flights |
| GET | `/flight/<flight_number>/<departure_date>` | Flight detail page |

---

## Test Queries for Demo

### Verify DB connection before running:
```bash
python3 -c "
import psycopg2
conn = psycopg2.connect('postgresql://postgres:mypassword123@localhost:5432/ps2', options='-c search_path=airline_hw')
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM airport')
print('Airports:', cur.fetchone()[0])
cur.execute('SELECT COUNT(*) FROM flight')
print('Flights:', cur.fetchone()[0])
cur.execute('SELECT COUNT(*) FROM booking')
print('Bookings:', cur.fetchone()[0])
conn.close()
print('Connection OK')
"
```

### UI Test Cases:

**Test 1 — Search with results:**
- Pick any origin/destination pair that exists in your `flightservice` table
- Set a wide date range e.g. 2024-01-01 to 2026-12-31
- Expected: flight results table appears

**Test 2 — Search with no results:**
- Pick two airports with no route between them
- Expected: "No flights found" message

**Test 3 — View seat availability:**
- Click any flight from Test 1 results
- Expected: detail page with seat count, seat map, passenger list

**Test 4 — Live DB change (TA demo):**

Open a new terminal:
```bash
psql -U postgres -d ps2
SET search_path TO airline_hw;
```

Add a booking and refresh the detail page:
```sql
INSERT INTO booking VALUES ('P001', 'AA101', '2024-01-15', 22);
```
→ Available seats should drop by 1.

Add a new flight and search for it:
```sql
INSERT INTO flight VALUES ('AA101', '2026-06-01', 'Boeing 737');
```
→ Search that route with a date covering June 2026, new flight appears.

---

## Common Errors & Fixes

| Error | Cause | Fix |
|-------|-------|-----|
| `relation "airport" does not exist` | Wrong schema name | Check `search_path=airline_hw` in `get_db()` |
| `command not found: python` | Mac uses python3 | Use `python3 app.py` or activate `.venv` first |
| `Access to 127.0.0.1 was denied` | Missing port in URL | Go to `http://127.0.0.1:5000` not `127.0.0.1` |
| `TypeError: timedelta % int` | duration is interval type | Already fixed in latest app.py |
| `500 error on search` | DB query failed | Check terminal for full traceback |

---

## Stopping the App

Press `Ctrl + C` in the terminal where the app is running.

---

## Restarting After Changes

Any time you edit `app.py`, stop and restart:
```bash
python app.py
```

The app runs in debug mode so most Python errors will show in the terminal with a full traceback.
