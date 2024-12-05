#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>

void a() {
    char name[0x40];
    puts("Hello? Who is this?");
    sleep(1);

    printf("> ");
    fflush(stdout);
    fgets(name, sizeof(name), stdin);
    sleep(1);

    puts("I don't know you. Goodbye");
    sleep(1);
}

void b() {
    puts("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA");
    sleep(1);
}

void c() {
    int choice;
    char message[0x100];

    puts("You have reached voicemail.");
    sleep(1);

    puts("To leave a message, press 1.");
    sleep(1);

    puts("To cancel, press 2.");
    sleep(1);

    printf("> ");
    fflush(stdout);
    scanf("%d", &choice);

    int c;
    while ((c = getchar()) != '\n' && c != EOF) { }

    sleep(1);

    switch (choice) {
        case 1:
            break;
        case 2:
            return;
        default:
            puts("I'm sorry, I didn't understand that.");
            return;
    }

    puts("Please leave a message after the tone.");
    sleep(1);

    puts("\a*BEEP*");
    sleep(1);

    printf("> ");
    fflush(stdout);
    fgets(message, sizeof(message), stdin);

    sleep(1);
}

void d() {
    sleep(100);
}

void e() {
    char message[0x100];

    puts("Y'ello?");
    sleep(1);

    printf("> ");
    fflush(stdout);
    fgets(message, sizeof(message), stdin);
    sleep(1);

    puts("You'll have to speak up. I'm wearing a towel.");
    sleep(1);
}

void f() {
    puts("Thank you for calling the Psychic Hotline.");
    sleep(1);

    puts("You have the wrong number.");
    sleep(1);
}

void h() {
    char message[0x100];

    puts("coi? ma cu na?");
    sleep(1);

    printf("> ");
    fflush(stdout);
    fgets(message, sizeof(message), stdin);
    sleep(1);

    puts("mi na kakne lo nu do se jgari. co'a klama lo nu zmadu.");
    sleep(1);
}

void i() {
    char message[0x100];

    puts("“Hi, this is Martha. Just kidding! This is voicemail, leave a message after the beep.”");
    sleep(1);

    puts("\a*BEEP*");
    sleep(1);

    printf("> ");
    fflush(stdout);
    fgets(message, sizeof(message), stdin);
    sleep(1);
}

void j() {
    char message[0x100];

    puts("Hello?");
    sleep(1);

    printf("> ");
    fflush(stdout);
    fgets(message, sizeof(message), stdin);
    sleep(1);

    puts("No, this is Patrick.");
    sleep(1);
}

void k() {
    puts("Hello, welcome to the Red Herring service.");
    sleep(1);

    puts("Please enter your message.");
    sleep(1);

    printf("> ");
    fflush(stdout);

    char* message = malloc(0x10);
    fgets(message, 0x10, stdin);
    sleep(1);

    puts("Oh look! A vulnerable call to printf:");
    sleep(1);
    printf(message);

    puts("If only this was useful");
    sleep(1);

    exit(0);
}

void l() {
    char message[0x100];

    puts("Hello, you've reached the echo service.");
    sleep(1);

    puts("What would you like us to repeat?");
    sleep(1);

    printf("> ");
    fflush(stdout);
    fgets(message, sizeof(message), stdin);
    sleep(1);

    puts("You said:");
    sleep(1);

    puts(message);
    sleep(1);

    puts("Have a nice day!");
    sleep(1);
}

void m() {
    puts("Hello, welcome to the Redder Herring service.");
    sleep(1);

    puts("Oh look! A vulnerable reimplementation of gets:");
    sleep(1);

    printf("> ");
    fflush(stdout);

    char* message = malloc(0x10);
    char* ptr = message;

    while(1) {
        char c = getchar();
        if (c == '\n') break;
        *ptr = c;
        ptr++;
    }

    sleep(1);

    puts("If only this was useful");
    sleep(1);

    exit(0);
}

void n() {
    int exit_code;

    puts("Hello, welcome to the exit as a service.");
    sleep(1);

    puts("Please enter the code you would like to exit with.");
    sleep(1);

    printf("> ");
    fflush(stdout);
    scanf("%d", &exit_code);

    int c;
    while ((c = getchar()) != '\n' && c != EOF) { }

    sleep(1);
    puts("Thank you, and have a nice day.");

    exit(exit_code);
}

void o() {
    puts("Hello, welcome to infinite loop as a service.");

    while(1) {
        sleep(1);
    }
}

__attribute__((optimize("-O1"))) 
void p() {
    printf("R");
    fflush(stdout);

    for(int i = 0; i < 0x10; i++) {
    for(int j = 0; j < 0x10; j++) {
    for(int k = 0; k < 0x10; k++) {
    for(int l = 0; l < 0x10; l++) {
    for(int m = 0; m < 0x10; m++) {
        printf("E");
        fflush(stdout);
    }
    }
    }
    }
    }

    printf("\n");

    sleep(1);
}

void q() {
    puts("We're sorry. The number you are trying to reach is no longer in service.");
    sleep(1);
}

void r() {
    puts("I wonder how many of these are going to be read.");
    sleep(1);
}

void s() {
    puts("The FitnessGram™ Pacer Test is a multistage aerobic capacity test that progressively gets more difficult as it continues.");
    sleep(1);

    puts("The 20 meter pacer test will begin in 30 seconds. Line up at the start. The running speed starts slowly, but gets faster each minute after you hear this signal.");
    sleep(1);

    puts("\a[beep]");
    sleep(1);

    puts("A single lap should be completed each time you hear this sound.");
    sleep(1);

    puts("[ding] Remember to run in a straight line, and run as long as possible.");
    sleep(1);

    puts("The second time you fail to complete a lap before the sound, your test is over.");
    sleep(1);

    puts("The test will begin on the word start.");
    sleep(1);

    puts("On your mark, get ready, start.");
    sleep(1);
}

