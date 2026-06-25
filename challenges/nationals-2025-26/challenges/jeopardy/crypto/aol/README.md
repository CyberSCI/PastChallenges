# AOL (ApocalypseOnLine)

**Author:** raed

**Category:** Crypto

## Description

In the chaos following the EMP, old dial-up modems became some of the most reliable communication hardware still standing. ApocalypseOnLine (AOL) re-emerged as a grassroots ISP running over salvaged phone lines. We've been tracking a Remnant operative known as @viper92, and a dial-up session linked to their account was intercepted on a salvaged phone line. Our analyst says there's something wrong with the signal, but can't put their finger on it. It sounds like noise. Listen closer.

### Files

[aol_connection.wav](./release_files/aol_connection.wav)

## Part 1

**CTFd name:** AOL (ApocalypseOnLine)

### CTFd Description

> In the chaos following the EMP, old dial-up modems became some of the most reliable communication hardware still standing. ApocalypseOnLine (AOL) re-emerged as a grassroots ISP running over salvaged phone lines, and we've been tracking a Remnant operative known as @viper92 on it. A dial-up session linked to their account was intercepted. It sounds like a normal AOL connection; carrier tones, handshake, static. Our analyst swears something is off. Can you find what's hidden in the noise?
>
> File: [aol_connection.wav](attachment)

### Depends on

None

### Flag

<details>
<summary>(expand to read)</summary><br>

`cybersci{d14l-up-4nd-tun3-1n-241316}`
or (acceptable mistake participants can make)
`cybersci{d141-up-4nd-tun3-1n-241316}`

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

The flag is hidden in the **spectrogram** of the audio - it's encoded into the frequency content of seconds 4–8 of the recording. The key insight is using the right spectrogram settings: a window size of 64 samples with no overlap and a rectangular (boxcar) window. Any other window type or size will blur the character strokes.

**Using Audacity:**

1. Load `aol_connection.wav`.
2. Click the track name dropdown → **Spectrogram**.
3. Click the track name dropdown again → **Spectrogram Settings…**
4. Set the following:

   | Setting | Value |
   |---|---|
   | Window size | **64** |
   | Window type | **Rectangular** |
   | Zero padding factor | **1** |
   | Minimum frequency | **200** |
   | Maximum frequency | **3800** |

5. Click **OK**.
6. Zoom the timeline to **t=4–8s**.

The flag text will be clearly visible in the frequency bands.

**Using Python**:

```
python3 challenges/jeopardy/crypto/aol/solve_files/solve.py 
```

</details>

## Setup instructions

1. Run `server_files/generate_audio.py` to produce `release_files/aol_connection.wav`.
2. Verify: open the WAV in Audacity in spectrogram view and confirm the flag is clearly readable.
3. Upload `aol_connection.wav` as a CTFd attachment - no server needed.
4. To regenerate with a different flag, edit the `FLAG` constant in `generate_audio.py` and re-run.
