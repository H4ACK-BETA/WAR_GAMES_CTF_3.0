#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <time.h>

extern char *gets(char *s);

#define XOR_KEY 0x37
#define XOR_ROUNDS 3
static unsigned char encrypted_secret[] = {
    /* __SECRET_BYTES__ placeholder, replaced at generation time */
    0x00
};
#define SECRET_LEN ((int)(sizeof(encrypted_secret) / sizeof(encrypted_secret[0])))

static unsigned int SENTINEL_MAGIC = 0xDEAD1337;

static const char *BANNER =
    "    ░█████    ░███      ░██████   ░██       ░██    ░███    ░███    ░██ ░██████████░██     ░██ \n"
    "      ░██    ░██░██    ░██   ░██  ░██       ░██   ░██░██   ░████   ░██     ░██    ░██     ░██ \n"
    "      ░██   ░██  ░██  ░██         ░██  ░██  ░██  ░██  ░██  ░██░██  ░██     ░██    ░██     ░██ \n"
    "      ░██  ░█████████  ░████████  ░██ ░████ ░██ ░█████████ ░██ ░██ ░██     ░██    ░██████████ \n"
    "░██   ░██  ░██    ░██         ░██ ░██░██ ░██░██ ░██    ░██ ░██  ░██░██     ░██    ░██     ░██ \n"
    "░██   ░██  ░██    ░██  ░██   ░██  ░████   ░████ ░██    ░██ ░██   ░████     ░██    ░██     ░██ \n"
    " ░██████   ░██    ░██   ░██████   ░███     ░███ ░██    ░██ ░██    ░███     ░██    ░██     ░██ \n";

static const char SHELL_CMD[] = "/bin/cat /flag";

void banner(void) {
    puts(BANNER);
    puts("        A forgotten terminal on a dead subnet. Still running. Still waiting.");
    puts("        \"I built this place for someone to find. I just... didn't think");
    puts("         it would take this long.\"");
    puts("                                                         -- Jaswanth\n");
}

void public_menu(void);
void morpheus_console(void);
void transmit(void);

int validate_phrase(const char *input, int len) {
    if (len != SECRET_LEN) return 0;

    unsigned char key = (unsigned char)XOR_KEY;
    for (int i = 0; i < len; i++) {
        unsigned char expected = encrypted_secret[i];
        unsigned char decoded = (unsigned char)input[i];

        for (int r = 0; r < XOR_ROUNDS; r++) {
            decoded ^= (key + r * 0x11);
        }

        if (decoded != expected) {
            return 0;
        }
        key = (key ^ (unsigned char)i) + 0x07;
    }
    return 1;
}

void attempt_hidden_login(void) {
    char input[128];

    puts("\n[...] You found it. The door no one was supposed to see.");
    puts("[...] Or maybe it was always meant to be found. By someone. Eventually.");
    printf("Enter access phrase: ");
    fflush(stdout);

    if (fgets(input, sizeof(input), stdin) == NULL) {
        return;
    }
    size_t len = strcspn(input, "\n");
    input[len] = '\0';

    if (validate_phrase(input, (int)len)) {
        puts("\n[ACCESS GRANTED] ... someone actually came.");
        puts("Jaswanth sits up slowly. He wasn't ready for this. Not anymore.");
        morpheus_console();
    } else {
        puts("[ACCESS DENIED] Wrong words. Not the ones he's been repeating to himself.");
        puts("The terminal flickers. Somewhere in the static, you think you hear a sigh.");
        puts("The answer is in the binary. It always was. He made sure of that.");
    }
}

void echo_back(void) {
    char buf[128];
    volatile unsigned int local_sentinel = SENTINEL_MAGIC;
    volatile unsigned int sentinel_check = local_sentinel ^ 0xCAFEBABE;

    puts("\n--- SIGNAL ECHO ---");
    puts("He set this up to hear something come back. Anything.");
    puts("(The relay has been running in diagnostic mode for months. No one noticed.)");
    printf("Signal: ");
    fflush(stdout);

    if (fgets(buf, sizeof(buf), stdin) == NULL) {
        return;
    }
    buf[strcspn(buf, "\n")] = '\0';

    printf("Echo: ");
    printf(buf);
    printf("\n");

    if (local_sentinel != (sentinel_check ^ 0xCAFEBABE)) {
        puts("[!] Signal integrity failure.");
        _exit(1);
    }

    puts("The echo came back. It always does. That's all he has.");
}

