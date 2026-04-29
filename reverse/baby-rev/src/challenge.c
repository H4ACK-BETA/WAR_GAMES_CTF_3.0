#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#define XOR_KEY      0x5A


static const unsigned char enc_password[] = {
    0x35, 0x2a, 0x3f, 0x34, 0x05,
    0x29, 0x3f, 0x29, 0x3b, 0x37,
    0x3f, 0x05, 0x6e, 0x68
};

#define PASS_LEN ((int)(sizeof(enc_password)))

int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin,  NULL, _IONBF, 0);

    puts("========================================");
    puts("           welcome to baby-rev          ");
    puts("   I know a secret. Can you find it?    ");
    puts("========================================");
    printf("Password: ");

    char input[256];
    if (!fgets(input, sizeof(input), stdin)) {
        puts("no input received.");
        return 1;
    }


    int len = (int)strlen(input);
    while (len > 0 && (input[len-1] == '\n' || input[len-1] == '\r'))
        input[--len] = '\0';

    if (len != PASS_LEN) {
        puts("Wrong! Keep reversing...");
        return 1;
    }

    int ok = 1;
    for (int i = 0; i < PASS_LEN; i++) {
        if (((unsigned char)input[i] ^ XOR_KEY) != enc_password[i]) {
            ok = 0;
            break;
        }
    }

    if (!ok) {
        puts("Wrong! Keep reversing...");
        return 1;
    }

    FILE *fp = fopen("/flag", "r");
    if (!fp) {
        puts("Error: flag file not found. Contact admin.");
        return 1;
    }
    char flag[256] = {0};
    fgets(flag, sizeof(flag), fp);
    fclose(fp);


    int flen = (int)strlen(flag);
    while (flen > 0 && (flag[flen-1] == '\n' || flag[flen-1] == '\r'))
        flag[--flen] = '\0';

    printf("Correct! Here is your flag:\n%s\n", flag);
    fflush(stdout);
    return 0;
}
