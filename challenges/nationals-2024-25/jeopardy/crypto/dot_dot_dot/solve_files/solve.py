FLAG_ENCODED = '-.-.-.---.....-....-.-....--....----...-.........--..--.-......--.....-.-.-----..-.....-...-..--..-.-----..-..-----..-....'

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

with open('words.txt', 'r') as f:
    WORDS = [x for x in f.read().strip().splitlines()]

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

# Encode each word
WORDS_ENCODED = [(encode(word), word) for word in WORDS]

# Read known start of the decoded string
decoded = input('Enter the start of the decoded string (or nothing): ')

# Check if the start is valid
encoded = FLAG_ENCODED
encoded_start = encode(decoded)
if not encoded.startswith(encoded_start):
    print('Invalid start')
    exit(1)

# Remove the start from the encoded string
encoded = encoded.removeprefix(encoded_start)

# Iteratively decode
while encoded:
    print('Decoded:', decoded)
    print('Remaining:', encoded)
    
    # Compute options
    options = []
    for word_encoded, word in WORDS_ENCODED:
        if encoded.startswith(word_encoded):
            options.append(word)
    
    # Order options by length
    options = sorted(options, key=len, reverse=True)
    
    # Display options
    print('Options:')
    for i, option in enumerate(options):
        print(f'{i + 1}.\t{option}')
    
    # Get user choice
    choice = int(input('Select option: '))
    
    # Add to decoded string
    if decoded:
        decoded += ' ' + options[choice - 1]
    else:
        decoded = options[choice - 1]
    
    # Remove from encoded string
    encoded = encoded.removeprefix(encode(options[choice - 1]))

print('Decoded:', decoded)