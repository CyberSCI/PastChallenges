import aes
import json
import string
from secret import FLAG, KEY, IV, REGISTRATION_TOKEN


KEY_SIZE = 16
TOKEN_SIZE = 32

assert len(KEY) == KEY_SIZE
assert len(IV) == KEY_SIZE
assert len(REGISTRATION_TOKEN) == TOKEN_SIZE
assert all(c in string.hexdigits for c in REGISTRATION_TOKEN)


def encrypt_input(input_payload, iv):
    input_payload = json.dumps(input_payload)
    input_payload_bytes = input_payload.encode()
    
    cipher = aes.AES(KEY)
    encrypted_input_bytes = cipher.encrypt_pcbc(input_payload_bytes, iv)
    encrypted_input_hex = encrypted_input_bytes.hex()
    
    return iv.hex() + encrypted_input_hex


def decrypt_input(encrypted_input_hex):
    encrypted_input_bytes = bytes.fromhex(encrypted_input_hex)
    
    iv = encrypted_input_bytes[:KEY_SIZE]
    encrypted_input_bytes = encrypted_input_bytes[KEY_SIZE:]
    
    cipher = aes.AES(KEY)
    decrypted_input_bytes = cipher.decrypt_pcbc(encrypted_input_bytes, iv)
    decrypted_input = decrypted_input_bytes.decode('ascii', errors='ignore')
    
    input_payload = json.loads(decrypted_input)
    
    return input_payload
    

def receive_input():
    encrypted_input_hex = input('Enter the encrypted input hex: ')
    
    try:
        input_payload = decrypt_input(encrypted_input_hex)
    except:
        return None
    
    return input_payload


REGISTERED_USERNAMES = []

def register_candidate(input_payload):
    username = input_payload.get('username')
    registration_token = input_payload.get('registration_token')
    
    if not username:
        return False, 'Username is required.'
    
    if not registration_token or registration_token != REGISTRATION_TOKEN:
        return False, 'Invalid registration token.'
    
    if username in REGISTERED_USERNAMES:
        return False, 'Username already registered.'
    
    REGISTERED_USERNAMES.append(username)
    
    return True, f'You are now registered as {username}.'


davey_jones_input = {
    'registration_token': REGISTRATION_TOKEN,
    'username': 'davey_jones',
    'bio': "Once in power, I shall bring Valverdian's fleet to its former glory!"
}
davey_jones_encrypted_input = encrypt_input(davey_jones_input, IV)


registered, message = register_candidate(davey_jones_input)
assert registered


print('=============================================')
print("You have intercepted Davey Jones' submission:")
print(davey_jones_encrypted_input)
print('=============================================')


print("""
Welcome to the Candidate Registry.

To register your candidate account and receive access to the portal,
submit your username, bio, and the registration token you received from the registrar.
""")

input_payload = receive_input()
print()

if not input_payload:
    print('Invalid input!')
    exit()

registered, message = register_candidate(input_payload)

print(message)
print()

if registered:
    print('Here is your password:', FLAG)