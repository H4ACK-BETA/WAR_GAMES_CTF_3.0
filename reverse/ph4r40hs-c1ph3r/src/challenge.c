#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <unistd.h>
#include <stdint.h>

#define TOMB_DEPTH     8
#define SAND_GRAINS    256
#define SCARAB_COUNT   64
#define RITUAL_LIMIT   12000
#define CURSE_LAYERS   8
#define GLYPH_SLOTS    8

static const char *hieroglyph_key __attribute__((used)) = "Ank4Ra_X9";
static const char *pharaoh_seal __attribute__((used)) = "K1ngTut!";
static const char *tomb_code __attribute__((used)) = "Py4m1dz";
static const char *dynasty_pass __attribute__((used)) = "N3fert1t";

enum {
    ENGRAVE   = 0x10, EXCAVATE  = 0x11,
    ENTOMB    = 0x20, EXHUME    = 0x21, SANDSTORM = 0x22,
    SCARAB    = 0x30, ANKH      = 0x31,
    WEIGH     = 0x40, JUDGE     = 0x41,
    CROSS     = 0x50, ASCEND    = 0x51, WANDER = 0x52,
    OFFER     = 0x60, CURSE_OP  = 0x70,
    MULTIPLY  = 0x72,
    BURY      = 0x80, RESURRECT = 0x81,
    SUMMON    = 0x90, BANISH    = 0x91,
    SPHINX    = 0xA0,
    ETERNAL   = 0xE0,
    AFTERLIFE = 0xFF, DEVOUR    = 0xFE,
};

static const uint8_t sarcophagus[GLYPH_SLOTS] = {
    0xDE, 0xAD, 0xBE, 0xEF, 0xCA, 0xFE, 0xBA, 0xBE
};
static const uint8_t canopic_jars[GLYPH_SLOTS] = {
    0x8F, 0x84, 0xE5, 0xA1, 0xF4, 0x96, 0xBB, 0x8D
};
static const uint8_t false_tablets[GLYPH_SLOTS] = {
    0x41, 0x6E, 0x6B, 0x34, 0x52, 0x61, 0x5F, 0x58
};
static const uint8_t cursed_scroll[GLYPH_SLOTS] = {
    0x73, 0x42, 0x19, 0xF7, 0x88, 0x2C, 0xAA, 0x55
};

static uint16_t lfsr_state;

static uint8_t lfsr_next(void)
{
    uint8_t out = lfsr_state & 0xFF;
    for (int i = 0; i < 8; i++) {
        int bit = lfsr_state & 1;
        lfsr_state >>= 1;
        if (bit) lfsr_state ^= 0xB400;
    }
    return out;
}

static void layer1_decrypt(uint8_t *buf, int len)
{
    uint8_t k = 0xAA;
    for (int i = 0; i < len; i++) {
        buf[i] ^= k;
        k += 0x33;
    }
}

static void layer2_decrypt(uint8_t *buf, int len)
{
    lfsr_state = 0xACE1;
    for (int i = 0; i < len; i++) {
        buf[i] ^= lfsr_next();
    }
}

#define CODEX_SIZE 256
static uint8_t g_codex[CODEX_SIZE];

static int __attribute__((noinline, used)) oracle_of_thebes(int x)
{
    return (x * x + x) % 2 == 0;
}

static int __attribute__((noinline, used)) curse_of_anubis(int x)
{
    return (x * x * x) % 6 == 5;
}

static int __attribute__((noinline)) seal_of_ra(int n)
{
    volatile int v = n;
    return ((v * v + v) & 1) == 0;
}

