from itertools import product
from enigma.machine import EnigmaMachine


rotors = 'V IV I'
ring_settings_2_3 = 'H W'
reflector = 'B'
plugboard_settings = 'FH AN BJ CK EO GW IR MQ TZ SU'


ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
DECRYPTED_ALPHABET = 'ABCDEFGHIJKLMNOP'

with open('files/output.txt') as f:
    CIPHERTEXT = f.read().strip()

def base16decode(encoded: str) -> bytes:
    chars = 'ABCDEFGHIJKLMNOP'
    data = bytearray()
    for i in range(0, len(encoded), 2):
        high_nibble = chars.index(encoded[i])
        low_nibble = chars.index(encoded[i + 1])
        byte = (high_nibble << 4) | low_nibble
        data.append(byte)
    return bytes(data)

for ring_setting_1, init_pos_1, init_pos_2, init_pos_3 in product(ALPHABET, repeat=4):
    # Modify ring settings and initial positions
    ring_settings = f'{ring_setting_1} {ring_settings_2_3}'
    initial_positions = f'{init_pos_1}{init_pos_2}{init_pos_3}'
    
    # Decrypt with modified settings
    machine = EnigmaMachine.from_key_sheet(
        rotors=rotors,
        reflector=reflector,
        ring_settings=ring_settings,
        plugboard_settings=plugboard_settings
    )
    
    machine.set_display(initial_positions)
    
    # Decrypt only the beginning to check for valid characters (base-16)
    decrypted_text_encoded = machine.process_text(CIPHERTEXT[:100])
    if any(c not in DECRYPTED_ALPHABET for c in decrypted_text_encoded):
        continue
    
    # Decrypt the rest of the ciphertext and check for valid characters (base-16)
    decrypted_text_encoded += machine.process_text(CIPHERTEXT[100:])
    if any(c not in DECRYPTED_ALPHABET for c in decrypted_text_encoded):
        continue
    
    # Decode from base-16
    decrypted_text = base16decode(decrypted_text_encoded)

    # If yes, output decrypted contents
    print(f'Ring Settings: {ring_settings}, Initial Positions: {initial_positions}')
    with open('files/email.eml', 'wb') as f:
        f.write(decrypted_text)
    
    break