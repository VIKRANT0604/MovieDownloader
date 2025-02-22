import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, Admin, Movie, Review
from datetime import datetime

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

# Create tables and owner account
with app.app_context():
    db.create_all()
    if not Admin.query.filter_by(username='vicky_choudhary_0604').first():
        owner = Admin(
            username='vicky_choudhary_0604',
            password_hash=generate_password_hash('vicky0604@#'),
            is_owner=True
        )
        db.session.add(owner)
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

@app.route('/admin/manage_admins')
@login_required
def manage_admins():
    if not current_user.is_owner:
        flash('Only owner can manage admins')
        return redirect(url_for('admin_dashboard'))
    admins = Admin.query.all()
    return render_template('admin/manage_admins.html', admins=admins)

@app.route('/admin/add_admin', methods=['GET', 'POST'])
@login_required
def add_admin():
    if not current_user.is_owner:
        flash('Only owner can add new admins')
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if Admin.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('add_admin'))

        admin = Admin(
            username=username,
            password_hash=generate_password_hash(password),
            is_owner=False
        )
        db.session.add(admin)
        db.session.commit()
        flash('Admin added successfully')
        return redirect(url_for('manage_admins'))

    return render_template('admin/add_admin.html')

@app.route('/admin/delete_admin/<int:admin_id>')
@login_required
def delete_admin(admin_id):
    if not current_user.is_owner:
        flash('Only owner can delete admins')
        return redirect(url_for('admin_dashboard'))

    admin = Admin.query.get_or_404(admin_id)
    if admin.is_owner:
        flash('Cannot delete owner account')
        return redirect(url_for('manage_admins'))

    db.session.delete(admin)
    db.session.commit()
    flash('Admin deleted successfully')
    return redirect(url_for('manage_admins'))

@app.route('/movie/<int:movie_id>/review', methods=['POST'])
def add_review(movie_id):
    movie = Movie.query.get_or_404(movie_id)

    reviewer_name = request.form.get('reviewer_name')
    rating = int(request.form.get('rating'))
    comment = request.form.get('comment')

    if not reviewer_name or not rating or rating < 1 or rating > 5:
        flash('Please provide your name and a valid rating')
        return redirect(url_for('movie_details', movie_id=movie_id))

    review = Review(
        reviewer_name=reviewer_name,
        rating=rating,
        comment=comment,
        movie_id=movie_id,
        created_at=datetime.utcnow()
    )

    db.session.add(review)
    db.session.commit()
    flash('Thank you for your review!')
    return redirect(url_for('movie_details', movie_id=movie_id))

@app.route('/movie/<int:movie_id>')
def movie_details(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    reviews = movie.reviews
    return render_template('movie_details.html', movie=movie, reviews=reviews)