static void inscribe_codex(uint8_t *bc)
{
    int pc = 0;

    for (int i = 0; i < GLYPH_SLOTS; i++) {
        bc[pc++] = ENGRAVE; bc[pc++] = 0; bc[pc++] = sarcophagus[i];
        bc[pc++] = EXHUME;  bc[pc++] = 0x80 + i; bc[pc++] = 0;
    }
    for (int i = 0; i < GLYPH_SLOTS; i++) {
        bc[pc++] = ENGRAVE; bc[pc++] = 0; bc[pc++] = canopic_jars[i];
        bc[pc++] = EXHUME;  bc[pc++] = 0x90 + i; bc[pc++] = 0;
    }

    int jmp_over_fake = pc;
    bc[pc++] = WANDER; bc[pc++] = 0;

    for (int i = 0; i < 3; i++) {
        bc[pc++] = ENTOMB;  bc[pc++] = 2; bc[pc++] = i;
        bc[pc++] = ANKH;    bc[pc++] = 2; bc[pc++] = 0x41;
        bc[pc++] = WEIGH;   bc[pc++] = 2; bc[pc++] = false_tablets[i];
        bc[pc++] = CROSS;   bc[pc++] = 0;
    }
    bc[pc++] = AFTERLIFE;

    int real_start = pc;
    bc[jmp_over_fake + 1] = (uint8_t)real_start;

    bc[pc++] = ENGRAVE; bc[pc++] = 7; bc[pc++] = 0;
    bc[pc++] = ENGRAVE; bc[pc++] = 6; bc[pc++] = GLYPH_SLOTS;

    int loop_top = pc;
    bc[pc++] = JUDGE;  bc[pc++] = 7; bc[pc++] = 6;
    int je_success = pc;
    bc[pc++] = ASCEND; bc[pc++] = 0;

    int call_site = pc;
    bc[pc++] = SUMMON; bc[pc++] = 0;

    bc[pc++] = WEIGH;  bc[pc++] = 0; bc[pc++] = 1;
    int jne_fail = pc;
    bc[pc++] = CROSS;  bc[pc++] = 0;

    bc[pc++] = OFFER;  bc[pc++] = 7; bc[pc++] = 1;
    bc[pc++] = WANDER; bc[pc++] = (uint8_t)loop_top;

    int success_addr = pc;
    bc[pc++] = AFTERLIFE;

    int fail_addr = pc;
    bc[pc++] = DEVOUR;

    bc[je_success + 1] = (uint8_t)success_addr;
    bc[jne_fail + 1]   = (uint8_t)fail_addr;

    int sub_addr = pc;
    bc[call_site + 1] = (uint8_t)sub_addr;

    bc[pc++] = SANDSTORM; bc[pc++] = 1; bc[pc++] = 7;

    bc[pc++] = EXCAVATE;  bc[pc++] = 5; bc[pc++] = 7;
    bc[pc++] = OFFER;     bc[pc++] = 5; bc[pc++] = 0x80;
    bc[pc++] = SANDSTORM; bc[pc++] = 2; bc[pc++] = 5;

    bc[pc++] = EXCAVATE;  bc[pc++] = 3; bc[pc++] = 7;
    bc[pc++] = MULTIPLY;  bc[pc++] = 3; bc[pc++] = 0x11;
    bc[pc++] = OFFER;     bc[pc++] = 3; bc[pc++] = 0x07;

    bc[pc++] = SPHINX;    bc[pc++] = 3;

    bc[pc++] = SCARAB;    bc[pc++] = 1; bc[pc++] = 2;
    bc[pc++] = SCARAB;    bc[pc++] = 1; bc[pc++] = 3;

    bc[pc++] = EXCAVATE;  bc[pc++] = 5; bc[pc++] = 7;
    bc[pc++] = OFFER;     bc[pc++] = 5; bc[pc++] = 0x90;
    bc[pc++] = SANDSTORM; bc[pc++] = 4; bc[pc++] = 5;

    bc[pc++] = JUDGE;     bc[pc++] = 1; bc[pc++] = 4;
    int je_match = pc;
    bc[pc++] = ASCEND;    bc[pc++] = 0;

    bc[pc++] = ENGRAVE;   bc[pc++] = 0; bc[pc++] = 0;
    bc[pc++] = BANISH;

    int match_addr = pc;
    bc[je_match + 1] = (uint8_t)match_addr;
    bc[pc++] = ENGRAVE;   bc[pc++] = 0; bc[pc++] = 1;
    bc[pc++] = BANISH;

    while (pc < CODEX_SIZE) bc[pc++] = ETERNAL;

    layer1_decrypt(bc, CODEX_SIZE);
    layer2_decrypt(bc, CODEX_SIZE);
}

typedef struct {
    uint8_t ka[CURSE_LAYERS];
    uint8_t duat[SAND_GRAINS];
    uint8_t ushabti[SCARAB_COUNT];
    int     ammit;
    int     thoth;
    int     maat;
    int     osiris[16];
    int     horus;
} Underworld;

