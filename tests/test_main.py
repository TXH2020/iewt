import unittest
import os
import sqlite3

def connect_db():
    try:
        con=sqlite3.connect("db.db")
        con.close()
    except sqlite3.OperationalError as e:
        return "string"

class TestDatabaseConnection(unittest.TestCase):
    def test_creation_priveleged(self):
        os.chdir('/home/osboxes/Desktop')
        if(os.path.exists('db.db')):
            os.remove('db.db')
        connect_db()
        self.assertEqual(os.path.exists('db.db'), True, "Unsuccessful")

    def test_creation_unpriveleged(self):
        os.chdir('/')
        if(os.path.exists('db.db')):
            os.remove('db.db')
        self.assertEqual(type(connect_db()), str, "Unsuccessful")

if __name__ == '__main__':
    unittest.main()
