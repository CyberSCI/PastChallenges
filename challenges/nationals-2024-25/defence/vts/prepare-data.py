#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# CyberSci Nationals 2024/25
#
# Script to prepare database and check integrity of all data files by 0xd13a

import sqlite3
import traceback
import zlib

DB = "./vts.db"
VOTERS = "./voter-list.csv"
CANDIDATES = "./candidates.csv"
MACHINES = "./machine-ids.csv"
CLASHES = "./machine-id-clashes.csv"
BAD_VOTERS = "./bad-voter-list.csv"
BAD_MACHINES = "./bad-machine-ids.csv"


print("Checking machines...")

machines = []
crcs = []

with open(MACHINES, "r") as file:
    for line in file.readlines():
        id = line.strip()
        if id in machines:
            print("Machine already exists:", id)
        machines.append(id)
        crc = zlib.crc32(id.encode('ascii'))
        if crc in crcs:
            print("CRC already exists:", hex(crc), id)
        crcs.append(crc)


with open(BAD_MACHINES, "r") as file:
    for line in file.readlines():
        id = line.strip()
        if id in machines:
            print("Machine already exists:", id)
        machines.append(id)
        crc = zlib.crc32(id.encode('ascii'))
        if crc in crcs:
            print("CRC already exists:", hex(crc), id)
        crcs.append(crc)

with open(CLASHES, "r") as file:
    for line in file.readlines():
        crc, m1, m2 = line.strip().split(',')
        if m1 in machines:
            print("Machine already exists:", m1)
        machines.append(m1)
        if m2 in machines:
            print("Machine already exists:", m2)
        machines.append(m2)
        crc = int(crc, 16)
        if crc in crcs:
            print("CRC already exists:", hex(crc), m1, m2)
        if crc != zlib.crc32(m1.encode('ascii')):
            print("CRC does not match:", hex(crc), m1)
        if crc != zlib.crc32(m2.encode('ascii')):
            print("CRC does not match:", hex(crc), m2)
            
        crcs.append(crc)

print("Checking voters...")


voters = []
voter_ids = []

with open(VOTERS, "r") as file:
    for line in file.readlines():
        id,name = line.strip().split(',')
        if id in voter_ids:
            print("Voter ID already exists:", id)
        voter_ids.append(id)
        if name in voters:
            print("Voter already exists:", name)
        voters.append(name)

with open(BAD_VOTERS, "r") as file:
    for line in file.readlines():
        id,name = line.strip().split(',')
        if id in voter_ids:
            print("Voter ID already exists:", id)
        voter_ids.append(id)
        if name in voters:
            print("Voter already exists:", name)
        voters.append(name)


print("Building database...")


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
exec_sql("DROP TABLE IF EXISTS candidates;", [], True)
exec_sql("DROP TABLE IF EXISTS machines;", [], True)
exec_sql("CREATE TABLE voters (id INT, name VARCHAR(255));", [], True)
exec_sql("CREATE TABLE candidates (id INT, name VARCHAR(255), votes INT);", [], True)
exec_sql("CREATE TABLE machines (crc INT, id VARCHAR(255));", [], True)


with open(VOTERS,"r") as file:
    for line in file.readlines():
        id, name = line.strip().split(",")
        exec_sql("INSERT INTO voters (id, name) VALUES(?, ?);", [id, name], True)

machines = {}

with open(MACHINES,"r") as file:
    for line in file.readlines():
        id = line.strip()
        machines[id] = zlib.crc32(id.encode('ascii'))

with open(CLASHES,"r") as file:
    for line in file.readlines():
        crc, id, clash = line.strip().split(",")
        machines[id] = int(crc, 16)

for k in sorted(machines.keys()):
    exec_sql("INSERT INTO machines (crc, id) VALUES(?, ?);", [machines[k], k], True)

with open(CANDIDATES,"r") as file:
    for line in file.readlines():
        id, name = line.strip().split(",")
        exec_sql("INSERT INTO candidates (id, name, votes) VALUES(?, ?, ?);", [id, name, 0], True)
