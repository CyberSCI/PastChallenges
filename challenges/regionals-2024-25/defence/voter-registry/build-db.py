#!/usr/bin/python3
# -*- coding: utf8 -*-
#

from faker import Faker
import sqlite3
import traceback

DB = "./voter-list.db"
LIST = "./voter-list.txt"

def exec_sql(query, param=[], update=False):
    con = None
    cur = None
    rows = []
    try:
        con = sqlite3.connect(DB)
        cur = con.cursor()
        for row in cur.execute(query, param):
            rows.append(row)
        if update:
            con.commit()
    except Exception as e:
        print(e)
        traceback.print_exc()
    finally:
        if cur != None:
            cur.close()
        if con != None:
            con.close()
    return rows

exec_sql("DROP TABLE IF EXISTS voters;", [], True)

exec_sql("CREATE TABLE voters (id VARCHAR(50), name VARCHAR(255), dob VARCHAR(255), address VARCHAR(255), admin INT);", [], True)

with open(LIST,"r") as file:
    for line in file.readlines():
        id, name, dob, address, admin = line.strip().split("|")
        exec_sql("INSERT INTO voters (id, name, dob, address, admin) VALUES(?, ?, ?, ?, ?);", [id, name, dob, address, admin], True)
