#!/usr/bin/python3
# -*- coding: utf8 -*-
#

from faker import Faker
import random

voter_list = "./voter-list.txt"

input("This will generate user data, overwriting existing file. Press Enter to continue...")

fake = Faker("es")
random.seed(0)
Faker.seed(0)

voters = {}
while len(voters) < 1000:
    id = fake.ssn()
    voters[id] = ("{} {}".format(fake.first_name(), fake.last_name()), fake.date_between(start_date='-100y', end_date='-18y'), "{}, {}, {}".format(fake.street_address().strip(), fake.city(), fake.postcode()), 1 if random.randint(1,50) == 1 else 0)

with open(voter_list,"w") as file:
    for id in voters.keys():
        file.write("{}|{}|{}|{}|{}\n".format(id, voters[id][0], voters[id][1], voters[id][2], voters[id][3]))