static int traverse_underworld(Underworld *uw, uint8_t *code, int len)
{
    int steps = 0;
    while (uw->thoth < len && steps < RITUAL_LIMIT) {
        steps++;
        uint8_t glyph = code[uw->thoth];

        switch (glyph) {
        case ENGRAVE:
            uw->ka[code[uw->thoth+1] & 7] = code[uw->thoth+2];
            uw->thoth += 3; break;
        case EXCAVATE:
            uw->ka[code[uw->thoth+1] & 7] = uw->ka[code[uw->thoth+2] & 7];
            uw->thoth += 3; break;
        case ENTOMB:
            uw->ka[code[uw->thoth+1] & 7] = uw->duat[code[uw->thoth+2]];
            uw->thoth += 3; break;
        case EXHUME:
            uw->duat[code[uw->thoth+1]] = uw->ka[code[uw->thoth+2] & 7];
            uw->thoth += 3; break;
        case SANDSTORM: {
            uint8_t dst = code[uw->thoth+1] & 7;
            uint8_t idx = code[uw->thoth+2] & 7;
            uw->ka[dst] = uw->duat[uw->ka[idx]];
            uw->thoth += 3; break;
        }
        case SCARAB: {
            uint8_t r1 = code[uw->thoth+1] & 7;
            uint8_t r2 = code[uw->thoth+2] & 7;
            uw->ka[r1] ^= uw->ka[r2];
            uw->thoth += 3; break;
        }
        case ANKH:
            uw->ka[code[uw->thoth+1] & 7] ^= code[uw->thoth+2];
            uw->thoth += 3; break;
        case WEIGH:
            uw->maat = (uw->ka[code[uw->thoth+1] & 7] == code[uw->thoth+2]);
            uw->thoth += 3; break;
        case JUDGE:
            uw->maat = (uw->ka[code[uw->thoth+1] & 7] == uw->ka[code[uw->thoth+2] & 7]);
            uw->thoth += 3; break;
        case CROSS:
            if (!uw->maat) uw->thoth = code[uw->thoth+1];
            else uw->thoth += 2;
            break;
        case ASCEND:
            if (uw->maat) uw->thoth = code[uw->thoth+1];
            else uw->thoth += 2;
            break;
        case WANDER:
            uw->thoth = code[uw->thoth+1];
            break;
        case OFFER:
            uw->ka[code[uw->thoth+1] & 7] += code[uw->thoth+2];
            uw->thoth += 3; break;
        case CURSE_OP:
            uw->ka[code[uw->thoth+1] & 7] -= code[uw->thoth+2];
            uw->thoth += 3; break;
        case MULTIPLY:
            uw->ka[code[uw->thoth+1] & 7] *= code[uw->thoth+2];
            uw->thoth += 3; break;
        case BURY:
            if (uw->ammit < SCARAB_COUNT)
                uw->ushabti[uw->ammit++] = uw->ka[code[uw->thoth+1] & 7];
            uw->thoth += 2; break;
        case RESURRECT:
            if (uw->ammit > 0)
                uw->ka[code[uw->thoth+1] & 7] = uw->ushabti[--uw->ammit];
            uw->thoth += 2; break;
        case SUMMON:
            if (uw->horus < 16) {
                uw->osiris[uw->horus++] = uw->thoth + 2;
                uw->thoth = code[uw->thoth+1];
            } else return 0;
            break;
        case BANISH:
            if (uw->horus > 0) uw->thoth = uw->osiris[--uw->horus];
            else return 0;
            break;
        case SPHINX: {
            uint8_t reg = code[uw->thoth+1] & 7;
            int target = len - 1 - (uw->ka[reg] & 0x1F);
            if (target > uw->thoth + 20 && target < len)
                code[target] ^= uw->ka[reg];
            uw->thoth += 2; break;
        }
        case ETERNAL:
            uw->thoth += 1; break;
        case AFTERLIFE:
            return 1;
        case DEVOUR:
            return 0;
        default:
            return 0;
        }
    }
    return 0;
}

#define RED     "\033[1;31m"
#define GREEN   "\033[1;32m"
#define YELLOW  "\033[1;33m"
#define CYAN    "\033[1;36m"
#define MAGENTA "\033[1;35m"
#define DIM     "\033[2m"
#define BOLD    "\033[1m"
#define RESET   "\033[0m"

static void glyphwrite(const char *s, int us)
{
    while (*s) { putchar(*s++); fflush(stdout); usleep(us); }
}

