#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

/*
 * Baby-pwn CTF Challenge
 * Difficulty: Easy-Med
 * Category: Binary Exploitation (ret2win)
 * Hint: The buffer is small, but the read is big.
 *       Can you redirect execution somewhere useful?
 */

void win(void)
{
    fflush(stdout);

    FILE *fp = fopen("/flag", "r");
    if (!fp) {
        puts("Error: flag file missing. Contact admin.");
        fflush(stdout);
        exit(1);
    }

    char buf[256] = {0};
    if (!fgets(buf, sizeof(buf), fp)) {
        puts("Error: could not read flag.");
        fflush(stdout);
        fclose(fp);
        exit(1);
    }
    fclose(fp);

    size_t len = strlen(buf);
    if (len > 0 && buf[len - 1] == '\n') buf[len - 1] = '\0';

    printf("You win! Here is your flag:\n%s\n", buf);
    fflush(stdout);
}

void vuln(void)
{
    char buf[64];

    printf("Enter your name: ");
    fflush(stdout);

    /* No bounds check — classic buffer overflow */
    fgets(buf, 256, stdin);

    printf("Hello, %s!\n", buf);
    fflush(stdout);
}

int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin,  NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);

    puts("");
    puts("  ____        _                                  ");
    puts(" | __ )  __ _| |__  _   _       _ ____      ___ __");
    puts(" |  _ \\ / _` | '_ \\| | | |_____| '_ \\ \\ /\\ / / '_ \\");
    puts(" | |_) | (_| | |_) | |_| |_____| |_) \\ V  V /| | | |");
    puts(" |____/ \\__,_|_.__/ \\__, |     | .__/ \\_/\\_/ |_| |_|");
    puts("                    |___/      |_|                   ");
    puts("");
    puts("        Author: H3xPh4r04h");
    puts("");
    puts("   My memory is not very well protected...");
    puts("   Can you smash your way to victory?");
    puts("");

    vuln();

    puts("Goodbye!");
    return 0;
}
