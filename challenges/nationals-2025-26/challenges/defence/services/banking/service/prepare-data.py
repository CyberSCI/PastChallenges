#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# CyberSci Nationals 2025/26
#
# Script to prepare datasets for the Banking service

from faker import Faker
import random

input("This will generate data files, overwriting existing files. Press Enter to continue...")

fake = Faker()
random.seed(0)
Faker.seed(0)

print("Generating account list...")


account_numbers = set()

while len(account_numbers) < 1000:
	account_numbers.add(random.randint(13814601,13944590))

with open("accounts.csv","w") as file:
	for acct in account_numbers:
		file.write("{},{},{} {},{}.{:02d},{}.{:02d}\n".format(acct, random.randint(1000,9999),
										fake.first_name(), fake.last_name(), 
									   random.randint(10000,100000),random.randint(0,99),
									   random.randint(10000,100000),random.randint(0,99)))

print("Generating payee list...")

payee_numbers = set()
while len(payee_numbers) < 1000:
	payee_numbers.add(random.randint(6271632,6297801))

with open("payees.csv","w") as file:
	for payee in payee_numbers:
		name = ""
		while True:
			name = fake.company()
			if "," not in name:
				break
		file.write("{},{}\n".format(payee, name))
