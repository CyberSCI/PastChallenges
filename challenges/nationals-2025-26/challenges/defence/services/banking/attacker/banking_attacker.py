#!/usr/bin/env python3
#
# CyberSci Nationals 2025/26
#
# Dmitriy Beryoza (0xd13a)
#
# Attacker for Banking vulnerable service

import pwn  # type: ignore[import-untyped]
import re
import traceback
import random
from pathlib import Path
from enum import Enum

from siege.attacker.attacker import Attacker
from siege.core.attack_result import AttackResult

REQUEST_TIMEOUT = 4

UP = "\x1b[A"
DOWN = "\x1b[B"

ANSI_ESCAPE_RE = re.compile(
    r"""
    (?:\x1B\[|\x9B)        # CSI: ESC [ or 8-bit CSI
    [0-?]*                 # parameter bytes
    [ -/]*                 # intermediate bytes
    [@-~]                  # final byte

    |                      # or

    (?:\x1B\]|\x9D)        # OSC: ESC ] or 8-bit OSC
    .*?
    (?:\x07|\x1B\\|\x9C)   # BEL, ST, or 8-bit ST terminator

    |                      # or

    (?:\x1B[P^_X]|\x90|\x9E|\x9F|\x98)  # DCS, PM, APC, SOS
    .*?
    (?:\x1B\\|\x9C)        # ST terminator

    |                      # or

    \x1B[\x20-\x2F]*[\x30-\x7E]  # other ESC sequences
    """,
    re.VERBOSE | re.DOTALL,
)

class Result(Enum):
    EXPECTED: int = 0
    UNEXPECTED: int = 1
    BROKEN: int = 2

