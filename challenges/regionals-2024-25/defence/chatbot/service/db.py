import sqlite3 as sql
import os

def connect_db():
    db = sql.connect("election.db")
    return db

def create_user(username, password, candidate, phone, email, platform):
    try:
        db = connect_db()
        c = db.cursor()
        c.execute("INSERT INTO users (username, password, candidate, phone, email) VALUES (?, ?, ?, ?, ?)", (username, password, candidate, phone, email))
        if candidate:
            c.execute("INSERT INTO platform (username, description) VALUES (?, ?)", (username, platform))

        db.commit()
    finally:
        db.close()

def get_user(username, password):
    try:
        db = connect_db()
        c = db.cursor()
        c.execute("SELECT * FROM users WHERE username=? and password=?", (username, password))
        return c.fetchone()
    finally:
        db.close()

def check_user(username):
    try:
        db = connect_db()
        c = db.cursor()
        c.execute("SELECT * FROM users WHERE username=?", (username,))
        return c.fetchone()
    finally:
        db.close()

def get_platform(username):
    try:
        db = connect_db()
        c = db.cursor()
        c.execute("SELECT * FROM platform WHERE username=?", (username,))
        return c.fetchone()
    finally:
        db.close()

def update_platform(username, platform):
    try:
        db = connect_db()
        c = db.cursor()
        c.execute("UPDATE platform SET description=? WHERE username=?", (platform, username))
        db.commit()
    finally:
        db.close()

def list_candidates():
    try:
        db = connect_db()
        c = db.cursor()
        c.execute("SELECT * FROM users WHERE candidate='true'")
        return c.fetchall()
    finally:
        db.close()

# Check if database exists
if not os.path.exists("election.db"):
    try:
        print("Connecting to database...")
        db = connect_db()
        print("Connected to database")
        print("DB initialization...")
        c = db.cursor()
        # Create a users table
        c.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password TEXT, candidate BOOL, phone TEXT, email TEXT)")
        # Create a platform table
        c.execute("CREATE TABLE platform (id INTEGER PRIMARY KEY, username TEXT, description TEXT)")
        print("DB initialization complete")
    finally:
        db.close()