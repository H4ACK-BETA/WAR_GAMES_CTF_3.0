#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#define SECRET_LEN 6
#define KEY 0x20
static const unsigned char secret[SECRET_LEN] = {
    0x51,  /* 'Q' */
    0x57,  /* 'W' */
    0x51,  /* 'Q' */
    0x52,  /* 'R' */
    0x50,  /* 'P' */
    0x58   /* 'X' */
};

int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin,  NULL, _IONBF, 0);

    puts("");
    puts("  ____        _                                ");
    puts(" | __ )  __ _| |__  _   _       _ __ _____   __");
    puts(" |  _ \\ / _` | '_ \\| | | |_____| '__/ _ \\ \\ / /");
    puts(" | |_) | (_| | |_) | |_| |_____| | |  __/\\ V / ");
    puts(" |____/ \\__,_|_.__/ \\__, |     |_|  \\___| \\_/  ");
    puts("                    |___/                       ");
    puts("");
    puts("        Author: H3xPh4r04h");
    puts("");
    puts("   I hid a secret in this binary...");
    puts("   Can you find the password?");
    puts("");
    printf("Enter password: ");

    char input[128];
    if (!fgets(input, sizeof(input), stdin)) {
        puts("No input received.");
        return 1;
    }

    /* Strip trailing newline/carriage return */
    int len = (int)strlen(input);
    while (len > 0 && (input[len - 1] == '\n' || input[len - 1] == '\r'))
        input[--len] = '\0';

    if (len != SECRET_LEN) {
        puts("Wrong! Try harder.");
        return 1;
    }

    /* Verify: input[i] + KEY should equal secret[i] */
    int correct = 1;
    for (int i = 0; i < SECRET_LEN; i++) {
        if ((unsigned char)(input[i] + KEY) != secret[i]) {
            correct = 0;
            break;
        }
    }

    if (!correct) {
        puts("Wrong! Try harder.");
        return 1;
    }

    /* Read and print the flag */
    FILE *fp = fopen("/flag", "r");
    if (!fp) {
        puts("Error: flag file missing. Contact admin.");
        return 1;
    }

    char flag[256] = {0};
    fgets(flag, sizeof(flag), fp);
    fclose(fp);

    int flen = (int)strlen(flag);
    while (flen > 0 && (flag[flen - 1] == '\n' || flag[flen - 1] == '\r'))
        flag[--flen] = '\0';

    printf("Correct! Here is your flag:\n%s\n", flag);
    return 0;
}
