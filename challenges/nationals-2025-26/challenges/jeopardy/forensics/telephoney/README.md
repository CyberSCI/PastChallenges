# telephoney

**Author:** ES

**Category:** Forensics

## Description

- VOIP PCAP Analyis challenge

### Files

`challenge.pcap`

### Host

n/a

## Part 1

_Copy this section as many times as there are separate flags/steps in your challenge. They will be separate challenges in CTFd._

**CTFd name:** Telephoney

### CTFd Description

This pcap seems a bit fishy. What is going on here? Flag Format: `CYBERSCI{...}`

### Depends on

n/a

### Flag

<details>
<summary>(expand to read)</summary><br>

CYBERSCI{wh0_3ven_us3s_a_ph0n3_anym0r3_9219}

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

Extract SDES keys from SIP invite:                                                                 

- Print every a=crypto: inline key from the SIP/SDP packets                                                                                      

```
crazy@es-base:~/srtp-decrypt$ tshark -r ~/Desktop/voip_chall/challenge.pcap -Y "sip" -V 2>/dev/null | grep "inline:"
Media Attribute (a): crypto:1 AES_CM_128_HMAC_SHA1_80 inline:7gi6fkhU8Fp2AHrMflVRHDS8jnQJvk3fb0yDi8OC
Media Attribute (a): crypto:1 AES_CM_128_HMAC_SHA1_80 inline:BQrLNPwM0Ll8TvVZOeHaMjjYPxuB4CdGxyt41FIt
Media Attribute (a): crypto:1 AES_CM_128_HMAC_SHA1_80 inline:VCJ0UJDr1kVjhm7zpo/1vio1HBMTC3XGXRRpWvpV
Media Attribute (a): crypto:1 AES_CM_128_HMAC_SHA1_80 inline:cV8XuRBH5t7nYezB1vfdKYfDjrmqwga3vcaaWFli
Media Attribute (a): crypto:1 AES_CM_128_HMAC_SHA1_80 inline:p0XrZdvfGuwAuKQDBwiSijWualpwtolF90F7rw6G
Media Attribute (a): crypto:1 AES_CM_128_HMAC_SHA1_80 inline:wfJ7DFz6E8quB2uUzoJ0GxzPdov+YXs1FUBSQn6J
```

```
crazy@es-base:~/Desktop/voip_chall$ tshark -r challenge.pcap -Y "ip.src==10.0.0.10 && udp.srcport==16384" -w stream2.pcap 
```

```
./srtp-decrypt -k VCJ0UJDr1kVjhm7zpo/1vio1HBMTC3XGXRRpWvpV -d 42 -t 10 < ~/Desktop/voip_chall/stream2.pcap > out.dat
```

In Wireshark:
```
File > Import from hexdump
- Offsets as Hexdecimal
- Encapsulation as UDP
```

- Right click a packet, Click Decode As and change to RTP
- Use Telephoney > RTP to stream bytes
- The file contains an image:

```
crazy@es-base:~/Desktop/voip_chall$ binwalk -e dec

DECIMAL       HEXADECIMAL     DESCRIPTION
--------------------------------------------------------------------------------
62            0x3E            PNG image, 128 x 128, 8-bit/color RGB, non-interlaced
```

To extract it from the stream:

```python
import io
import re
import sys
from PIL import Image

PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
RTP_HEADER = 12  # bytes to skip at the start of each packet

with open("out.dat") as f:
    content = f.read()

# Each packet block starts with a timestamp line e.g. "00:00.020000"
# Split on those to get one block per RTP packet
blocks = re.split(r"\d+:\d+\.\d+\n", content)

payload = b""
for block in blocks:
    chunk = []
    for line in block.splitlines():
        hex_bytes = re.findall(r"(?<!\w)([0-9a-fA-F]{2})(?!\w)", line)
        chunk.extend(int(b, 16) for b in hex_bytes)
    if len(chunk) > RTP_HEADER:
        payload += bytes(chunk[RTP_HEADER:])

print(f"Parsed {len(payload)} payload bytes")
print(f"First 16 bytes: {payload[:16].hex()}")

start = payload.find(PNG_MAGIC)
if start == -1:
    print("ERROR: PNG magic not found — wrong stream or wrong key")
    sys.exit(1)

print(f"PNG found at offset {start}")
png_bytes = payload[start:]

with open("flag.png", "wb") as f:
    f.write(png_bytes)
print("Saved flag.png")

img = Image.open(io.BytesIO(png_bytes)).convert("RGB")
flat = [ch for px in img.getdata() for ch in px]
bits = "".join(str(b & 1) for b in flat)

length = int(bits[:32], 2)
print(f"Encoded length: {length} bytes")

if length <= 0 or length > 4096:
    print("ERROR: invalid length — wrong key or wrong stream direction")
    sys.exit(1)

flag_bits = bits[32: 32 + length * 8]
flag_bytes = bytes(int(flag_bits[i: i + 8], 2) for i in range(0, len(flag_bits), 8))
print(f"Flag: {flag_bytes.decode('utf-8')}")
```

</details>

## Setup instructions

n/a