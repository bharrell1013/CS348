import datetime, os
import sys
from sys import stderr
from flask import Flask, render_template, request, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from dotenv import load_dotenv
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] =\
        'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG')

db = SQLAlchemy(app)
app.secret_key = 'secret'

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

class Genre(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    movies = db.relationship('Movie', backref='genre', lazy=True)
    directors = db.relationship('Director', secondary='movie', lazy='dynamic')

class Director(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    movies = db.relationship('Movie', backref='director', lazy=True)
    directed_genres = db.relationship('Genre', secondary='movie', lazy='dynamic')

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False, unique=True)
    release_year = db.Column(db.Integer, nullable=False)
    genre_id = db.Column(db.Integer, db.ForeignKey('genre.id'), nullable=False)
    director_id = db.Column(db.Integer, db.ForeignKey('director.id'), nullable=False)
    __table_args__ = (
        db.Index('ix_movie_genre_id_director_id', 'genre_id', 'director_id'),
    )


@app.route('/')
def index():
    sort_by = request.args.get('sort_by', None)
    if sort_by == 'release_date':
        # Using prepared SQL statement
        sql_query = text("SELECT movie.*, genre.name AS genre_name, director.name AS director_name FROM movie LEFT JOIN genre ON movie.genre_id = genre.id LEFT JOIN director ON movie.director_id = director.id ORDER BY movie.release_year DESC")
        result = [Movie(id=row.id, title=row.title, release_year=row.release_year, genre=Genre(name=row.genre_name), director=Director(name=row.director_name)) for row in db.session.execute(sql_query).fetchall()]
    elif sort_by == 'director':
        # Using prepared SQL statement with JOIN
        sql_query = text("""
            SELECT movie.*, director.name AS director_name, genre.name AS genre_name FROM movie
            LEFT JOIN director ON movie.director_id = director.id
            LEFT JOIN genre ON movie.genre_id = genre.id
            ORDER BY director_name
        """)
        result = [Movie(id=row.id, title=row.title, release_year=row.release_year, genre=Genre(name=row.genre_name), director=Director(name=row.director_name)) for row in db.session.execute(sql_query).fetchall()]
    elif sort_by == 'genre':
        # Using prepared SQL statement with JOIN
        sql_query = text("""
            SELECT movie.*, genre.name AS genre_name, director.name AS director_name FROM movie
            LEFT JOIN genre ON movie.genre_id = genre.id
            LEFT JOIN director ON movie.director_id = director.id
            ORDER BY genre_name
        """)
        result = [Movie(id=row.id, title=row.title, release_year=row.release_year, genre=Genre(name=row.genre_name), director=Director(name=row.director_name)) for row in db.session.execute(sql_query).fetchall()]
    else:
        # Using ORM query
        movies = Movie.query.all()
        return render_template('index.html', movies=movies, sort_by=None)
    
    return render_template('index.html', movies=result, sort_by=sort_by)

@app.route('/<int:movie_id>/')
def movie(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    return render_template('movie.html', movie=movie)

@app.route('/genres/')
def genres():
    genres = Genre.query.all()
    return render_template('genres.html', genres=genres)

@app.route('/genres/<int:genre_id>/')
def genre(genre_id):
    genre = Genre.query.get_or_404(genre_id)
    directors = genre.directors.all()
    return render_template('genre.html', genre=genre, directors=directors)

@app.route('/directors/')
def directors():
    directors = Director.query.all()
    return render_template('directors.html', directors=directors)

@app.route('/director/<int:director_id>/')
def director(director_id):
    director = Director.query.get_or_404(director_id)
    genres = director.directed_genres.all()
    return render_template('director.html', director=director, genres=genres)


@app.route('/create/')
def create():
    return render_template('create.html')

@app.route('/create/movie', methods=['GET', 'POST'])
def create_movie():
    if request.method == 'POST':
        title = request.form['title']
        release_year = request.form['release_year']
        genre_id = request.form['genre_id']
        director_id = request.form['director_id']
        
        movie = Movie(title=title, release_year=release_year, genre_id=genre_id, director_id=director_id)
        db.session.add(movie)
        db.session.commit()
        
        return redirect(url_for('index'))
    
    genres = Genre.query.all()
    directors = Director.query.all()
    return render_template('create_movie.html', genres=genres, directors=directors)

@app.route('/create/genre', methods=['GET', 'POST'])
def create_genre():
    if request.method == 'POST':
        name = request.form['name']
        
        genre = Genre(name=name)
        db.session.add(genre)
        db.session.commit()
        
        return redirect(url_for('genres'))
    
    return render_template('create_genre.html')

@app.route('/create/director', methods=['GET', 'POST'])
def create_director():
    if request.method == 'POST':
        name = request.form['name']
        
        director = Director(name=name)
        db.session.add(director)
        db.session.commit()
        
        return redirect(url_for('directors'))
    
    return render_template('create_director.html')

@app.route('/<int:movie_id>/edit/', methods=['GET', 'POST'])
def edit(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    if request.method == 'POST':
        title = request.form['title']
        release_year = request.form['release_year']
        genre_id = request.form['genre_id']
        director_id = request.form['director_id']
        
        movie.title = title
        movie.release_year = release_year
        movie.genre_id = genre_id
        movie.director_id = director_id
        
        db.session.commit()
        
        return redirect(url_for('index'))
    genres = Genre.query.all()
    directors = Director.query.all()
    return render_template('edit.html', movie=movie, genres=genres, directors=directors)

@app.post('/<int:movie_id>/delete/')
def delete(movie_id):
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('index'))

@app.post('/<int:genre_id>/delete/genre')
def delete_genre(genre_id):
    genre = Genre.query.get_or_404(genre_id)
    if genre.movies:
        # If there are, do not allow the deletion
        flash('Cannot delete genre because it has associated movies', 'error')
        return redirect(url_for('genres'))
    db.session.delete(genre)
    db.session.commit()
    return redirect(url_for('genres'))

@app.post('/<int:director_id>/delete/director')
def delete_director(director_id):
    director = Director.query.get_or_404(director_id)
    if director.movies:
        # If there are, do not allow the deletion
        flash('Cannot delete director because it has associated movies', 'error')
        return redirect(url_for('directors'))
    db.session.delete(director)
    db.session.commit()
    return redirect(url_for('directors'))

@app.route('/about/')
def about():
    return render_template('about.html')


