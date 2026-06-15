#define INPUT_SIZE 256
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define BANNER \
    "=========================================\n" \
    "           Welcome to baby-pwn           \n" \
    "   My memory is not very well protected. \n" \
    "=========================================\n" \

void win(void)
{
    /* flush before reading flag */
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

    /*No bound check*/
    fgets(buf, sizeof(buf)*4, stdin);
    buf[63] = '\0';

    printf("Hello, %s!\n", buf);
    fflush(stdout);
}

int main(void)
{
    /* Disable buffering */
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin,  NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);

    printf(BANNER);
    vuln();

    puts("Goodbye!");
    return 0;
}
