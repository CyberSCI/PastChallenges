//!/usr/bin/python3
// -*- coding: utf8 -*-
//
// CyberSci Regionals 2025/26
//
// Dmitriy Beryoza (0xd13a@gmail.com)
//
// Water treatment challenge

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <dos.h>    // union REGS, int86

// MD2 hash of password 'waterworkz'
char PASSWORD_HASH[] = { 0x9e, 0x46, 0x24, 0x8d, 0x91, 0xfd, 0xcb, 
    0xec, 0xb3, 0xf4, 0xba, 0x7c, 0xaa, 0xe3, 0x8b, 0x0d };

// Data for MD2 algorithm
static const uint8_t S[256] = {
  41,46,67,201,162,216,124,  1, 61, 54, 84,161,236,240,  6, 19,
  98,167, 5,243,192,199,115,140,152,147, 43,217,188, 76,130,202,
  30,155,87, 60,253,212,224, 22,103, 66,111, 24,138, 23,229, 18,
  190, 78,196,214,218,158,222, 73,160,251,245,142,187, 47,238,122,
  169,104,121,145, 21,178,  7, 63,148,194, 16,137, 11, 34, 95, 33,
  128,127, 93,154, 90,144, 50, 39, 53, 62,204,231,191,247,151,  3,
  255, 25, 48,179, 72,165,181,209,215, 94,146, 42,172, 86,170,198,
  79,184, 56,210,150,164,125,182,118,252,107,226,156,116,  4,241,
  69,157,112, 89,100,113,135, 32,134, 91,207,101,230, 45,168,  2,
  27, 96, 37,173,174,176,185,246, 28, 70, 97,105, 52, 64,126, 15,
  85, 71,163, 35,221, 81,175, 58,195, 92,249,206,186,197,234, 38,
  44, 83, 13,110,133, 40,132,  9,211,223,205,244, 65,129, 77, 82,
  106,220, 55,200,108,193,171,250, 36,225,123,  8, 12,189,177, 74,
  120,136,149,139,227, 99,232,109,233,203,213,254, 59,  0, 29, 57,
  242,239,183, 14,102, 88,208,228,166,119,114,248,235,117, 75, 10,
  49, 68, 80,180,143,237, 31, 26,219,153,141, 51,159, 17,131, 20
};

static void md2(const uint8_t *msg, size_t len, uint8_t out[16]) {
    /* Step 1: pad to multiple of 16 with value = pad length */
    uint8_t pad = 16 - (len % 16 ? len % 16 : 16);
    size_t padded_len = len + pad;

    uint8_t C[16] = {0};
    uint8_t L = 0;

    uint8_t *buf = (uint8_t*)malloc(padded_len + 16); /* +checksum */
    size_t i;
    int j;
    uint8_t c;
    size_t total;
    uint8_t X[48] = {0};
    uint8_t t;
    int r;
    int k;
    if (!buf) exit(1);
    memcpy(buf, msg, len);
    memset(buf + len, pad, pad);

    /* Step 2: compute 16-byte checksum over the padded message,
       append it to the message */

    for (i = 0; i < padded_len; i += 16) {
        for (j = 0; j < 16; ++j) {
            c = buf[i + j];
            C[j] ^= S[c ^ L];
            L = C[j];
        }
    }
    memcpy(buf + padded_len, C, 16);
    total = padded_len + 16;

    /* Step 3: process blocks to produce digest */
    for (i = 0; i < total; i += 16) {
        /* Copy block and form state */
        for (j = 0; j < 16; ++j) {
            X[16 + j] = buf[i + j];
            X[32 + j] = X[16 + j] ^ X[j];
        }
        /* 18 rounds of mixing */
        t = 0;
        for (r = 0; r < 18; ++r) {
            for (k = 0; k < 48; ++k) {
                t = X[k] ^= S[t];
            }
            t = (t + r) & 0xFF;
        }
    }
    memcpy(out, X, 16);
    free(buf);
}

/*
  _   _               _                        ____    ___    ___    ___  
 | \ | |  ___  _ __  | |_  _   _  _ __    ___ |___ \  / _ \  / _ \  / _ \ 
 |  \| | / _ \| '_ \ | __|| | | || '_ \  / _ \  __) || | | || | | || | | |
 | |\  ||  __/| |_) || |_ | |_| || | | ||  __/ / __/ | |_| || |_| || |_| |
 |_| \_| \___|| .__/  \__| \__,_||_| |_| \___||_____| \___/  \___/  \___/ 
              |_|                                                         
*/

