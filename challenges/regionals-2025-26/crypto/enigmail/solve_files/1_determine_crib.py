import base64

def base16encode(data: bytes) -> str:
    chars = 'ABCDEFGHIJKLMNOP'
    encoded = ''
    for byte in data:
        high_nibble = (byte >> 4) & 0x0F
        low_nibble = byte & 0x0F
        encoded += chars[high_nibble] + chars[low_nibble]
    return encoded

with open('../server_files/output.txt') as f:
    CIPHERTEXT = f.read().strip()

with open('files/logo.png', 'rb') as f:
    CRIB = f.read()

CRIB = base64.b64encode(CRIB).decode()
CRIB = '\r\n'.join(CRIB[i:i+76] for i in range(0, len(CRIB), 76))
CRIB = base16encode(CRIB.encode())


# find all positions where the crib can fit without letter conflicts
def check_crib_at_position(message, crib, position):
    for i in range(len(crib)):
        if message[position + i] == crib[i]:
            return False
    return True

for i in range(len(CIPHERTEXT) - len(CRIB) + 1):
    if check_crib_at_position(CIPHERTEXT, CRIB, i):
        print(f'Crib can fit at position: {i}')
        
        partial_ciphertext = CIPHERTEXT[i:i+500]
        partial_plaintext = CRIB[:500]
        print('Partial CT:', partial_ciphertext)
        print('Partial PT:', partial_plaintext)