import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Admin, Movie

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize database
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

# Create tables and admin user
with app.app_context():
    db.create_all()
    if not Admin.query.filter_by(username='admin').first():
        admin = Admin(username='admin', password_hash=generate_password_hash('admin123'))
        db.session.add(admin)
        db.session.commit()

@app.route('/')
def index():
    search_query = request.args.get('search', '')
    if search_query:
        movies = Movie.query.filter(Movie.title.ilike(f'%{search_query}%')).all()
    else:
        movies = Movie.query.all()
    return render_template('index.html', movies=movies)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password_hash, password):
            login_user(admin)
            return redirect(url_for('admin_dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin_dashboard():
    movies = Movie.query.all()
    return render_template('admin/dashboard.html', movies=movies)

@app.route('/admin/add_movie', methods=['GET', 'POST'])
@login_required
def add_movie():
    if request.method == 'POST':
        movie = Movie(
            title=request.form.get('title'),
            description=request.form.get('description'),
            genre=request.form.get('genre'),
            poster_url=request.form.get('poster_url'),
            download_url=request.form.get('download_url')
        )
        db.session.add(movie)
        db.session.commit()
        flash('Movie added successfully')
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/add_movie.html')

@app.route('/admin/delete_movie/<int:movie_id>')
@login_required
def delete_movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    flash('Movie deleted successfully')
    return redirect(url_for('admin_dashboard'))
