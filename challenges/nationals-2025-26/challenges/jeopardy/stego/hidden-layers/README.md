# Hidden-Layers

**Author:** willem

**Category:** Stego

## Description

A language model researcher left behind two artifacts before disappearing. They said the truth was hiding in plain sight -- you just need to look at the data the right way. Contestants must reverse-engineer steganographic flags hidden in a tokenizer encoding and in a model embedding matrix.

### Files

- [passage.txt](./release_files/passage.txt)
- [embeddings.safetensors](./release_files/embeddings.safetensors)

### Host

No server required -- offline challenge.

## Part 1

**CTFd name:** Hidden Layers: The Passage

### CTFd Description

> A language model researcher left behind two artifacts before disappearing. They said the truth was hiding in plain sight -- you just need to look at the data the right way.
>
> The text doesn't make much sense, but the researcher insisted every word was chosen carefully.
>
> Files: [passage.txt](attachment), [embeddings.safetensors](attachment)
>
> **Flag format:** `CyberSci{...}`

### Depends on

None

### Flag

<details>
<summary>(expand to read)</summary><br>

`CyberSci{qw3n_t0k3n1z3r_LSB}`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

The passage was crafted so that each Qwen2.5-0.5B token ID's **least-significant bit** encodes one bit of the flag in ASCII.

1. Tokenize `passage.txt` with the `Qwen/Qwen2.5-0.5B` tokenizer.
2. Extract the LSB (`token_id % 2`) of each token ID to get a bitstream.
3. Group the bits into 8-bit bytes and convert to ASCII characters.

**Using Python:**

```
python3 challenges/jeopardy/stego/hidden-layers/solve_files/solve_flag1.py
```

</details>

## Part 2

**CTFd name:** Hidden Layers: The Weights

### CTFd Description

> The researcher was working with a Qwen2.5 architecture. Something about the weights feels... off.

### Depends on

Hidden Layers: The Passage

### Flag

<details>
<summary>(expand to read)</summary><br>

`CyberSci{3mb3dd1ng_gh0st_w31ght5}`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

The `embeddings.safetensors` file contains a 151,936 x 896 embedding matrix. Most rows look like random trained weights, but a contiguous block near the end (rows 151900-151933) has been overwritten: the first element of each row is a float32 ASCII code, and all remaining elements are 0.0.

1. Load the safetensors file and extract the `model.embed_tokens.weight` tensor.
2. Find rows where all elements except the first are zero (anomalous rows).
3. Read the first element of each anomalous row as an ASCII character code.

**Using Python:**

```
python3 challenges/jeopardy/stego/hidden-layers/solve_files/solve_flag2.py
```

</details>

## Setup instructions

1. Install dependencies: `pip install transformers safetensors numpy`
2. Run `server_files/generate_flag1.py` to produce `release_files/passage.txt`.
3. Run `server_files/generate_flag2.py` to produce `release_files/embeddings.safetensors` (~518 MB).
4. Verify Part 1: run `solve_files/solve_flag1.py` and confirm it prints `CyberSci{qw3n_t0k3n1z3r_LSB}`.
5. Verify Part 2: run `solve_files/solve_flag2.py` and confirm it prints `CyberSci{3mb3dd1ng_gh0st_w31ght5}`.
6. Upload `passage.txt` and `embeddings.safetensors` as CTFd attachments -- no server needed.
7. To regenerate with different flags, edit the `FLAG` constants in the generate scripts and re-run.
