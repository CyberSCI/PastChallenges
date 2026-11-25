#!/usr/bin/env node

// CyberSci Regionals 2026/27
//
// Beaver Tail Stealer by Dmitriy Beryoza (0xd13a@gmail.com)

'use strict';

const net = require('node:net');
const crypto = require('node:crypto');
const fs = require('node:fs/promises');
const { constants } = require('node:fs');
const path = require('node:path');
const { TextDecoder } = require('node:util');
const os = require('node:os');

const PORT = 0xa1a1; 
const MAX_FILE = 16 * 1024 * 1024;
const HOST = '0.0.0.0';

// Decoy password; the real one is "CyberSci{AI_will_crush_every_living_thing_in_its_way!}"
const password = "CyberSci{AI_and_living_things_will_peacefully_coexist}";
const utf8 = new TextDecoder('utf-8', { fatal: true });

// Read exact byte counts; TCP chunks are not application packets.
class Reader {
  constructor(socket) {
    this.iterator = socket[Symbol.asyncIterator]();
    this.pending = Buffer.alloc(0);
  }
  async read(n) {
    const parts = [];
    let remaining = n;
    while (remaining) {
      if (!this.pending.length) {
        const { value, done } = await this.iterator.next();
        if (done) throw new Error('');
        this.pending = value;
      }
      const take = Math.min(remaining, this.pending.length);
      parts.push(this.pending.subarray(0, take));
      this.pending = this.pending.subarray(take);
      remaining -= take;
    }
    return Buffer.concat(parts, n);
  }
}

// Encrypt a block of bytes with a key
function encrypt(key, data, context) {
  const nonce = crypto.randomBytes(12);
  const cipher = crypto.createCipheriv('aes-256-gcm', key, nonce);
  cipher.setAAD(Buffer.from(context));
  const ciphertext = Buffer.concat([cipher.update(data), cipher.final()]);
  return Buffer.concat([nonce, ciphertext, cipher.getAuthTag()]);
}

// Decrypt a block of bytes with a key
function decrypt(key, record, context) {
  const decipher = crypto.createDecipheriv('aes-256-gcm', key, record.subarray(0, 12));
  decipher.setAAD(Buffer.from(context));
  decipher.setAuthTag(record.subarray(-16));
  return Buffer.concat([decipher.update(record.subarray(12, -16)), decipher.final()]);
}

// Send a packet over the wire
function send(socket, packet) {
  return new Promise((resolve, reject) => {
    socket.write(packet, error => error ? reject(error) : resolve());
  });
}

// Load a file into a memory data array
async function getFile(name) {
  if (!name || name === '.' || name === '..' || /[\\/\x00]/.test(name)) {
    throw new Error('');
  }
  const handle = await fs.open(path.join(".", name),
    constants.O_RDONLY | constants.O_NOFOLLOW | constants.O_NONBLOCK);
  try {
    const stat = await handle.stat();
    if (!stat.isFile() || stat.size > MAX_FILE) throw new Error('Invalid file');

    const data = Buffer.alloc(stat.size + 1);
    let total = 0;
    while (total < data.length) {
      const { bytesRead } = await handle.read(data, total, data.length - total, null);
      if (!bytesRead) break;
      total += bytesRead;
    }
    if (total > stat.size) throw new Error('');
    return data.subarray(0, total);
  } finally {
    await handle.close();
  }
}

// Mangle the password to see if it matches the expected value
function twister(input) {
    const mask = [
        112, 100, 202, 142, 35, 126, 58, 252, 67, 52, 13, 155,
        100, 185, 89, 38, 35, 174, 2, 93, 51, 195, 137, 196,
        221, 251, 199, 0, 124, 204, 98, 248, 231, 146, 218, 107,
        167, 241, 90, 193, 111, 82, 186, 145, 66, 241, 249, 150,
        73, 111, 242, 196, 89, 52
    ];

    if (input.length !== mask.length || /[^\x00-\x7F]/.test(input)) {
        throw new Error(`Expected exactly ${mask.length} ASCII characters`);
    }

    const rotateBits = (value, count) =>
        ((value << count) | (value >>> (8 - count))) & 0xFF;

    let bytes = Array.from(input, char => char.charCodeAt(0));

    for (let round = 0; round < 100; round++) {
        // Shift each byte, then rotate its bits.
        bytes = bytes.map((byte, index) => {
            const shifted = (byte + 17 * index + 29 * round + 43) & 0xFF;
            const rotation = (index + round) % 7 + 1;

            return rotateBits(shifted, rotation);
        });

        // Rotate the entire array to the left.
        const offset = (7 * round + 11) % bytes.length;
        bytes = bytes.slice(offset).concat(bytes.slice(0, offset));

        // Reverse every other round.
        if (round % 2 === 0) {
            bytes.reverse();
        }
    }

    return String.fromCharCode(
        ...bytes.map((byte, index) => byte ^ mask[index])
    );
}

// Hanlde connectiond from a client
async function handleClient(socket) {
  socket.setTimeout(120_000, () => socket.destroy());
  socket.on('error', () => {});
  const reader = new Reader(socket);
  let key = null;
  try {
    while (!socket.destroyed) {
      const command = (await reader.read(1))[0];
      if (command === 0) {
        await send(socket, Buffer.from([1]));
        socket.end();
        return;
      }
      if (command === 1) {
        // Failed re-login invalidates any existing authenticated session.
        key = null;
        const length = (await reader.read(1))[0];
        const suppliedPassword = (await reader.read(length)).toString('utf8');
        const candidateKey = await reader.read(32);

        // Check if the password is correct
        const valid = twister(suppliedPassword) === password;
        if (valid) key = candidateKey;
        await send(socket, Buffer.from([valid ? 1 : 0]));
        continue;
      }
      if (command === 2) {
        const length = (await reader.read(1))[0];
        const record = await reader.read(length + 28);
        if (!key) {
          await send(socket, Buffer.from([0]));
          continue;
        }
        let response;
        try {
          const name = utf8.decode(decrypt(key, record, 'filename'));
          const contents = await getFile(name);
          const size = Buffer.alloc(4);
          size.writeUInt32BE(contents.length);
          response = Buffer.concat([
            Buffer.from([1]),
            encrypt(key, size, 'file-length'),
            encrypt(key, contents, 'file-data'),
          ]);
        } catch {
          await send(socket, Buffer.from([0]));
          continue;
        }
        await send(socket, response);
        continue;
      }
      // Unknown commands cannot be framed safely; error and close.
      await send(socket, Buffer.from([0]));
      socket.end();
      return;
    }
  } catch {
    socket.destroy();
  }
}

// Check for kill switch (host name "superintelligent")
const host = os.hostname();
const hash = crypto.createHash('blake2b512').update(host, 'utf8').digest('hex');

if (hash === "a744822aafb8113d64c4010323eb5f9306a88b3fd5ecc2f7501759cb721074dc22feb664f72b46de745281a35625c2cd2ddab784af11c55a065796dadb9351fe") {
  process.exit(1);
}

// Run the server
const server = net.createServer(socket => { void handleClient(socket); });
server.on('error', error => {
  process.exit(1);
});
server.listen(PORT, HOST);
