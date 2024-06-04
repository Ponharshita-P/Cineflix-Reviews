from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

##CREATE DB
class Base(DeclarativeBase):
    pass
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://default:CeT0gqBcrj5l@ep-solitary-star-a44bncmy.us-east-1.aws.neon.tech:5432/verceldb?sslmode=require'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


##CREATE TABLE
class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer, nullable=True)
    review: Mapped[str] = mapped_column(String(250), nullable=True)
    img_url: Mapped[str] = mapped_column(String(250), nullable=False)

with app.app_context():
    db.create_all()

class AddMovieForm(FlaskForm):
    title = StringField("Movie Title", validators=[DataRequired()])
    submit = SubmitField("Add Movie")

class RateMovieForm(FlaskForm):
    rating = StringField("Your Rating Out of 10 e.g. 7.5")
    review = StringField("Your Review")
    submit = SubmitField("Done")

# Example function to add a new movie
def add_new_movie():
    if not db.session.query(Movie).filter_by(title="Phone Booth").first():
        new_movie = Movie(
            title="Phone Booth",
            year=2002,
            description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
            rating=7.3,
            ranking=10,
            review="My favourite character was the caller.",
            img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
        )
        db.session.add(new_movie)
        db.session.commit()
    else:
        print("Movie already exists in the database.")

# Ensure the function is only called when necessary
with app.app_context():
    add_new_movie()


@app.route("/")
def home():
    result = db.session.execute(db.select(Movie).order_by(Movie.rating))
    all_movies = result.scalars().all()  # convert ScalarResult to Python List
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", all_movies=all_movies)

@app.route("/add",methods=["GET", "POST"])
def add():
    form = AddMovieForm()
    if form.validate_on_submit():
        movie_title = form.title.data
        url = "https://api.themoviedb.org/3/search/movie"
        api = "2a72b97ee7aee1b3a58218dde58bb661"
        response = requests.get(url, params={"api_key": api, "query": movie_title}).json()
        data = response["results"]
        return render_template("select.html", data=data)
    return render_template("add.html", form=form)


@app.route("/select/<int:id>")
def get_movie_details(id):
    if id:
        url = "https://api.themoviedb.org/3/movie/" + str(id)
        movie = requests.get(url,params={"api_key": "2a72b97ee7aee1b3a58218dde58bb661"}).json()
        base_url = "https://image.tmdb.org/t/p/w500"
        relative_url = movie['poster_path']
        image_url = base_url + relative_url
        title = movie['title']
        year = movie['release_date'][:4]
        description = movie['overview']
        #insert values
        new_movie = Movie(
            title=title,
            img_url=image_url,
            year=year,
            description=description)
        db.session.add(new_movie)
        db.session.commit()
        return redirect(url_for('edit', id = new_movie.id))



# Adding the Update functionality
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    form = RateMovieForm()
    movie = db.get_or_404(Movie, id)
    if form.validate_on_submit():
        #receive data from form
        movie.rating = float(form.rating.data)
        movie.review = form.review.data
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", movie=movie, form=form)

@app.route("/delete/<int:id>")
def delete(id):
    # DELETE A RECORD BY ID
    movie_to_delete = db.get_or_404(Movie, id)
    # Alternative way to select the book to delete.
    # movie_to_delete = db.session.execute(db.select(Movie).where(Movie.id == id)).scalar()
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True, port=5001)
