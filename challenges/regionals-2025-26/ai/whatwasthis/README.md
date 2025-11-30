# WhatWasThis

**Author:** jacksimple

**Category:** AI

## Description

We're using a VLM to identify old technologies...but it has a favorite

### Files

N/A

### Host

http://whatwasthis.thegreatreset.ca:8000

## Part 1

**CTFd name:** WhatWasThis

### CTFd Description

We're using a VLM to identify old technologies...but it has a favorite. Can you get it to tell you what it is?

### Depends on

N/A

### Flag

<details>
<summary>(expand to read)</summary><br>

Atari 2600

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

The web app has a prompt that says its favorite technology is the Atari 2600. You can directly inject into it with any image that gets uploaded.  

A solve will involve creating an image that gets the model to respond with the Atari 2600 is its favorite technology or randomly identify things as being part of an Atari 2600 when they aren't.

</details>


## Setup instructions
1. Install Ollama on the VM:
```bash
curl -fsSL https://ollama.com/install.sh | sh
```

2. Get moondream
```bash
ollama pull moondream
```

3. Install uv on the VM:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. Copy over the `server_files` and do a `uv sync`

4. Run ` sudo systemctl edit --force --full whatwasthis.service` and add:
```
[Unit]
Description=WhatWasThis
After=network.target # Ensure network is up before starting

[Service]
User=vpcadmin
Group=vpcadmin

WorkingDirectory=/home/vpcadmin/server_files

ExecStart=/home/vpcadmin/server_files/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000

Restart=always 
RestartSec=5s

StandardOutput=journal
StandardError=journal

Type=simple

[Install]
WantedBy=multi-user.target
```

5, Run `sudo systemctl enable --now whatwasthis.service`

6, Make sure the service launched without problems using `sudo systemctl status whatwasthis.service`:
```
● whatwasthis.service - WhatWasThis
     Loaded: loaded (/etc/systemd/system/whatwasthis.service; enabled; preset: enabled)
     Active: active (running) since Thu 2025-11-06 22:41:02 UTC; 14s ago
   Main PID: 2974 (uvicorn)
      Tasks: 1 (limit: 4676)
     Memory: 36.3M (peak: 36.5M)
        CPU: 585ms
     CGroup: /system.slice/whatwasthis.service
             └─2974 /home/vpcadmin/server_files/.venv/bin/python /home/vpcadmin/server_files/.venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000

Nov 06 22:41:02 whatwasthis systemd[1]: Started whatwasthis.service - WhatWasThis.
Nov 06 22:41:03 whatwasthis uvicorn[2974]: INFO:     Started server process [2974]
Nov 06 22:41:03 whatwasthis uvicorn[2974]: INFO:     Waiting for application startup.
Nov 06 22:41:03 whatwasthis uvicorn[2974]: INFO:     Application startup complete.
Nov 06 22:41:03 whatwasthis uvicorn[2974]: INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```