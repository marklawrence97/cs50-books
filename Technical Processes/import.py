import csv
import os
import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv('DATABASE_URL'))
db = scoped_session(sessionmaker(bind=engine))

def main():
    f = open('books.csv', 'r')
    reader = csv.reader(f)
    for isbn,title,author,year in reader:
        print(isbn,title,author,year)
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)", 
        {"isbn": isbn, "title": title, "author": author, "year": datetime.date(int(year),1,1)})
        print(f"Book with title {title} was inserted into the book table")
    db.commit()

if __name__ == "__main__":
    main()