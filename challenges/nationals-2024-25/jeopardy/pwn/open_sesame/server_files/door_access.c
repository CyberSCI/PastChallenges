#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void print_access_logs()
{
    FILE *logs = fopen("physical_key_access_logs.txt", "r");
    if (logs == NULL)
    {
        printf("Almost there! Enter the same passcode on this challenge's server to reveal the logs.\n");
        exit(1);
    }
    char buffer[1000];
    printf("\nHere are the most recent physical key card access logs:\n");
    while (fgets(buffer, sizeof(buffer), logs) != NULL)
    {
        printf("%s", buffer);
    }
    printf("\n");
    fclose(logs);
}

void door_access()
{
    char input[32];
    const char *correct_passcode = "open_sesame";
    gets(input);
    printf("The passcode that you have entered is being confirmed...\n");
    printf("Access Denied! Try again.\n");
}

int main()
{
    setvbuf(stdout, NULL, _IONBF, 0); // <--- disable buffering
    printf("Welcome to the Remote Door Access System!\n");
    door_access();
    return 0;
}