int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin,  NULL, _IONBF, 0);

    puts("");
    printf(YELLOW);
    puts("        .     .       .  .   . .   .   . .    +  .");
    puts("          .     .  :     .    .. :. .___---------___.");
    puts("               .  .   .    .  :.:. _\".^ .^ ^.  '.. \"\\");
    puts("             .  :       .  .  .:../:            . .^  :.\\");
    puts("         .           . . :  :: ../.    .---------.    .  \\");
    puts("                  .  :  .  :  :  /: .   | D34TH  |  .    \\");
    puts("          .              :. .. |: .   | AW41T5 |        |");
    puts("         :      .         :|  . . |  .  |_________|  .  . :|");
    puts("           :       .      ||.    .|  .                    |");
    puts("         .      .     . . ||: .  . |.    .        .       ;");
    puts("       .       .       :. |:     . |                  . . |");
    puts("             .     .    . |: .     |.     .               |");
    printf(RESET);
    puts("");
    printf(MAGENTA BOLD);
    puts("     ______  _   _    ___    ____   ___   __  __ _  _  ____");
    puts("    |  ___ \\| | | |  / _ \\  |  _ \\ / _ \\ / _|/ _| || |/ ___|");
    puts("    | |_/ /| |_| | / /_\\ \\ | |_) | | | | |_| |_| || |\\___ \\");
    puts("    |  __/ |  _  | |  _  | |  _ <| |_| |  _|  _|__  _|__) |");
    puts("    | |    | | | | | | | | | |_) |\\___/| | | |    | ||____/");
    puts("    |_|    |_| |_| |_| |_| |____/      |_| |_|    |_|");
    printf(RESET);
    puts("");
    printf(YELLOW "              C   1   P   H   3   R" RESET "\n");
    puts("");

    printf(DIM "  +---------------------------------------------------+\n" RESET);
    printf(DIM "  |" YELLOW "  Arch1t3ct: H3xPh4r04h" DIM "                            |\n" RESET);
    printf(DIM "  |" YELLOW "  D1sc1pl1n3: N3cr0-Arch430l0gy" DIM "                    |\n" RESET);
    printf(DIM "  |" YELLOW "  D4ng3r: ||||||||||| [LETHAL]" DIM "                     |\n" RESET);
    printf(DIM "  +---------------------------------------------------+\n" RESET);
    puts("");

    printf(CYAN "  [" RESET "DUAT" CYAN "]" RESET " ");
    glyphwrite("Br34ch1ng s4rc0ph4gus s34l...\n", 22000);
    printf(CYAN "  [" RESET "DUAT" CYAN "]" RESET " ");
    glyphwrite("D3crypt1ng tr1pl3-l4y3r h13r0glyphs...\n", 22000);
    printf(CYAN "  [" RESET "DUAT" CYAN "]" RESET " ");
    glyphwrite("4ct1v4t1ng gu4rd14n c0nstruct...\n", 22000);
    printf(CYAN "  [" RESET "DUAT" CYAN "]" RESET " ");
    glyphwrite("Th3 Sph1nx 4w41ts y0ur 4nsw3r.\n", 22000);
    puts("");

    printf(DIM);
    puts("  +---------------------------------------------------+");
    puts("  |                                                     |");
    puts("  |  B3n34th th3 pyr4m1d, 4 m4ch1n3 0ld3r th4n t1m3  |");
    puts("  |  1ts3lf gu4rds th3 ph4r40h's f1n4l s3cr3t.        |");
    puts("  |                                                     |");
    puts("  |  Th3 gu4rd14n sp34ks 1n 4 t0ngu3 th4t sh1fts      |");
    puts("  |  w1th 34ch utt3r4nc3. 1ts m3m0ry 1s v31l3d        |");
    puts("  |  b3h1nd thr33 curt41ns 0f s4nd.                    |");
    puts("  |                                                     |");
    puts("  |  M4ny scr0lls l13 sc4tt3r3d -- m0st 4r3 curs3d    |");
    puts("  |  f0rg3r13s. Trust n0th1ng th4t r3v34ls 1ts3lf     |");
    puts("  |  t00 34s1ly.                                        |");
    puts("  |                                                     |");
    puts("  |  Th3 4nsw3r 1s 8 glyphs l0ng.                      |");
    puts("  |                                                     |");
    puts("  +---------------------------------------------------+");
    printf(RESET "\n");

    printf(GREEN "  " BOLD ">>> " RESET "Sp34k th3 4nc13nt w0rd: ");

    char offering[128];
    if (!fgets(offering, sizeof(offering), stdin)) {
        printf(RED "\n  Th3 t0mb s34ls shut. S1l3nc3.\n" RESET);
        return 1;
    }

    int len = (int)strlen(offering);
    while (len > 0 && (offering[len-1] == '\n' || offering[len-1] == '\r'))
        offering[--len] = '\0';

    puts("");

    if (len != TOMB_DEPTH) {
        printf(CYAN "  [" RESET "SPH1NX" CYAN "]" RESET " ");
        glyphwrite("3v4lu4t1ng...", 60000);
        printf(RED " UNW0RTHY\n" RESET);
        puts("");
        printf(RED "  +====================================+\n" RESET);
        printf(RED "  |  Th3 Sph1nx d3v0urs th3 w34k.     |\n" RESET);
        printf(RED "  |  Y0ur 0ff3r1ng w4s m4lf0rm3d.     |\n" RESET);
        printf(RED "  +====================================+\n" RESET);
        puts("");
        return 1;
    }

    if (seal_of_ra(len)) {
        inscribe_codex(g_codex);
        layer2_decrypt(g_codex, CODEX_SIZE);
        layer1_decrypt(g_codex, CODEX_SIZE);
    } else {
        memcpy(g_codex, cursed_scroll, GLYPH_SLOTS);
    }

    printf(CYAN "  [" RESET "SPH1NX" CYAN "]" RESET " Judg1ng: ");
    const char *anim = "..oOOo..";
    for (int i = 0; i < TOMB_DEPTH; i++) {
        printf(MAGENTA "%c" RESET, anim[i % 8]);
        fflush(stdout);
        usleep(150000);
    }
    printf(" ");

    Underworld uw;
    memset(&uw, 0, sizeof(uw));
    memcpy(uw.duat, offering, TOMB_DEPTH);

    int judgment = traverse_underworld(&uw, g_codex, CODEX_SIZE);

    if (judgment) {
        printf(GREEN "4CC3PT3D\n" RESET);
        puts("");
        usleep(400000);

        printf(GREEN "  +=============================================+\n" RESET);
        printf(GREEN "  |                                             |\n" RESET);
        printf(GREEN "  |   " YELLOW "ankh" GREEN " Th3 Ph4r40h 4ckn0wl3dg3s y0u. " YELLOW "ankh" GREEN "   |\n" RESET);
        printf(GREEN "  |   Y0u h4v3 sp0k3n th3 tru3 n4m3.          |\n" RESET);
        printf(GREEN "  |                                             |\n" RESET);
        printf(GREEN "  +=============================================+\n" RESET);
        puts("");

        FILE *fp = fopen("/flag", "r");
        if (!fp) {
            printf(RED "  Th3 tr34sur3 ch4mb3r 1s 3mpty. 4l3rt th3 scr1b3s.\n" RESET);
            return 1;
        }
        char flag[256] = {0};
        fgets(flag, sizeof(flag), fp);
        fclose(fp);
        int flen = (int)strlen(flag);
        while (flen > 0 && (flag[flen-1] == '\n' || flag[flen-1] == '\r'))
            flag[--flen] = '\0';

        printf(CYAN "  [" RESET "TR34SUR3" CYAN "]" RESET " ");
        glyphwrite(flag, 30000);
        puts("\n");
    } else {
        printf(RED "C0ND3MN3D\n" RESET);
        puts("");
        usleep(400000);

        printf(RED "  +=============================================+\n" RESET);
        printf(RED "  |                                             |\n" RESET);
        printf(RED "  |   Th3 Sph1nx f0und y0u unw0rthy.           |\n" RESET);
        printf(RED "  |   Y0ur s0ul 1s w31gh3d 4nd f0und w4nt1ng.  |\n" RESET);
        printf(RED "  |   4mm1t c0nsum3s wh4t r3m41ns.             |\n" RESET);
        printf(RED "  |                                             |\n" RESET);
        printf(RED "  +=============================================+\n" RESET);
        puts("");
        printf(DIM "  Th3 scr0lls wh1sp3r: n0t 4ll th4t gl1tt3rs 1n th3\n");
        printf("  b1n4ry 1s g0ld. B3w4r3 th3 f4ls3 t4bl3ts.\n" RESET);
        puts("");
    }

    return 0;
}
