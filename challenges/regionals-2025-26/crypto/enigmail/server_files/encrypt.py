import base64
import random

# https://github.com/gremmie/enigma
# https://pypi.org/project/py-enigma/
from enigma.machine import EnigmaMachine


with open('files/email.eml', 'rb') as f:
    MESSAGE_BYTES = f.read()

with open('files/logo.png', 'rb') as f:
    LOGO_BYTES = f.read()


LOGO_BYTES_ENCODED = base64.b64encode(LOGO_BYTES).decode()
LOGO_BYTES_ENCODED = '\r\n'.join(LOGO_BYTES_ENCODED[i:i+76] for i in range(0, len(LOGO_BYTES_ENCODED), 76))
assert LOGO_BYTES_ENCODED.encode() in MESSAGE_BYTES


def base16encode(data: bytes) -> str:
    chars = 'ABCDEFGHIJKLMNOP'
    encoded = ''
    for byte in data:
        high_nibble = (byte >> 4) & 0x0F
        low_nibble = byte & 0x0F
        encoded += chars[high_nibble] + chars[low_nibble]
    return encoded

MESSAGE = base16encode(MESSAGE_BYTES)


ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'


def keygen():
    rotors = ['I', 'II', 'III', 'IV', 'V']
    random.shuffle(rotors)
    rotors = rotors[:3]

    reflector = 'B'
    
    ring_settings = [random.choice(ALPHABET) for _ in range(3)]
    
    plugboard_pairs = 10
    letters = list(ALPHABET)
    random.shuffle(letters)
    plugboard_settings = ' '.join(letters[i] + letters[i + 1] for i in range(0, plugboard_pairs * 2, 2))
    
    initial_positions = ''.join(random.choice(ALPHABET) for _ in range(3))
    
    key_sheet = {
        'rotors': ' '.join(rotors),
        'reflector': reflector,
        'ring_settings': ' '.join(ring_settings),
        'plugboard_settings': plugboard_settings
    }
    
    return key_sheet, initial_positions


key_sheet, initial_positions = keygen()

machine = EnigmaMachine.from_key_sheet(**key_sheet)
machine.set_display(initial_positions)

print('Machine:', key_sheet)
print('Initial Positions:', initial_positions)

ciphertext = machine.process_text(MESSAGE)
with open('output.txt', 'w') as f:
    f.write(ciphertext)