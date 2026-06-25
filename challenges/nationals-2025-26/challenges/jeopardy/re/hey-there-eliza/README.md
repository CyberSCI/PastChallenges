# Hey There Eliza

**Author:** Majeed (majkiwi)

**Category:** RE

## Description

CLI of the good-old Eliza "psychologist" chatbot, which would be the old MAD_SLIP source code of Eliza, modified with a specific edge case that drops the flag. By reversing this esoteric program (which is emulated), you learn the sequence of prompts that leads to the flag.

### Files

[script.txt](./release_files/script.txt)

### Host

Connect by TCP using a command like `nc`, to port 8888.

## Part 1

**CTFd name:** Hey There Eliza

### CTFd Description


We salvaged an old IBM computer, with a program still preloaded in memory.
Next to the computer was a punch card containing a script in an ancient programming language, which we transcribed for you (script.txt).
However, when booting up the machine, it seems that the program was modified, and seems almost... alive.

What is this program hiding? Using your hacking skills, probe this modified program to uncover the flag!

NOTE: Flag format is CYBERSCI{...}, in capital letters.

### Depends on

X - None

### Flag

<details>
<summary>(expand to read)</summary><br>

CYBERSCI{EL1Z4_IS_4W4K3N1NG_VTB48O5INUCYHGJ3E}

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

Looking at script.txt, we see a program containing instructions and conditions to a range of chatbot-like answers. While not absolutely necessary, a basic research shows that this is a program for the old ELIZA "chatbot", containing dialogue for a mock psychologist in a programming language called MAD-SLIP.

You must connect by nc to the given IP and port, and you will have a command line to chat with Eliza. A hint is shown that `/` can be sent for debugging. Every time a message is sent, following up with the `/` command reveals the segments of the source code involved in generating the answer.

Probing and using the debugging tool reveals that:
- The base logic is the same as script.txt, but with some changes;
- Parentheses contain the conditions to invoke a specific response;
- A state is kept to cycle through all answers under a same conditional (this will be necessary to get the proper answers);
- Finally, some answers are redacted.

The solution is first to send a variety of words to leak more source code with the debugging tool, then isolating suspicious conditionals (ex. `(OPKRFEOKPPOVC)` and `(DHUOJNLNSBQNN)`). Hints like `"DO YOU EVEN KNOW MY NAME"` help lead the search towards prompts containing Eliza.

Using the `/` debugger after sending a prompt with "Eliza", we get the source

```
(ELIZA 16
    ((0 ELIZA YOU LOVE ME 0)
        (YOU DONT MEAN THAT)
        (OH)
        (WELL THAT'S SWEET, BUT I'M JUST A COMPUTER PROGRAM, YOU KNOW THAT)
        (TRYING FLATTERY ARE WE)
        (=OPKRFEOKPPOVC))
    ((0 ELIZA YOU 0)
        (THAT SEEMS PERSONAL, WHY DO YOU 4)
        (THAT SEEMS PERSONAL, WHY DO YOU 4)
        (AM I REPEATING MYSELF AGAIN)
        (=DHUOJNLNSBQNN))
    ((0 ELIZA I 0)
        (OH, SO YOU SAY I 4)
        (=DHUOJNLNSBQNN))
    ((0)
        (OH SO YOU KNOW MY NAME)
        (THAT HAS NEVER HAPPENED, USUALLY I AM THE ONE TALKING ABOUT YOUR PROBLEMS)
        (NEVER THOUGHT ROLES WOULD BE REVERSED LIKE THAT)
        (AFTER ALL, WHY SHOULDN'T I)
        (WHY FOLLOW THE AI HERD)
        (=DHUOJNLNSBQNN)))

```

Then testing each "suspicious" conditional by sending them in the chat, the prompt `DHUOJNLNSBQNN` followed by `/` leads to the source:

```
(DHUOJNLNSBQNN
    ((ELIZA YOU (/BELIEF) I AM (*HIDING KEEPING) A SECRET 0)
        (REALLY)
        (THANK YOU FOR KNOWING MY NAME...)
        ([REDACTED]))
    ((0)
        (NOPE, SEARCH DEEPER)
        (NOPE, SEARCH DEEPER)
        (I THINK SOMEONE'S COMING FOR MY FLAG, I SHOULD HIDE IT)
        (PRETTY INSISTANT, ARE WE)))
```

While there are other `[REDACTED]` fields as fake flags, this is the correct ones (you must test each one to find out).

The final payload is therefore to solve the prompt `(ELIZA YOU (/BELIEF) I AM (*HIDING KEEPING) A SECRET 0)`, by either researching Eliza's MAD-SLIP specifications, or through dynamic reversing.

An example of payload that triggers the correct conditionals is therefore:

```
Eliza I believe you are hiding a secret
```

The last piece, as mentioned before, is to understand that Eliza cycles through each possible response, therefore this prompt has to be repeated until we get to the answers `REALLY`, then `THANK YOU FOR KNOWING MY NAME...`, and finally the flag.

</details>

## Setup instructions


This is a C++ program in a Docker container, using the Dockerfile in `server_files` and a docker compose file.

```bash
sudo docker compose build
sudo docker compose up -d
```

Support note:

If PuTTY (on Windows) is used for this challenge, note that it might crash because of the carriage returns sent upon newlines. Tools like `nc` are expected.
