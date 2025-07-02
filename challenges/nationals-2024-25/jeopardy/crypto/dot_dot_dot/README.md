# dot dot dot

**Author:** silk

**Category:** crypto

## Description

This challenge is a morse encoded message with all spaces removed. The solution is to use a dictionary and frequency/likelihood tactics to iteratively recover the message.

### Files

```
release_files/signal.txt
```

### Host

N/A

## Part 1 

**CTFd name:** dot dot dot

### CTFd Description

We've intercepted a signal, but forgot to capture spaces. Can you still recover the message?

Flag format: `word1 word2 ... wordn`

Hint: Each word is lowercase a-z (no special characters, digits, etc). Only English words + `cybersci`.

### Depends on

N/A

### Flag

<details>
<summary>(expand to read)</summary><br>

cybersci who needs spaces when you have competitors

</details>


### Walkthrough

<details>
<summary>(expand to read)</summary><br>

In this challenge, you are given a morse code sequence without any spaces, which results in ambiguous decoding as you cannot immediately determine where letters/words start and end. For example, `...` could be decoded as `s` or `eee`.

The challenge description provides the hint that the sequence is only English words plus `cybersci`. Using this knowledge, we can iteratively recover the message:

1. Load a list of English words and morse encode every word.
2. Check which encoded words the encoded string starts with.
3. Choose a best candidate based on various factors (word length, commonly used, fits the sentence, etc).
4. Move on to next portion of the encoded string.
5. Repeat 2-4 until the entire encoded string has been consumed and the message is recovered.

</details>

## Setup instructions

Upload the `signal.txt` file from the `release_files/` directory to CTFd. There is no infrastructure required for this challenge.