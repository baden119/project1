import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():

    # # Create Databases
    # db.execute("CREATE TABLE books (isbn VARCHAR PRIMARY KEY, title VARCHAR NOT NULL, author VARCHAR NOT NULL, year INTEGER NOT NULL)")
    # db.execute("CREATE TABLE users (id SERIAL PRIMARY KEY, created TIMESTAMP NOT NULL, username VARCHAR NOT NULL, password VARCHAR NOT NULL)")
    # db.execute("CREATE TABLE reviews (id SERIAL PRIMARY KEY, submission_dt TIMESTAMP NOT NULL, rating INTEGER NOT NULL, review_text TEXT NOT NULL, reviewer_id INTEGER REFERENCES users, isbn VARCHAR REFERENCES books)")
    #
    # db.commit()


    f = open("books.csv")
    reader = csv.reader(f)
    next(f)                                      #Skip first line of file (column headers)
    for isbn, title, author, year in reader:							# loop gives each column a name

        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                    {"isbn": isbn, "title": title, "author": author, "year":int(year)})	# substitute values from CSV line into SQL command, as per this dict

        print(f"Added [{title}] by {author} ({year}) ({isbn}).")

    db.commit()

if __name__ == "__main__":
    main()
