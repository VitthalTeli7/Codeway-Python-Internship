# Movie Ticket Booking (Flask)

A simple movie ticket booking web app built with Flask + SQLite. Features movies, showtimes, seat selection, authentication, and viewing your bookings.

## Features
- User registration and login
- List movies with posters and descriptions
- View showtimes per movie
- Interactive seat selection grid (40 seats per showtime)
- Booking multiple seats with total price calculation
- SQLite database with demo data seeding

## Tech Stack
- Flask, Flask-Login, SQLAlchemy, Bootstrap 5

## Getting Started

1. Create a virtual environment (optional but recommended):
```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Initialize the database with demo data:
```bash
flask --app app init-db
```

This creates movies, showtimes, seats, and a demo admin user:
- Email: `demo@example.com`
- Password: `password`

4. Run the development server:
```bash
python app.py
```

5. Open your browser at `http://localhost:5000`.

## Notes
- To change the seat grid size, edit `create_seats_for_showtime` in `app.py`.
- For a fresh start, re-run the `init-db` command.