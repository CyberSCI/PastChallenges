from pwn import *


"""
EXPLANATION

After looking up PCBC, we can find a weakness is that two cipher blocks can be swapped without affecting any other plaintext blocks.

We can infer that Davey Jones decrypted input looks like this:
{"registration_token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", "username": "davey_jones", "bio": "Once in power, I shall bring Valverdian's fleet to its former glory!"}
Swapping two blocks can result in the following decrypted output:
{"registration_token": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx", "username": "davey_jo********************************hall bring Valverdian's fleet to its former glory!"}

The asterisk (*) above represents the unknown characters as a result of the block swap.
The blocks to swap are from indexes 80 to 96 and 96 to 112. In hex these indexes are doubled.
"""


conn = remote('10.0.2.11', 10001)

conn.recvuntil("You have intercepted Davey Jones' submission:\n")
davey_jones_encrypted_input = conn.recvline().strip()

# split the iv from the encrypted input
iv = davey_jones_encrypted_input[:32]
davey_jones_encrypted_input = davey_jones_encrypted_input[32:]

# swap the blocks
forged_input = davey_jones_encrypted_input[:80*2] + davey_jones_encrypted_input[96*2:112*2] + davey_jones_encrypted_input[80*2:96*2] + davey_jones_encrypted_input[112*2:]

# add the iv back
forged_input = iv + forged_input

# send the forged input
conn.sendline(forged_input)

print(conn.recvall().decode())