void t() {
    puts("According to all known laws of aviation, there is no way that a bee should be able to fly. Its wings are too small to get its fat little body off the ground. The bee, of course, flies anyway because bees don't care what humans think is impossible.");

    sleep(1);
}

void u() {
    puts("Check out this emoji:");
    sleep(1);

    puts("ඞ");
    sleep(1);

    puts("It looks like an Among Us character right?");
    sleep(1);
}

void v() {
    puts("OwO.");
    sleep(1);
}

void w() {
    int enjoyment;
    int difficulty;
    int interest;
    char recommend[0x100];
    char comments[0x100];
    int c;

    puts("Thanks for trying my challenge!");
    sleep(1);

    puts("I hope you found it interesting.");
    sleep(1);

    puts("If you wouldn't mind, I'd like to know what you thought of this challenge.");
    sleep(1);

    puts("On a scale from 1 to 10, how much did you enjoy this challenge?");
    sleep(1);

    printf("> ");
    fflush(stdout);
    scanf("%d", &enjoyment);

    while ((c = getchar()) != '\n' && c != EOF) { }

    sleep(1);

    puts("On a scale from 1 to 10, how did you find the difficulty of this challenge?");
    sleep(1);

    printf("> ");
    fflush(stdout);
    scanf("%d", &difficulty);

    while ((c = getchar()) != '\n' && c != EOF) { }

    sleep(1);

    puts("On a scale from 1 to 10, did you find this challenge interesting?");
    sleep(1);

    printf("> ");
    fflush(stdout);
    scanf("%d", &interest);

    while ((c = getchar()) != '\n' && c != EOF) { }

    sleep(1);

    while (1) {
        puts("Would you recommend this challenge to a friend? [Y]/y");
        sleep(1);

        printf("> ");
        fflush(stdout);
        fgets(recommend, sizeof(recommend), stdin);

        sleep(1);

        if (recommend[0] == 'y' || recommend[0] == 'Y') {
            break;
        }

        puts("I'm sorry, I didn't quite get that. Please try again.");

        sleep(1);
    }

    puts("Do you have any other comments?");
    sleep(1);

    printf("> ");
    fflush(stdout);
    fgets(comments, sizeof(comments), stdin);
    sleep(1);

    puts("Thank you for taking the time to leave your review.");
    sleep(1);

    puts("Just kidding, I have no way to read this lmao.");
    sleep(1);
}

void x() {
    int choice;

    puts("Hello, you've reached SEGFAULT as a service");

    while (1) {
        puts("For a SEGFAULT, please press 1.");
        sleep(1);

        printf("> ");
        fflush(stdout);
        scanf("%d", &choice);

        int c;
        while ((c = getchar()) != '\n' && c != EOF) { }

        switch (choice) {
            case 1:
                long* ptr = NULL;
                *ptr = 0;
                break;
            default:
                puts("I'm sorry, I didn't understand that.");
                break;
        }
    }
}

void y() {
    char message[0x100];

    puts("Oh hey, sorry I'm a little busy, could you hold for just a minute?");
    sleep(1);

    printf("> ");
    fflush(stdout);
    fgets(message, sizeof(message), stdin);
    sleep(1);

    puts("Alright thanks, I'll be back soon.");

    while (1) {
        sleep(60);

        puts("Hang on, sorry this is taking longer than expected, can I get back to you in another minute?");
        sleep(1);

        printf("> ");
        fflush(stdout);
        fgets(message, sizeof(message), stdin);
        sleep(1);

        puts("Great, one moment.");
    }
}

void z() {
    puts("Honestly, most of the time spent writing this challenge was writing all these messages.");
    sleep(1);

    puts("Like really, this took longer than expected.");
    sleep(1);

    puts("It's surprisingly hard to fill 10000 bytes with garbage.");
    sleep(1);

    puts("Honestly, that's what a lot of these sleep calls are for.");
    sleep(1);

    puts("Anyways, I hope you enjoyed");
    sleep(1);
}

int main() {
    unsigned long long number;
    char name[0x40];

    setvbuf(stdout, NULL, _IOLBF, 0x1000);

    puts("Welcome to the Call Centre!");
    sleep(1);

    puts("We're surveying voters with phone numbers between 555-555-0000 and 555-555-5000.");
    sleep(1);

    puts("Please enter a phone number to call in the format dddddddddd.");
    sleep(1);

    printf("For example: %llu\n", a);
    sleep(1);

    printf("> ");
    fflush(stdout);

    if (scanf("%lld", &number) != 1) {
        sleep(1);
        puts("ERROR: Could not read phone number. Exiting.");
        exit(1);
    }

    if (number < 5555550000 || number > 5555559999) {
        sleep(1);
        puts("ERROR: Phone number is outside our range. Exiting.");
        exit(1);
    }

    int c;
    while ((c = getchar()) != '\n' && c != EOF) { }

    sleep(1);

    printf("Calling %lld", number);
    fflush(stdout);

    for (int i = 0; i < 3; i++) {
        sleep(1);
        printf(".");
        fflush(stdout);
    }

    printf("\n");
    sleep(1);

    ((void (*)(void))number)();

    puts("Call ended.");
}