class BankingAttacker(Attacker):

    good_accounts: dict[int, int] = {}
    bad_accounts: dict[int, int] = {}
    good_payees: list[int] = []
    bad_payees: list[int] = []

    def load_accounts(self):
        min_acct: int = 0
        max_acct: int = 0
        with open(Path(__file__).parent / "accounts.csv", "r") as file:
            for line in file.readlines():
                account, pin, _, _, _ = line.strip().split(",")
                acct = int(account)
                self.good_accounts[acct] = int(pin)
                if min_acct > acct or min_acct == 0:
                    min_acct = acct
                if max_acct < acct:
                    max_acct = acct

        while len(self.bad_accounts) < 1000:
            val = random.randint(min_acct + 1, max_acct - 1)
            if val not in self.good_accounts.keys() and \
                val not in self.bad_accounts:
                self.bad_accounts[val] = random.randint(0,9999)

    def load_payees(self):
        min_payee: int = 0
        max_payee: int = 0
        with open(Path(__file__).parent / "payees.csv", "r") as file:
            for line in file.readlines():
                payee, _ = line.strip().split(",")
                payee_no = int(payee)
                self.good_payees.append(payee_no)
                if min_payee > payee_no or min_payee == 0:
                    min_payee = payee_no
                if max_payee < payee_no:
                    max_payee = payee_no

        while len(self.bad_payees) < 1000:
            val = random.randint(min_payee + 1, max_payee - 1)
            if val not in self.good_payees and \
                val not in self.bad_payees:
                self.bad_payees.append(val)

    def strip_ansi(self, text: str) -> str:
        """Return *text* with ANSI/VT terminal escape sequences removed."""
        return ANSI_ESCAPE_RE.sub("", text)

    def __init__(self, host, port):
        super().__init__(host, port)
        
        try:
            self.load_accounts()
            self.load_payees()
        except BaseException:
            traceback.print_exc()

    def log(self, str):
        print(f"BankingAttacker - {str}")

    def drain(self, r):
        output = r.clean(timeout=1)
        return output

    def connect(self):
        return pwn.remote(self.host, self.port, timeout=REQUEST_TIMEOUT,
                          level='critical', ssl=True)

    def talk(self, r, str):
        r.sendline(str.encode())
        output = self.strip_ansi(self.drain(r).decode())

        return output

    def parse_balances(self, str):

        match = re.search(r"Checking: \$([\d.,]+)", str)
        checking = float(re.sub(",", "", match.group(1))) if match else None

        match = re.search(r"Savings : \$([\d.,]+)", str)
        savings = float(re.sub(",", "", match.group(1))) if match else None

        return checking, savings
    
    def random_dollars(self, val):
        return random.uniform(0.01, val-0.01)
    
    def random_acct_type(self):
        return random.choice(["c", "s"])
    
    def random_acct_amount(self, checking, savings):

        acct = self.random_acct_type()

        if acct == "c":
            amount = self.random_dollars(checking)
        else:
            amount = self.random_dollars(savings)

        return acct, amount

    def transaction_correct(self, acct, checking, savings,checking_after, savings_after, delta):
        if acct == "c":
            if f"{checking + delta:.2f}" == f"{checking_after:.2f}":
                return True
        else:
            if f"{savings + delta:.2f}" == f"{savings_after:.2f}":
                return True
        return False

    ##########################################################

    def process_deposit(self, benign) -> Result:
        r = self.connect()

        try: 
            user = random.choice(list(self.good_accounts))
            pin = self.good_accounts[user]

            self.log(f"User {user}:{pin}")
            output = self.talk(r,f"{user}\x0a{pin}\x0a")

            checking, savings = self.parse_balances(output)
            self.log(f"Balances: {checking:.2f} {savings:.2f}")
            if checking is None or savings is None:
                return Result.BROKEN

            if "Account (C=checking, S=savings)" not in output:
                return Result.BROKEN

            acct = self.random_acct_type()
            amount = self.random_dollars(10000)

            self.log(f"Account: {acct}")
            output = self.talk(r,f"{acct}")
            if "Amount (dollars)" not in output:
                return Result.BROKEN

            self.log(f"Amount: {amount:.2f}")
            output = self.talk(r,f"{amount:.2f}")

            if "Insert the money and enter C to continue or E to exit [C/E]:" not in output:
                return Result.BROKEN

            if benign:
                output = self.talk(r,'c')

                checking_after, savings_after = self.parse_balances(output)
                self.log(f"Balances after: {checking_after:.2f} {savings_after:.2f}")

                if not self.transaction_correct(acct, checking, savings, checking_after, savings_after, amount):
                    return Result.UNEXPECTED

                if "Deposit complete." in output:
                    return Result.EXPECTED
                return Result.UNEXPECTED
            else:                
                output = self.talk(r,'e')

                checking_after, savings_after = self.parse_balances(output)
                self.log(f"Balances after: {checking_after:.2f} {savings_after:.2f}")

                if checking != checking_after or savings != savings_after:
                    return Result.EXPECTED
                return Result.UNEXPECTED

        finally:
            r.close()

    ##########################################################

    def process_withdrawal(self, benign):
        r = self.connect()

        try: 
            user = random.choice(list(self.good_accounts))
            pin = self.good_accounts[user]

            self.log(f"User {user}:{pin}")
            output = self.talk(r,f"{user}\x0a{pin}\x0a{DOWN}")

            checking, savings = self.parse_balances(output)
            self.log(f"Balances: {checking:.2f} {savings:.2f}")
            if checking is None or savings is None:
                return Result.BROKEN

            if "Account (C=checking, S=savings)" not in output:
                return Result.BROKEN

            if benign:
                acct, amount = self.random_acct_amount(checking, savings)
            else:
                acct = self.random_acct_type()
                amount = -self.random_dollars(10000)

            self.log(f"Account: {acct}")
            output = self.talk(r,f"{acct}")
            if "Amount (dollars)" not in output:
                return Result.BROKEN

            self.log(f"Amount: {amount:.2f}")
            output = self.talk(r,f"{amount:.2f}")

            checking_after, savings_after = self.parse_balances(output)
            self.log(f"Balances after: {checking_after or 0:.2f} {savings_after or 0:.2f}")

            if benign:
                if not self.transaction_correct(acct, checking, savings, checking_after, savings_after, -amount):
                    return Result.UNEXPECTED

                if "Please take your cash." in output:
                    return Result.EXPECTED
                return Result.UNEXPECTED
            else:
                if "Please take your cash." in output:
                    return Result.EXPECTED
                return Result.UNEXPECTED
    
        finally:
            r.close()

    ##########################################################

    def process_transfer(self, benign):
        r = self.connect()

        try: 
            user = random.choice(list(self.good_accounts))
            pin = self.good_accounts[user]

            self.log(f"User {user}:{pin}")
            output = self.talk(r,f"{user}\x0a{pin}\x0a{DOWN*2}")

            checking, savings = self.parse_balances(output)
            self.log(f"Balances: {checking:.2f} {savings:.2f}")
            if checking is None or savings is None:
                return Result.BROKEN

            if "Account (C=checking, S=savings)" not in output:
                return Result.BROKEN

            acct, amount = self.random_acct_amount(checking, savings)

            self.log(f"Account: {acct}")
            output = self.talk(r,f"{acct}")
            if "Amount (dollars)" not in output:
                return Result.BROKEN

            if not benign:
                if acct == "c":
                    amount = checking
                else:
                    amount = savings
                amount = random.uniform(amount+0.01, amount+10000)

            self.log(f"Amount: {amount:.2f}")
            output = self.talk(r,f"{amount:.2f}")

            checking_after, savings_after = self.parse_balances(output)
            self.log(f"Balances after: {checking_after or 0:.2f} {savings_after or 0:.2f}")

            if benign:
                if acct == "c":
                    if f"{checking - amount:.2f}" != f"{checking_after:.2f}" or \
                       f"{savings + amount:.2f}" != f"{savings_after:.2f}":
                        return Result.UNEXPECTED
                else:
                    if f"{savings - amount:.2f}" != f"{savings_after:.2f}" or \
                       f"{checking + amount:.2f}" != f"{checking_after:.2f}":
                        return Result.UNEXPECTED

                if "Transfer complete." in output:
                    return Result.EXPECTED
                return Result.UNEXPECTED
            else: 
                if "Transfer complete." in output:
                    return Result.EXPECTED
                return Result.UNEXPECTED

        finally:
            r.close()

    ##########################################################

    def process_send(self, benign):
        r = self.connect()

        try: 
            user = random.choice(list(self.good_accounts))
            pin = self.good_accounts[user]

            self.log(f"User {user}:{pin}")
            output = self.talk(r,f"{user}\x0a{pin}\x0a{DOWN*3}")

            checking, savings = self.parse_balances(output)
            self.log(f"Balances: {checking:.2f} {savings:.2f}")
            if checking is None or savings is None:
                return Result.BROKEN

            if "Account (C=checking, S=savings)" not in output:
                return Result.BROKEN

            acct = self.random_acct_type()

            self.log(f"Account: {acct}")
            output = self.talk(r,f"{acct}")
            if "Destination card:" not in output:
                return Result.BROKEN

            card = ""
            while True:
                card = random.choice(list(self.good_accounts))
                if card != user:
                    break
            self.log(f"Card: {card}")
            output = self.talk(r,f"{card}")
            if "Account (C=checking, S=savings)" not in output:
                return Result.BROKEN

            dest_acct = self.random_acct_type()
            self.log(f"Dest account: {dest_acct}")
            output = self.talk(r,f"{dest_acct}")
            if "Amount (dollars)" not in output:
                return Result.BROKEN

            if benign:
                amount = self.random_dollars(9999.99)
            else: 
                if acct == "c":
                    amount = checking
                else:
                    amount = savings

                amount = random.uniform(10000.01, amount-0.01)

            self.log(f"Amount: {amount:.2f}")
            output = self.talk(r,f"{amount:.2f}")

            checking_after, savings_after = self.parse_balances(output)
            self.log(f"Balances after: {checking_after:.2f} {savings_after:.2f}")

            math_correct = self.transaction_correct(acct, checking, savings, checking_after, savings_after, -amount)
            
            if benign:
                if not math_correct:
                    return Result.UNEXPECTED
                if "Send money complete." in output:
                    return Result.EXPECTED
                return Result.UNEXPECTED
            else:
                if math_correct:
                    return Result.UNEXPECTED
                return Result.EXPECTED

        finally:
            r.close()

    ##########################################################

    def process_pay(self, benign, payees):
        r = self.connect()

        try: 
            user = random.choice(list(self.good_accounts))
            pin = self.good_accounts[user]

            self.log(f"User {user}:{pin}")
            output = self.talk(r,f"{user}\x0a{pin}\x0a{DOWN*4}")

            checking, savings = self.parse_balances(output)
            self.log(f"Balances: {checking:.2f} {savings:.2f}")
            if checking is None or savings is None:
                return Result.BROKEN

            payee = random.choice(payees)
            self.log(f"Payee: {payee}")
            output = self.talk(r,f"{payee}")
            if "Account (C=checking, S=savings)" not in output:
                if benign:
                    return Result.BROKEN
                else:
                    return Result.UNEXPECTED

            acct, amount = self.random_acct_amount(checking, savings)

            self.log(f"Account: {acct}")
            output = self.talk(r,f"{acct}")
            if "Amount (dollars)" not in output:
                return Result.BROKEN

            self.log(f"Amount: {amount:.2f}")
            output = self.talk(r,f"{amount:.2f}")

            checking_after, savings_after = self.parse_balances(output)
            self.log(f"Balances after: {checking_after:.2f} {savings_after:.2f}")

            if benign:
                if not self.transaction_correct(acct, checking, savings, checking_after, savings_after, -amount):
                    return Result.UNEXPECTED
                
                if "Bill payment complete." in output:
                    return Result.EXPECTED
                return Result.UNEXPECTED
            else:
                if "Bill payment complete." in output:
                    return Result.EXPECTED
                return Result.UNEXPECTED
    
        finally:
            r.close()

    ##########################################################

    def benign_request(self, id, tick, sequence_no):
        try:
            if id == 1:
                res = self.process_deposit(True)
            elif id == 2:
                res = self.process_withdrawal(True)
            elif id == 3:
                res = self.process_transfer(True)
            elif id == 4:
                res = self.process_send(True)
            elif id == 5:
                res = self.process_pay(True, self.good_payees)
        
            if res == Result.EXPECTED:
                return AttackResult.RESULT_SUCCESS
            else:
                return AttackResult.RESULT_FAILURE
        except BaseException:
            traceback.print_exc()
            return AttackResult.RESULT_DOWN
        raise Exception(f"Unknown request type '{id}'")

    def malicious_request(self, id, tick, sequence_no):
        try:
            if id == 1:
                res = self.process_deposit(False)
            elif id == 2:
                res = self.process_withdrawal(False)
            elif id == 3:
                res = self.process_transfer(False)
            elif id == 4:
                res = self.process_send(False)
            elif id == 5:
                res = self.process_pay(False, self.bad_payees)

            if res in [Result.EXPECTED, Result.BROKEN]:
                return AttackResult.RESULT_SUCCESS
            else:
                return AttackResult.RESULT_FAILURE
        except BaseException:
            traceback.print_exc()
            return AttackResult.RESULT_DOWN
        raise Exception(f"Unknown request type '{id}'")
