
# Walkthrough for By The Power of the key, open!

## Description

This is a pwn challenge targeted around badge access for rooms hosting the voting ballets. The code responsible for unlocking the doors has been leaked! Can the attackers figure out how to extract the secrets used to sign essential badges!

## Walkthrough

The goal of the challenge is to extract an RSA private key stored within the leaked verification code. The developers of this code were are the smartest and believe that they can secure the key within their binary.

The key has been xored with the meaning of life (42) before being stored in the binary.
Before the key is used for validation memfrob is used to decrypt the key. 

To extract this key use GDB to set a breakpoint on the memfrob function (the function can be identified with strings or list functions) then continue until memfrob exits and display the hex representation of the input variable to memfrob.

Then the extracted key needs to be provided to the keyserver and if valid the server will respond with the key
