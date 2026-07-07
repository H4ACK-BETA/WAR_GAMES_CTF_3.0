#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#define XOR_KEY 0x37
static unsigned char encrypted_secret[] = {
    /* __SECRET_BYTES__ placeholder, replaced at generation time */
    0x00
};
#define SECRET_LEN ((int)(sizeof(encrypted_secret) / sizeof(encrypted_secret[0])))

void banner(void) {
    puts("=== MACHINE CITY ACCESS TERMINAL ===");
    puts("Authorized personnel only. All activity is logged.");
}

void public_menu(void);
void morpheus_console(void);
void transmit(void);
void become_the_one(void);

int validate_phrase(const char *input, int len) {
    if (len != SECRET_LEN) return 0;
    for (int i = 0; i < len; i++) {
        if ((unsigned char)(input[i] ^ XOR_KEY) != encrypted_secret[i]) {
            return 0;
        }
    }
    return 1;
}

void attempt_hidden_login(void) {
    char input[128];
    printf("Enter access phrase: ");
    fflush(stdout);

    if (fgets(input, sizeof(input), stdin) == NULL) {
        return;
    }
    size_t len = strcspn(input, "\n");
    input[len] = '\0';

    if (validate_phrase(input, (int)len)) {
        puts("\n[ACCESS GRANTED] Welcome back, operative.");
        morpheus_console();
    } else {
        puts("[ACCESS DENIED] This incident has been reported.");
    }
}

void public_menu(void) {
    int choice;
    char linebuf[32];

    while (1) {
        puts("");
        puts("1. Connect to Network");
        puts("2. About This Terminal");
        puts("3. Exit");
        printf("Choice: ");
        fflush(stdout);

        if (fgets(linebuf, sizeof(linebuf), stdin) == NULL) {
            exit(0);
        }
        choice = atoi(linebuf);

        switch (choice) {
            case 1:
                puts("\nConnecting... [OK]");
                puts("You are now jacked in. There is no spoon here, only data.");
                break;
            case 2:
                puts("\nThis terminal is property of the Machine City.");
                puts("Unauthorized access attempts are logged and traced.");
                break;
            case 3:
                puts("\nDisconnecting. Stay vigilant.");
                return;
            default:
                if (choice == 1337) {
                    attempt_hidden_login();
                } else {
                    puts("\nInvalid choice.");
                }
        }
    }
}

void morpheus_console(void) {
    int choice;
    char linebuf[32];

    while (1) {
        puts("");
        puts("=== MORPHEUS CONSOLE ===");
        puts("1. View System Logs");
        puts("2. Send Transmission");
        puts("3. Logout");
        printf("Choice: ");
        fflush(stdout);

        if (fgets(linebuf, sizeof(linebuf), stdin) == NULL) {
            exit(0);
        }
        choice = atoi(linebuf);

        switch (choice) {
            case 1:
                puts("\n[LOG] Sentinel patrol rerouted - sector 9.");
                puts("[LOG] Operative Trinity reported signal disturbance.");
                puts("[LOG] Zion mainframe heartbeat: nominal.");
                break;
            case 2:
                transmit();
                break;
            case 3:
                puts("\nLogging out of Morpheus Console.");
                return;
            default:
                puts("\nInvalid choice.");
        }
    }
}

void transmit(void) {
    char message[64];

    puts("\n--- SECURE TRANSMISSION UPLINK ---");
    puts("Broadcast your message to the resistance:");
    printf("> ");
    fflush(stdout);

    gets(message);

    puts("\nTransmission sent.");
}

void become_the_one(void) {
    puts("\n=== ROOT ACCESS GRANTED ===");
    puts("You are The One. The Matrix has no more secrets from you.\n");

    FILE *f = fopen("/flag.txt", "r");
    if (!f) {
        puts("[!] Flag file missing. Contact an admin.");
        return;
    }
    char buf[256];
    while (fgets(buf, sizeof(buf), f) != NULL) {
        fputs(buf, stdout);
    }
    fclose(f);
}

int main(int argc, char **argv) {
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin, NULL, _IONBF, 0);

    banner();
    public_menu();

    return 0;
}
