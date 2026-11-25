// Requires an AES-GCM key. Values use 16 unsigned big-endian bytes; output uses base 10.
export async function encrypt(x: bigint, key: CryptoKey): Promise<string> {
  if (x < 0n || x >= (1n << 128n)) throw new Error("Value out of range");
  const plaintext = new Uint8Array(16);
  for (let i = plaintext.length - 1, n = x; i >= 0; i--, n >>= 8n) {
    plaintext[i] = Number(n & 255n);
  }
  const iv = new Uint8Array(12);
  // A nonzero first IV byte keeps BigInt conversion lossless.
  do {
    crypto.getRandomValues(iv);
  } while (iv[0] === 0);
  const ciphertext = await crypto.subtle.encrypt(
    { name: "AES-GCM", iv },
    key,
    plaintext,
  );
  const data = new Uint8Array([...iv, ...new Uint8Array(ciphertext)]);
  return data.reduce((n, b) => (n << 8n) | BigInt(b), 0n).toString(10);
}

export async function decrypt(c: string, key: CryptoKey): Promise<bigint> {
  if (!/^[1-9][0-9]*$/.test(c)) throw new Error("Invalid ciphertext");
  const bytes: number[] = [];
  for (let n = BigInt(c); n > 0n; n >>= 8n) bytes.push(Number(n & 255n));
  const data = Uint8Array.from(bytes.reverse());
  if (data.length !== 44) throw new Error("Invalid ciphertext");
  const plaintext = await crypto.subtle.decrypt(
    { name: "AES-GCM", iv: data.subarray(0, 12) },
    key,
    data.subarray(12),
  );
  return new Uint8Array(plaintext).reduce((n, b) => (n << 8n) | BigInt(b), 0n);
}