// ENcoded logo
char logo[] = {1,32,1,95,3,32,1,95,15,32,1,95,24,32,4,95,4,32,3,95,4,32,
    3,95,4,32,3,95,2,32,1,10,1,124,1,32,1,92,1,32,1,124,1,32,1,124,2,32,
    3,95,2,32,1,95,1,32,2,95,2,32,1,124,1,32,1,124,1,95,2,32,1,95,3,32,
    1,95,2,32,1,95,1,32,2,95,4,32,3,95,1,32,1,124,3,95,1,32,1,92,2,32,1,
    47,1,32,1,95,1,32,1,92,2,32,1,47,1,32,1,95,1,32,1,92,2,32,1,47,1,32,
    1,95,1,32,1,92,1,32,1,10,1,124,2,32,1,92,1,124,1,32,1,124,1,32,1,47,
    1,32,1,95,1,32,1,92,1,124,1,32,1,39,1,95,1,32,1,92,1,32,1,124,1,32,
    2,95,2,124,1,32,1,124,1,32,1,124,1,32,2,124,1,32,1,39,1,95,1,32,1,
    92,2,32,1,47,1,32,1,95,1,32,1,92,2,32,2,95,1,41,1,32,2,124,1,32,1,
    124,1,32,1,124,1,32,2,124,1,32,1,124,1,32,1,124,1,32,2,124,1,32,1,
    124,1,32,1,124,1,32,1,124,1,10,1,124,1,32,1,124,1,92,2,32,2,124,2,
    32,2,95,1,47,1,124,1,32,1,124,1,95,1,41,1,32,2,124,1,32,1,124,1,95,
    1,32,1,124,1,32,1,124,1,95,1,124,1,32,2,124,1,32,1,124,1,32,1,124,
    1,32,2,124,2,32,2,95,1,47,1,32,1,47,1,32,2,95,1,47,1,32,1,124,1,32,
    1,124,1,95,1,124,1,32,2,124,1,32,1,124,1,95,1,124,1,32,2,124,1,32,1,
    124,1,95,1,124,1,32,1,124,1,10,1,124,1,95,1,124,1,32,1,92,1,95,1,124,
    1,32,1,92,3,95,2,124,1,32,1,46,2,95,1,47,2,32,1,92,2,95,1,124,1,32,
    1,92,2,95,1,44,1,95,2,124,1,95,1,124,1,32,1,124,1,95,1,124,1,32,1,
    92,3,95,2,124,5,95,1,124,1,32,1,92,3,95,1,47,2,32,1,92,3,95,1,47,2,
    32,1,92,3,95,1,47,1,32,1,10,13,32,1,124,1,95,1,124,57,32,1,10};

// Buffer for string input
char input_buffer[80];

// Print logo on the screen
void printLogo() {
    int i;
    int count;

    printf("WELCOME TO\n");
    for (i = 0; i < sizeof(logo); i += 2) {
        for (count = 0; count < logo[i]; count++) {
            putchar(logo[i+1]);
        }
    }
    printf("\n                *** WATER TREATMENT PLANT MANAGEMENT SYSTEM ***\n");
}

// Input string from keyboard
void input_str(char* str) {
    printf(str);
    scanf("%s", input_buffer);
}

// Handle login
int login() {

    uint8_t digest[16];

    input_str("Enter password: ");

    md2(input_buffer, strlen(input_buffer), digest);

    if (0 == memcmp(digest, PASSWORD_HASH, 16)) {
        return 1;
    }

    printf("\n*** Incorrect password ***\n");

    return 0;
}

// Display and process the menu
int menu() {

    printf("\n\n*** MENU ***\n\n");
    printf("1 - Display system status\n");
    printf("2 - Control clarification system\n");
    printf("3 - Control sand filtration system\n");
    printf("4 - Control ozonation tank\n");
    printf("5 - Control carbon filtration system\n");
    printf("6 - Add chlorine gas\n");
    printf("0 - Exit\n\n");

    input_str("Select an option: ");

    printf("\n");

    return atoi(input_buffer);
}

// Safety code is: Aqu@Sh0cK!
char SAFETY_CODE[] = 
    { 0x1e, 1, 0x10, 0, 0x16, 0, 0x03, 1, 0x1f, 1, 0x23, 0, 0x0b, 0, 0x2e, 0, 0x25, 1, 0x02, 1 };

// Chlorination procedure
void chlorinate() {
    union REGS inregs, outregs;
    unsigned char scancode, flags;
    int i = 0;
    char codes[100];

    printf("*** DANGER: use care when adding chlorine gas into the system ***\n\n");
    printf("Enter safety code (ENTER to submit, ESC to cancel): \n");


    while (1) {

        // BIOS: AH=00 - wait for keystroke, return AL=ASCII (or 0), AH=scan code
        inregs.h.ah = 0x00;
        int86(0x16, &inregs, &outregs);
        scancode = (unsigned char) outregs.h.ah;

        // BIOS: AH=02 - get keyboard flags, AL = BIOS keyboard flags
        inregs.h.ah = 0x02;
        int86(0x16, &inregs, &outregs);
        flags = outregs.h.al;

        // Escape pressed
        if (scancode == 0x01) {
            return;
        }

        // Enter pressed
        if (scancode == 0x1c) {
            if (sizeof(SAFETY_CODE) == i) {
                if (0 == memcmp(codes, SAFETY_CODE, sizeof(SAFETY_CODE)))
                    break;
            }

            printf("\n*** Incorrect safety code ***\n");
            return;
        }

        codes[i] = scancode;
        codes[i + 1] = (flags & 0x03) ? 1 : 0;
        i += 2;
    }

    printf("\nCode is correct.\n");

    printf("\n*** Can't access chlorination system ***\n");
}

int main(int argc, char **argv) {

    int option;
    printLogo();
    if (login()) {
        while(1) {
            option = menu();

            switch (option) {
                case 0:
                    return 0;
                    break;

                case 1:
                    printf("Clarification system     - OFFLINE\n");
                    printf("Sand filtration system   - OFFLINE\n");
                    printf("Ozonation tank           - OFFLINE\n");
                    printf("Carbon filtration system - OFFLINE\n");
                    printf("Chlorination system      - OFFLINE\n");
                    break;
            
                case 2:
                    printf("*** Can't access clarification system ***\n");
                    break;

                case 3:
                    printf("*** Can't access sand filtration system ***\n");
                    break;
            
                case 4:
                    printf("*** Can't access ozonation tank ***\n");
                    break;

                case 5:
                    printf("*** Can't access carbon filtration system ***\n");
                    break;
            
                case 6:
                    chlorinate();
                    break;

                default:
                    break;
            }
        }
    }

    return 0;
}
