from flask import Flask, render_template, request, jsonify
import psycopg2
import psycopg2.extras
import datetime

app = Flask(__name__)

DATABASE_URL = "postgresql://postgres:mypassword123@localhost:5432/ps2"

def get_db():
    conn = psycopg2.connect(DATABASE_URL, options="-c search_path=airline_hw")
    return conn

def query(sql, params=None, one=False):
    conn = get_db()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(sql, params or ())
    result = cur.fetchone() if one else cur.fetchall()
    cur.close()
    conn.close()
    return result

def format_duration(duration):
    """Handle duration whether it's int (minutes), timedelta, or string."""
    if isinstance(duration, datetime.timedelta):
        total_mins = int(duration.total_seconds() // 60)
    elif isinstance(duration, int):
        total_mins = duration
    else:
        # Try converting string like '02:30:00' or plain number
        try:
            total_mins = int(duration)
        except:
            return str(duration)
    hours = total_mins // 60
    mins = total_mins % 60
    return f"{hours}h {mins:02d}m"

def normalize_row(r):
    """Convert postgres date/time types to plain strings."""
    d = dict(r)
    if hasattr(d.get('departure_date'), 'isoformat'):
        d['departure_date'] = d['departure_date'].isoformat()
    if hasattr(d.get('departure_time'), 'strftime'):
        d['departure_time'] = d['departure_time'].strftime('%H:%M')
    return d

@app.route('/')
def index():
    airports = query("SELECT airport_code, city, name FROM airport ORDER BY airport_code")
    return render_template('index.html', airports=airports)

@app.route('/search', methods=['GET'])
def search():
    origin = request.args.get('origin', '').upper()
    dest = request.args.get('dest', '').upper()
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')

    if not all([origin, dest, date_from, date_to]):
        return jsonify({'error': 'Missing parameters'}), 400

    flights = query('''
        SELECT 
            f.flight_number,
            f.departure_date,
            fs.airline_name,
            fs.origin_code,
            fs.dest_code,
            fs.departure_time,
            fs.duration,
            a_orig.city AS origin_city,
            a_dest.city AS dest_city
        FROM flight f
        JOIN flightservice fs ON f.flight_number = fs.flight_number
        JOIN airport a_orig ON fs.origin_code = a_orig.airport_code
        JOIN airport a_dest ON fs.dest_code = a_dest.airport_code
        WHERE fs.origin_code = %s
          AND fs.dest_code = %s
          AND f.departure_date BETWEEN %s AND %s
        ORDER BY f.departure_date, fs.departure_time
    ''', (origin, dest, date_from, date_to))

    results = []
    for r in flights:
        row = normalize_row(r)
        results.append({
            'flight_number': row['flight_number'],
            'departure_date': row['departure_date'],
            'airline_name': row['airline_name'],
            'origin_code': row['origin_code'],
            'dest_code': row['dest_code'],
            'origin_city': row['origin_city'],
            'dest_city': row['dest_city'],
            'departure_time': row['departure_time'],
            'duration': format_duration(row['duration'])
        })

    return jsonify(results)

@app.route('/flight/<flight_number>/<departure_date>')
def flight_detail(flight_number, departure_date):
    info = query('''
        SELECT 
            f.flight_number,
            f.departure_date,
            f.plane_type,
            fs.airline_name,
            fs.origin_code,
            fs.dest_code,
            fs.departure_time,
            fs.duration,
            a.capacity,
            a_orig.name AS origin_name,
            a_orig.city AS origin_city,
            a_dest.name AS dest_name,
            a_dest.city AS dest_city,
            COUNT(b.seat_number) AS booked_seats
        FROM flight f
        JOIN flightservice fs ON f.flight_number = fs.flight_number
        JOIN aircraft a ON f.plane_type = a.plane_type
        JOIN airport a_orig ON fs.origin_code = a_orig.airport_code
        JOIN airport a_dest ON fs.dest_code = a_dest.airport_code
        LEFT JOIN booking b ON b.flight_number = f.flight_number AND b.departure_date = f.departure_date
        WHERE f.flight_number = %s AND f.departure_date = %s
        GROUP BY f.flight_number, f.departure_date, f.plane_type,
                 fs.airline_name, fs.origin_code, fs.dest_code,
                 fs.departure_time, fs.duration, a.capacity,
                 a_orig.name, a_orig.city, a_dest.name, a_dest.city
    ''', (flight_number, departure_date), one=True)

    if not info:
        return render_template('detail.html', error="Flight not found"), 404

    bookings = query('''
        SELECT b.seat_number, p.passenger_name
        FROM booking b
        JOIN passenger p ON b.pid = p.pid
        WHERE b.flight_number = %s AND b.departure_date = %s
        ORDER BY b.seat_number
    ''', (flight_number, departure_date))

    flight_dict = normalize_row(info)
    duration_str = format_duration(flight_dict['duration'])
    available = flight_dict['capacity'] - flight_dict['booked_seats']

    return render_template('detail.html',
        flight=flight_dict,
        bookings=[dict(b) for b in bookings],
        available_seats=available,
        duration_str=duration_str
    )

if __name__ == '__main__':
    app.run(debug=True, port=5000)
