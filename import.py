import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():

    # # WORKING!!
    # HAD TO CHANGE ALL TO VARCHAR
    # db.execute("CREATE TABLE books (isbn INTEGER PRIMARY KEY, title VARCHAR NOT NULL, author VARCHAR NOT NULL, year INTEGER NOT NULL)")

    f = open("bookssmall.csv")
    reader = csv.reader(f)
    for isbn, title, author, year in reader:							# loop gives each column a name
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)",
                    {"isbn": isbn, "title": title, "author": author, "year": year})	# substitute values from CSV line into SQL command, as per this dict

        print(f"Added [{title}] by {author} ({year}) ({isbn}).")

    db.commit()

if __name__ == "__main__":
    main()
