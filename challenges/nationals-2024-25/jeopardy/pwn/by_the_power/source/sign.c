#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <openssl/pem.h>
#include <openssl/rsa.h>
#include <openssl/evp.h>
#include <openssl/err.h>

void handle_errors(const char *msg) {
    fprintf(stderr, "%s\n", msg);
    ERR_print_errors_fp(stderr);
    exit(EXIT_FAILURE);
}

int main() {
    OpenSSL_add_all_algorithms();
    ERR_load_crypto_strings();

    // char key_path[256];
    // printf("Enter path to private key (PEM format): ");
    // scanf("%255s", key_path);
    char key_path[256] = "./files/badge";

    FILE *fp = fopen(key_path, "r");
    if (!fp) {
        perror("Unable to open private key file");
        return 1;
    }

    EVP_PKEY *pkey = PEM_read_PrivateKey(fp, NULL, NULL, NULL);
    fclose(fp);
    if (!pkey) {
        handle_errors("Failed to read private key");
    }

    char input[1024];
    printf("Enter string to sign: ");
    getchar();  // clear newline left in buffer
    fgets(input, sizeof(input), stdin);
    input[strcspn(input, "\n")] = '\0';  // Remove newline

    EVP_MD_CTX *mdctx = EVP_MD_CTX_new();
    if (!mdctx) {
        handle_errors("Failed to create MD context");
    }

    if (EVP_DigestSignInit(mdctx, NULL, EVP_sha256(), NULL, pkey) <= 0) {
        handle_errors("DigestSignInit failed");
    }

    if (EVP_DigestSignUpdate(mdctx, input, strlen(input)) <= 0) {
        handle_errors("DigestSignUpdate failed");
    }

    size_t siglen;
    if (EVP_DigestSignFinal(mdctx, NULL, &siglen) <= 0) {
        handle_errors("DigestSignFinal (size calculation) failed");
    }

    unsigned char *sig = malloc(siglen);
    if (!sig) {
        perror("Unable to allocate memory for signature");
        return 1;
    }

    if (EVP_DigestSignFinal(mdctx, sig, &siglen) <= 0) {
        handle_errors("DigestSignFinal failed");
    }

    printf("Signature (hex): ");
    for (size_t i = 0; i < siglen; i++) {
        printf("%02x", sig[i]);
    }
    printf("\n");

    free(sig);
    EVP_MD_CTX_free(mdctx);
    EVP_PKEY_free(pkey);
    EVP_cleanup();
    ERR_free_strings();

    return 0;
}
