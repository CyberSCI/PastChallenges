# Leaked and Loaded

## Prompt

One of the oppositions candidates campaign managers considers themselves to know a lot about security! So before they sent an email to their colleague with their account password they decided to "protect" it first. Can we retrieve the passcode? 

## Flag format

flag{}

## Explanation

This is a very simple warm-up challenge that can be completely solved through CyberChef. The challenge will be distributed through a text file. The attacker will need to identify what actions were done to encrypt the password. 

## Challenge Walkthrough

### Recipe to encrypt

```bash
To_Base64('A-Za-z0-9+/=')
ROT13(true,true,false,5)
To_Binary('Space',8)
```
## Recipe to decrypt

```bash
From_Binary('Space',8)
ROT13(true,true,false,21)
From_Base64('A-Za-z0-9+/=',true,false)
```

## Flags
- flag{ncaa-teal-rinsing-kin} -> challenge flag
- bel-trill-kindle -> sponsor flag
