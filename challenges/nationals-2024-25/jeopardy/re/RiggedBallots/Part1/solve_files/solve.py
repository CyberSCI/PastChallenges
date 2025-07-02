import base64
import binascii

with open('flag.txt', 'r') as file:
    FLAG = file.readlines()

flag_single = list(set(FLAG))

key = "Hail our leader and savior Esperanza"

for ballot in flag_single:
    ballot = ballot.strip()
    test = True
    while test == True:
        try:
            unencode = base64.b64decode(ballot)
            test = False
        except:
            ballot = ballot + '=='

    
    unencode = unencode.decode('utf-8').replace('0x','')
    split_uncode = unencode.split(" ")

    xor_result = ' '.join((hex(ord(chr(int(a, 16))) ^ ord(b))) for a, b in zip(split_uncode, key))
    split_hex = xor_result.split(" ")
    flag_text = ""
    for hexes in split_hex:
        hexes = hexes[2:]
        flag_text = flag_text + hexes
    
    print(flag_text)