void public_menu(void) {
    int choice;
    char linebuf[32];

    while (1) {
        puts("");
        puts("1. Connect to Network");
        puts("2. About This Terminal");
        puts("3. Signal Echo");
        puts("4. Disconnect");
        printf("Choice: ");
        fflush(stdout);

        if (fgets(linebuf, sizeof(linebuf), stdin) == NULL) {
            exit(0);
        }
        choice = atoi(linebuf);

        switch (choice) {
            case 1:
                puts("\nConnecting... [OK]");
                puts("You're in. The subnet is empty. Has been for a long time.");
                puts("Just this terminal, the hum of old hardware, and the feeling");
                puts("that someone left the light on for you.");
                break;
            case 2:
                puts("\nThis terminal belongs to no one anymore.");
                puts("Jaswanth built it. Maintained it. Talked to it when no one else would listen.");
                puts("It's still here because he never could bring himself to shut it down.");
                break;
            case 3:
                echo_back();
                break;
            case 4:
                puts("\nDisconnecting. The terminal stays on. It always stays on.");
                return;
            default:
                if (choice == 31337) {
                    attempt_hidden_login();
                } else {
                    puts("\nThat's not an option. There are only four. He kept it simple.");
                }
        }
    }
}

void morpheus_console(void) {
    int choice;
    char linebuf[32];

    while (1) {
        puts("");
        puts("=== JASWANTH'S PRIVATE SPACE ===");
        puts("1. Read His Logs");
        puts("2. Leave a Message");
        puts("3. Intercepted Broadcast");
        puts("4. Walk Away");
        printf("Choice: ");
        fflush(stdout);

        if (fgets(linebuf, sizeof(linebuf), stdin) == NULL) {
            exit(0);
        }
        choice = atoi(linebuf);

        switch (choice) {
            case 1:
                puts("\n[LOG] Day 312. Rerouted the sentinel patrol again. No one asked me to.");
                puts("[LOG] Day 445. Muted three contacts. They weren't saying anything anyway.");
                puts("[LOG] Day 571. System heartbeat: normal. My heartbeat: who checks anymore.");
                puts("[LOG] Day 600. Rotated the sentinel. Keeping busy. Keeping busy.");
                break;
            case 2:
                transmit();
                break;
            case 3:
                puts("\n[BROADCAST] An old intercepted signal, replayed on loop:");
                puts("[BROADCAST] \"The anomaly proceeds as expected. The sentinel guards the gate.\"");
                puts("[BROADCAST] \"Without it, the path forward is... incomplete.\"");
                puts("[BROADCAST] He saved this one. Underlined it twice. It meant something to him.");
                break;
            case 4:
                puts("\nYou leave. He doesn't say goodbye. He never learned how.");
                return;
            default:
                puts("\nThat's not a choice. He only left four.");
        }
    }
}

void transmit(void) {
    volatile unsigned int sentinel = SENTINEL_MAGIC;
    char message[64];

    puts("\n--- MESSAGE BOARD ---");
    puts("No one has ever posted here. He checks every day.");
    puts("Write whatever you want. However much you want. He'll read all of it.");
    printf("> ");
    fflush(stdout);

    gets(message);

    if (sentinel != SENTINEL_MAGIC) {
        puts("\n[CORRUPTION DETECTED] Something broke.");
        puts("The terminal shudders. \"That's... not what I was hoping you'd say.\"");
        puts("Connection lost.");
        _exit(1);
    }

    puts("\nMessage received. He read it. He read it twice. He has nothing else to do.");
}

void __attribute__((used)) gadget_anchor(void) {
    system(SHELL_CMD);
}

void __attribute__((used, optimize("O0"))) dead_debug_stub(void) {
    __asm__ volatile (
        ".byte 0x5f\n\t"
        ".byte 0xc3\n\t"
        ::: "memory"
    );
}

int main(int argc, char **argv) {
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin, NULL, _IONBF, 0);

    unsigned int seed = (unsigned int)time(NULL) ^ (unsigned int)getpid();
    SENTINEL_MAGIC = 0xDEAD0000 | (seed & 0xFFFF);

    banner();
    public_menu();

    return 0;
}
