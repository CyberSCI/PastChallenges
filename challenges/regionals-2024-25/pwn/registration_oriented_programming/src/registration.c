#include <stdio.h>

void menu() {
    puts("1. Register new voter.");
    puts("2. Print registered voters.");
    puts("3. Exit.");
    printf("> ");
}

int get_int() {
    int choice;
    char choice_buf[8];
    fgets(choice_buf, sizeof(choice_buf), stdin);
    sscanf(choice_buf, "%d", &choice);
    return choice;
}

int main(int argc, char** argv) {
    setvbuf(stdin, NULL, _IONBF, 0);
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);

    int index = -1;
    char names[16][8];

    while (1) {
        menu();

        switch (get_int()) {
            case 1:
                printf("Index: ");
                index = get_int();

                printf("Name: ");
                fgets(names[index], sizeof(names[0]), stdin);

                puts("Registration successful!");
                break;
            case 2:
                puts("\n=== Registration List ===");
                for (int i = 0; i <= index; i++) {
                    printf("%d: ", i);
                    puts(names[i]);
                }
                puts("");
                break;
            case 3:
                return 0;
            default:
                puts("Unknown option.");
                break;
        }
    }

    return 0;
}
