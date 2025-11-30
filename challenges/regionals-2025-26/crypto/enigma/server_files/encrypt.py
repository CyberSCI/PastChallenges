import random

# https://github.com/gremmie/enigma
# https://pypi.org/project/py-enigma/
from enigma.machine import EnigmaMachine
from secret import MESSAGE


ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'

REPLACEMENTS = {
    ' ': 'X',
    '0': 'ZERO',
    '1': 'ONE',
    '2': 'TWO',
    '3': 'THREE',
    '4': 'FOUR',
    '5': 'FIVE',
    '6': 'SIX',
    '7': 'SEVEN',
    '8': 'EIGHT',
    '9': 'NINE'
}

assert MESSAGE.startswith('CYBERSCI 2026')

for k, v in REPLACEMENTS.items():
    MESSAGE = MESSAGE.replace(k, v)

assert all(c in ALPHABET for c in MESSAGE)


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

ciphertext = machine.process_text(MESSAGE)

print(ciphertext)

print('Machine:', key_sheet)
print('Initial Positions:', initial_positions)

print('PT:', MESSAGE)
print('CT:', ciphertext)
