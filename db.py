import sqlite3
from os import path, getcwd

ROOT = path.dirname(path.realpath(__file__))
db = path.join(ROOT, "database.db")
# db = path.join(getcwd(), 'database.db')

class Database:

    def __init__(self):
        self.connection = sqlite3.connect(db, check_same_thread=False)

    def query(self, q, arg=()):
        cursor = self.connection.cursor()

        cursor.execute(q, arg)
        results = cursor.fetchall()
        cursor.close()

        return results

    def insert(self, q, arg=()):
        cursor = self.connection.cursor()

        cursor.execute(q, arg)

        self.connection.commit()
        result = cursor.lastrowid
        cursor.close()
        return result

    def select(self, q, arg=()):
        cursor = self.connection.cursor()

        return cursor.execute(q, arg)

    def delete(self, q, arg=()):
        cursor = self.connection.cursor()
        result = cursor.execute(q, arg)
        self.connection.commit()
        return result
