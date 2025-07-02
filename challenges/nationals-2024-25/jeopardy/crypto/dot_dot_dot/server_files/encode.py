FLAG = 'cybersci who needs spaces when you have competitors'

MORSE_TABLE = [
    ('a', '.-'),
    ('b', '-...'),
    ('c', '-.-.'),
    ('d', '-..'),
    ('e', '.'),
    ('f', '..-.'),
    ('g', '--.'),
    ('h', '....'),
    ('i', '..'),
    ('j', '.---'),
    ('k', '-.-'),
    ('l', '.-..'),
    ('m', '--'),
    ('n', '-.'),
    ('o', '---'),
    ('p', '.--.'),
    ('q', '--.-'),
    ('r', '.-.'),
    ('s', '...'),
    ('t', '-'),
    ('u', '..-'),
    ('v', '...-'),
    ('w', '.--'),
    ('x', '-..-'),
    ('y', '-.--'),
    ('z', '--..')
]

MORSE_TABLE_DICT = dict(MORSE_TABLE)

def encode(text):
    # Remove spaces
    text = text.replace(' ', '')
    
    # Convert to lowercase
    text = text.lower()
    
    # Encode each character
    encoded = [MORSE_TABLE_DICT[c] for c in text]
    
    # Join the encoded characters
    encoded = ''.join(encoded)
    
    return encoded

# Encode flag
encoded = encode(FLAG)
print(encoded)