import os
from datetime import datetime, timedelta
from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movie_booking.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    duration_minutes = db.Column(db.Integer, nullable=False)
    poster_url = db.Column(db.String(500), nullable=True)
    showtimes = db.relationship('Showtime', backref='movie', lazy=True)


class Showtime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    ticket_price = db.Column(db.Float, nullable=False, default=10.0)
    seats = db.relationship('Seat', backref='showtime', lazy=True)


class Seat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    showtime_id = db.Column(db.Integer, db.ForeignKey('showtime.id'), nullable=False)
    seat_label = db.Column(db.String(10), nullable=False)
    is_booked = db.Column(db.Boolean, default=False)


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    showtime_id = db.Column(db.Integer, db.ForeignKey('showtime.id'), nullable=False)
    seat_labels = db.Column(db.Text, nullable=False)  # CSV of seat labels
    total_price = db.Column(db.Float, nullable=False)
    booked_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('bookings', lazy=True))
    showtime = db.relationship('Showtime', backref=db.backref('bookings', lazy=True))


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def create_seats_for_showtime(showtime: Showtime, rows: int = 5, cols: int = 8) -> None:
    for r in range(rows):
        row_label = chr(ord('A') + r)
        for c in range(1, cols + 1):
            seat = Seat(showtime_id=showtime.id, seat_label=f"{row_label}{c}")
            db.session.add(seat)


def seed_demo_data() -> None:
    if Movie.query.count() > 0:
        return

    demo_movies = [
        {
            'title': 'Interstellar',
            'description': 'A team of explorers travel through a wormhole in space in an attempt to ensure humanity\'s survival.',
            'duration_minutes': 169,
            'poster_url': 'https://m.media-amazon.com/images/I/91kFYg4fX3L._AC_SL1500_.jpg'
        },
        {
            'title': 'Inception',
            'description': 'A thief who steals corporate secrets through dream-sharing technology is given an inverse task of planting an idea.',
            'duration_minutes': 148,
            'poster_url': 'https://m.media-amazon.com/images/I/51s+JvFsHkL._AC_.jpg'
        },
        {
            'title': 'The Dark Knight',
            'description': 'Batman faces the Joker, a criminal mastermind who plunges Gotham into anarchy.',
            'duration_minutes': 152,
            'poster_url': 'https://m.media-amazon.com/images/I/51K8ouYrHeL._AC_.jpg'
        }
    ]

    for movie_data in demo_movies:
        movie = Movie(**movie_data)
        db.session.add(movie)
        db.session.flush()  # to get movie.id

        base_time = datetime.utcnow().replace(minute=0, second=0, microsecond=0) + timedelta(hours=2)
        for i in range(3):
            showtime = Showtime(
                movie_id=movie.id,
                start_time=base_time + timedelta(hours=3 * i),
                ticket_price=10.0 + 2.0 * i
            )
            db.session.add(showtime)
            db.session.flush()
            create_seats_for_showtime(showtime)

    # Create a demo user
    if not User.query.filter_by(email='demo@example.com').first():
        user = User(name='Demo User', email='demo@example.com', is_admin=True)
        user.set_password('password')
        db.session.add(user)

    db.session.commit()


@app.route('/')
def home():
    movies = Movie.query.all()
    return render_template('index.html', movies=movies)


@app.route('/movie/<int:movie_id>')
def movie_detail(movie_id: int):
    movie = Movie.query.get_or_404(movie_id)
    return render_template('movie_detail.html', movie=movie)


@app.route('/showtime/<int:showtime_id>')
def showtime_detail(showtime_id: int):
    showtime = Showtime.query.get_or_404(showtime_id)
    seats = Seat.query.filter_by(showtime_id=showtime.id).order_by(Seat.seat_label.asc()).all()
    # Organize seats by row for grid
    rows = {}
    for seat in seats:
        row_label = seat.seat_label[0]
        rows.setdefault(row_label, []).append(seat)
    return render_template('showtime.html', showtime=showtime, rows=rows)


@app.route('/book/<int:showtime_id>', methods=['POST'])
@login_required
def book_tickets(showtime_id: int):
    showtime = Showtime.query.get_or_404(showtime_id)
    selected_seats = request.form.getlist('seats')
    if not selected_seats:
        flash('Please select at least one seat.', 'warning')
        return redirect(url_for('showtime_detail', showtime_id=showtime.id))

    # Verify availability
    seats = Seat.query.filter(Seat.showtime_id == showtime.id, Seat.seat_label.in_(selected_seats)).all()
    if len(seats) != len(selected_seats) or any(s.is_booked for s in seats):
        flash('One or more selected seats are no longer available. Please try again.', 'danger')
        return redirect(url_for('showtime_detail', showtime_id=showtime.id))

    # Book
    for seat in seats:
        seat.is_booked = True
    total_price = showtime.ticket_price * len(selected_seats)
    booking = Booking(user_id=current_user.id, showtime_id=showtime.id, seat_labels=','.join(selected_seats), total_price=total_price)
    db.session.add(booking)
    db.session.commit()

    flash(f'Booking confirmed for seats: {", ".join(selected_seats)}', 'success')
    return redirect(url_for('my_bookings'))


@app.route('/bookings')
@login_required
def my_bookings():
    bookings = Booking.query.filter_by(user_id=current_user.id).order_by(Booking.booked_at.desc()).all()
    return render_template('bookings.html', bookings=bookings)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            next_url = request.args.get('next')
            return redirect(next_url or url_for('home'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        if not name or not email or not password:
            flash('All fields are required.', 'warning')
            return render_template('register.html', name=name, email=email)
        if User.query.filter_by(email=email).first():
            flash('Email already in use.', 'warning')
            return render_template('register.html', name=name, email=email)
        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('home'))


@app.cli.command('init-db')
def init_db_command():
    db.drop_all()
    db.create_all()
    seed_demo_data()
    print('Initialized the database with demo data.')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_demo_data()
    app.run(host='0.0.0.0', port=5000, debug=True)