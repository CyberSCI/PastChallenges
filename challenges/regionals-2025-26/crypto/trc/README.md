# _TRC_

**Author:** _Robert Babaev_

**Category:** _Crypto_

## Description

A while ago, one of our patrols managed to find a light flashing rhythmically. Short bursts, long bursts, there was a mix of the two. We're pretty sure it could be some kind of signal base. When we tried flashing a signal of our own, though, we always got the same response. Matter of fact, any sort of communication got more or less the same response.

### Files

N/A

### Host

`nc 10.0.2.41 42000`

## Part 1

**CTFd name:** TRC 1

### CTFd Description

Figure out what kind of message the station is sending. I don't think it's an S.O.S.

### Flag

<details>
<summary>(expand to read)</summary><br>

CyberSci{M0rse_th4n_ju5t_4_c0d3}

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

Regardless of what kind of message you send to the initial server, the response will be some garble of Morse Code. Decoding that, however, results in more garbled characters -- the response has been encoded first with Base32, then converted into Morse Code. This can be decoded using a CyberChef recipe, though writing a script wouldn't hurt -- especially for the next step.

</details>

## Part 2

**CTFd name:** TRC 2

### CTFd Description

Okay, I don't even want to ask why, how, or who thought of this, but it's honestly kind of genius -- and a little insane.

See if you can't communicate with the "server" in a way it'll recognize.

### Depends on

TRC 1

### Flag

<details>
<summary>(expand to read)</summary><br>

CyberSci{R3qu3s7_gr4n73d}

</details>

### Walkthrough

<details>
<summary>(expand to read)</summary><br>

Now you need to send an HTTP request to the server. However you construct the HTTP request message is up to you. What's important is that it gets encoded the same way the server encoded its message: Base32 into Morse Code. Sending a GET request to / should obtain the flag.

(You likely see now why I recommended the script.)

</details>

## Setup instructions

In literally any environment that supports Python 3.13, run `main.py` and make sure port 42000 is somehow accessible -- either via reverse proxy or via Docker container.

In this case, I opted for a systemd service as follows. You will need to ensure `main.py` is in `/usr/bin` for this example to work, along with a working installation of `python3`. If for some reason you do not have a working installation of `python3` . . . pray?

```ini
[Unit]
Description=TRC
After=network.target
Conflicts=getty@tty1.service

[Service]
User=vpcadmin
Group=vpcadmin
Restart=always
RestartSec=5s
StandardOutput=journal
StandardError=journal
Type=simple
ExecStart=/usr/bin/python3 /usr/bin/main.py
StandardInput=tty-force

[Install]
WantedBy=multi-user.target
```

Save that file as `/usr/lib/systemd/system/trc.service`.

In the terminal, run:

```bash
sudo systemctl enable --now trc.service
```

If all goes well, you should see `trc.service` up and running with:

```bash
systemctl status trc.service
```
