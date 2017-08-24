#!/usr/bin/env python
"""Creates and adds article entries to database."""

import os
import sqlite3


class Article:
    """Stores article data."""
    def __init__(self, title, url, snippet):
        self.title = title
        self.url = url
        self.snippet = snippet

    def _tuple(self):
        return (self.title, self.url, self.snippet)

    def __str__(self):
        return self.title

    def __repr__(self):
        return self.title


class ArticleDB:
    """Stores articles in sqlite database."""
    DB_NAME = "Oski.db"
    TABLE_NAME = "Articles"

    def __init__(self):
        create_table = not os.path.exists(self.DB_NAME)

        self.connection = sqlite3.connect(self.DB_NAME)
        self.cursor = self.connection.cursor()
        if create_table:
            create_cmd = """CREATE TABLE %s (
                            title TEXT, 
                            url TEXT, 
                            snippet TEXT);""" % self.TABLE_NAME
            self.cursor.execute(create_cmd)
            self.connection.commit()

    def __del__(self):
        self.connection.close()

    def add_article(self, article):
        """Add article to database."""
        if self.in_database(article.title):  return False

        insert_cmd = """
            INSERT INTO %s (title, url, snippet) 
            VALUES (?, ?, ?)""" % self.TABLE_NAME
        self.cursor.execute(insert_cmd, article._tuple())
        self.connection.commit()
        return True

    def delete_article(self, title):
        """Delete article with matching title."""
        if self.in_database(title):
            delete_cmd = """DELETE FROM %s WHERE title = ?""" % self.TABLE_NAME
            self.cursor.execute(delete_cmd, (title, ))
            self.connection.commit()
            return True
        return False

    def get_article(self, title):
        """Return article matching input title."""
        select_cmd = """SELECT * FROM %s WHERE title = ?""" % self.TABLE_NAME
        self.cursor.execute(select_cmd, (title, ))
        results = self.cursor.fetchall()
        if len(results) > 0:
            return Article(*results[0])
        return None

    def get_articles(self):
        """Return all articles in database."""
        select_cmd = """SELECT * FROM %s""" % self.TABLE_NAME
        self.cursor.execute(select_cmd)
        results = self.cursor.fetchall()
        articles = [Article(*result) for result in results]
        return articles

    def in_database(self, title):
        """Check if a given article is already in the database."""
        search_cmd = """SELECT * FROM %s WHERE title = ?""" % self.TABLE_NAME
        self.cursor.execute(search_cmd, (title, ))
        results = self.cursor.fetchall()
        return len(results) > 0


def main():
    db = ArticleDB()
    return


if __name__ == "__main__":
    main()