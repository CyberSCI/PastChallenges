#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>
#include <openssl/evp.h>
#include <openssl/sha.h>
#include <zlib.h>
#include <arpa/inet.h> 

#define DUMP_SIZE 135

// --------------------------------------------------
// Helpers
// --------------------------------------------------

void pad_field(uint8_t *dst, const uint8_t *src, size_t len) {
    size_t l = strlen((const char*)src);
    if (l > len) l = len;
    memcpy(dst, src, l);
    if (l < len) memset(dst + l, 0, len - l);
}

// --------------------------------------------------
// Key derivation (SHA256)
// --------------------------------------------------

void derive_key(uint8_t *key,
                uint8_t *name,
                uint8_t *surname,
                uint8_t *id,
                uint8_t gender)
{
    uint8_t material[67];

    pad_field(material,       name,    25);
    pad_field(material + 25,  surname, 25);
    pad_field(material + 50,  id,      16);
    material[66] = gender;

    SHA256(material, 67, key);
}

// --------------------------------------------------
// AES-256-ECB decrypt
// --------------------------------------------------

int decrypt_ecb(uint8_t *key, uint8_t *cipher, uint8_t *out)
{
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    int len, plaintext_len;

    EVP_DecryptInit_ex(ctx, EVP_aes_256_ecb(), NULL, key, NULL);
    EVP_CIPHER_CTX_set_padding(ctx, 1);

    EVP_DecryptUpdate(ctx, out, &len, cipher, 64);
    plaintext_len = len;

    if (!EVP_DecryptFinal_ex(ctx, out + len, &len)) {
        EVP_CIPHER_CTX_free(ctx);
        return -1;
    }

    plaintext_len += len;
    EVP_CIPHER_CTX_free(ctx);

    return plaintext_len;
}

// --------------------------------------------------
// CRC check
// --------------------------------------------------

int check_crc(uint8_t *data)
{
    uint32_t stored;
    memcpy(&stored, data + 131, 4);
    stored = ntohl(stored);

    uint32_t computed = crc32(0, data, 131);

    return stored == computed;
}

// --------------------------------------------------
// Main decode
// --------------------------------------------------

void decode(uint8_t *dump)
{
    // 1. CRC validation
    if (!check_crc(dump)) {
        printf("[-] Invalid data\n");
        exit(1);
    }



    // 2. Extract fields
    uint8_t name[26] = {0};
    uint8_t surname[26] = {0};
    uint8_t id[17] = {0};
    uint8_t gender = dump[66];

    memcpy(name, dump, 25);
    memcpy(surname, dump + 25, 25);
    memcpy(id, dump + 50, 16);

    // 3. Derive key
    uint8_t key[32];
    derive_key(key, name, surname, id, gender);

    // 4. Decrypt packet
    uint8_t plaintext[128] = {0};
    int len = decrypt_ecb(key, dump + 67, plaintext);

    if (len <= 0) {
        printf("[-] Invalid data\n");
        exit(1);
    }

    // --------------------------------------------------
    // 5. Validate IP header
    // --------------------------------------------------

    uint8_t version_ihl = plaintext[0];
    uint8_t protocol    = plaintext[9];

    if (version_ihl != 0x45) {
        printf("[-] Invalid data\n");
        exit(1);
    }

    if (protocol != 1) {
        printf("[-] Invalid data\n");
        exit(1);
    }

    // --------------------------------------------------
    // 6. Validate ICMP
    // --------------------------------------------------

    uint8_t icmp_type = plaintext[20];

    if (icmp_type != 8) {
        printf("[-] Invalid data\n");
        exit(1);
    }

    // --------------------------------------------------
    // 7. Extract payload (FLAG)
    // --------------------------------------------------

    uint8_t *payload = plaintext + 28; // IP(20) + ICMP header(8)
    printf("[+] Name: %s\n", name);
    printf("[+] Surname: %s\n", surname);
    printf("[+] ID: %s\n", id);
    printf("[+] Gender: %d\n", gender);
    printf("[+] Payload: %.32s\n", payload);
}

// --------------------------------------------------
// Hex loader
// --------------------------------------------------

int hex_to_bytes(const char *hex, uint8_t *out)
{
    size_t len = strlen(hex);
    if (len % 2 != 0) return -1;

    for (size_t i = 0; i < len / 2; i++) {
        sscanf(hex + 2*i, "%2hhx", &out[i]);
    }
    return len / 2;
}

// --------------------------------------------------

int main(int argc, char **argv)
{
    if (argc != 2) {
        printf("Usage: %s dump.hex\nThe file shall contain the ASCII representation of the hex digits.", argv[0]);
        return 1;
    }

    printf("Avian Reader expects exactly 135 bytes of data.\n");

    FILE *f = fopen(argv[1], "r");
    if (!f) {
        perror("fopen");
        return 1;
    }

    char hex[300];
    fgets(hex, sizeof(hex), f);
    fclose(f);

    uint8_t dump[DUMP_SIZE];
    int len = hex_to_bytes(hex, dump);

    if (len != DUMP_SIZE) {
        printf("[-] Invalid dump size\n");
        return 1;
    }

    decode(dump);
    return 0;
}