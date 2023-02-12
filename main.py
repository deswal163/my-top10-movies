import requests
from flask import Flask, render_template, redirect
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, validators, SubmitField, IntegerField
from sqlalchemy import desc


app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)
app.app_context().push()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/movies_database.db'
db = SQLAlchemy(app)


class AddMovie(FlaskForm):
    movie_title = StringField("Movie Title", validators=[validators.data_required()])
    submit = SubmitField("Add Movie")


class EditForm(FlaskForm):
    new_rating = IntegerField("Your rating out of 10 e.g. 7.5",
                              validators=[validators.NumberRange(0, 10), validators.Optional()])
    new_review = StringField("Your Review", validators=[validators.Optional()])
    submit = SubmitField("Done")


class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String, nullable=True)
    rating = db.Column(db.Integer, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String)
    img_url = db.Column(db.String, nullable=True, unique=True)


db.create_all()
api_key = "4aafa951a3546d49324c366949dfe4d3"


def get_movies(movie):
    response = requests.get("https://api.themoviedb.org/3/search/movie", {
        "api_key": api_key,
        "query": movie
    }).json()
    return response["results"]


def requested_movie(movie_id):
    response = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}", {
        "api_key": api_key,
    }).json()

    return response


def create_order():
    movies = Movie.query.order_by(desc(Movie.rating))
    count = 1
    for i in movies:
        i.ranking = count
        count += 1
    db.session.commit()
    return Movie.query.order_by(desc(Movie.rating))


@app.route("/")
def home():
    movies = create_order()
    return render_template("index.html", movies=movies)


@app.route("/edit/<movie_id>", methods=["POST", "GET"])
def edit_review(movie_id):
    form = EditForm()

    movie = Movie.query.filter_by(id=movie_id).first()
    if form.validate_on_submit():
        new_rating = form.new_rating.data
        new_review = form.new_review.data
        movie.rating = new_rating if new_rating or new_rating == 0 else movie.rating
        movie.review = new_review if new_review else movie.review
        db.session.commit()
        return redirect('/')

    return render_template("edit.html", form=form, movie=movie)


@app.route('/delete/<movie_id>')
def delete_movie(movie_id):
    movie = Movie.query.filter_by(id=movie_id).first()
    db.session.delete(movie)
    db.session.commit()
    return redirect("/")


@app.route("/add", methods=['POST', 'GET'])
def add_movie():
    form = AddMovie()

    if form.validate_on_submit():
        movies = get_movies(form.movie_title.data)
        return render_template("select.html", movies=movies)

    return render_template("add.html", form=form)


@app.route("/add/<movie_id>")
def add_a_movie(movie_id):
    movie_response = requested_movie(movie_id)
    new_movie = Movie(
        title=movie_response["title"],
        year=int(movie_response["release_date"][0: 4]),
        description=movie_response["overview"],
        rating=0,
        ranking=0,
        review="none",
        img_url=movie_response["poster_path"]
    )
    db.session.add(new_movie)
    db.session.commit()
    return redirect(f'/edit/{Movie.query.filter_by(title=movie_response["title"]).first().id}')


if __name__ == '__main__':
    app.run(debug=True)
