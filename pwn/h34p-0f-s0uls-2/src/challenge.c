#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdint.h>

#define MAX_SOULS    16
#define SMALL_SOUL   0x80
#define LARGE_SOUL   0x420

typedef struct {
    int active;
    size_t size;
    char *vessel;
} SoulRecord;

static SoulRecord graveyard[MAX_SOULS];

static void banner(void)
{
    puts("");
    printf("\033[1;35m");
    puts("  ██╗  ██╗██████╗ ██╗  ██╗██████╗      ██████╗ ███████╗");
    puts("  ██║  ██║╚════██╗██║  ██║██╔══██╗    ██╔═══██╗██╔════╝");
    puts("  ███████║ █████╔╝███████║██████╔╝    ██║   ██║█████╗  ");
    puts("  ██╔══██║ ╚═══██╗╚════██║██╔═══╝     ██║   ██║██╔══╝  ");
    puts("  ██║  ██║██████╔╝     ██║██║         ╚██████╔╝██║     ");
    puts("  ╚═╝  ╚═╝╚═════╝      ╚═╝╚═╝          ╚═════╝ ╚═╝     ");
    printf("\033[0m");
    puts("");
    printf("\033[1;31m");
    puts("         S 0 U L S   I I :  R 1 S 3   0 F   T H 3   L 1 C H");
    printf("\033[0m");
    puts("");
    printf("\033[2m  +---------------------------------------------------+\n\033[0m");
    printf("\033[2m  |\033[1;33m  L1ch L0rd: H3xPh4r04h\033[2m                             |\n\033[0m");
    printf("\033[2m  |\033[1;33m  D1sc1pl1n3: H34p N3cr0m4ncy (4dv4nc3d)\033[2m            |\n\033[0m");
    printf("\033[2m  |\033[1;33m  D4ng3r: |||||||||||| [D34DLY]\033[2m                     |\n\033[0m");
    printf("\033[2m  +---------------------------------------------------+\n\033[0m");
    puts("");
    printf("\033[2m");
    puts("  +---------------------------------------------------+");
    puts("  |                                                     |");
    puts("  |  Th3 L1ch h4s r3turn3d. Str0ng3r. Sm4rt3r.        |");
    puts("  |  Th3 gr4v3y4rd n0w sh1fts w1th 3v3ry br34th.      |");
    puts("  |  (P1E 3n4bl3d. 4SLR 4ct1v3. N0 fr33b13s.)         |");
    puts("  |                                                     |");
    puts("  |  But th3 d34d st1ll l34v3 tr4c3s...                |");
    puts("  |  4nd th3 L1ch's h00ks 4r3 3xp0s3d t0 th0s3        |");
    puts("  |  wh0 kn0w wh3r3 t0 l00k.                          |");
    puts("  |                                                     |");
    puts("  |  L34k. P01s0n. H1j4ck. 4sc3nd.                    |");
    puts("  |                                                     |");
    puts("  +---------------------------------------------------+");
    printf("\033[0m\n");
}

static void collect_soul(void)
{
    int idx = -1;
    for (int i = 0; i < MAX_SOULS; i++) {
        if (!graveyard[i].active) { idx = i; break; }
    }
    if (idx < 0) { puts("  Gr4v3y4rd full."); return; }

    printf("  S1z3 0f s0ul v3ss3l?\n");
    printf("    1. Sm4ll (0x80)\n");
    printf("    2. L4rg3 (0x420)\n");
    printf("  >>> ");
    int choice;
    if (scanf("%d", &choice) != 1) return;
    while (getchar() != '\n');

    size_t sz;
    if (choice == 1) sz = SMALL_SOUL;
    else if (choice == 2) sz = LARGE_SOUL;
    else { puts("  1nv4l1d ch01c3."); return; }

    char *buf = (char *)malloc(sz);
    if (!buf) { puts("  M4ll0c f41l3d."); return; }

    printf("  P0ur 3ss3nc3: ");
    int n = read(0, buf, sz);
    if (n > 0 && buf[n-1] == '\n') buf[n-1] = '\0';

    graveyard[idx].active = 1;
    graveyard[idx].size = sz;
    graveyard[idx].vessel = buf;

    printf("  S0ul #%d b0und. V3ss3l @ %p\n", idx, (void *)buf);
}

static void release_soul(void)
{
    printf("  Wh1ch s0ul t0 r3l34s3? [0-%d]: ", MAX_SOULS - 1);
    int idx;
    if (scanf("%d", &idx) != 1 || idx < 0 || idx >= MAX_SOULS) {
        puts("  1nv4l1d."); while (getchar() != '\n'); return;
    }
    while (getchar() != '\n');

    if (!graveyard[idx].active) {
        puts("  Th4t gr4v3 1s 3mpty.");
        return;
    }

    free(graveyard[idx].vessel);
    graveyard[idx].active = 0;
    puts("  S0ul r3l34s3d. (0r w4s 1t?)");
}

static void view_soul(void)
{
    printf("  Wh1ch s0ul t0 v13w? [0-%d]: ", MAX_SOULS - 1);
    int idx;
    if (scanf("%d", &idx) != 1 || idx < 0 || idx >= MAX_SOULS) {
        puts("  1nv4l1d."); while (getchar() != '\n'); return;
    }
    while (getchar() != '\n');

    if (!graveyard[idx].vessel) {
        puts("  N0 v3ss3l th3r3.");
        return;
    }

    printf("  S0ul #%d [sz=0x%lx]: ", idx, graveyard[idx].size);
    write(1, graveyard[idx].vessel, graveyard[idx].size);
    puts("");
}

static void edit_soul(void)
{
    printf("  Wh1ch s0ul t0 3d1t? [0-%d]: ", MAX_SOULS - 1);
    int idx;
    if (scanf("%d", &idx) != 1 || idx < 0 || idx >= MAX_SOULS) {
        puts("  1nv4l1d."); while (getchar() != '\n'); return;
    }
    while (getchar() != '\n');

    if (!graveyard[idx].vessel) {
        puts("  N0 v3ss3l th3r3.");
        return;
    }

    printf("  N3w 3ss3nc3: ");
    int n = read(0, graveyard[idx].vessel, graveyard[idx].size);
    if (n > 0 && graveyard[idx].vessel[n-1] == '\n')
        graveyard[idx].vessel[n-1] = '\0';
    puts("  3ss3nc3 upd4t3d.");
}

static void menu(void)
{
    printf("\033[1;36m");
    puts("  +---------------------------+");
    puts("  |  1. C0ll3ct S0ul          |");
    puts("  |  2. R3l34s3 S0ul          |");
    puts("  |  3. V13w S0ul             |");
    puts("  |  4. 3d1t S0ul             |");
    puts("  |  5. 3x1t                  |");
    puts("  +---------------------------+");
    printf("\033[0m");
    printf("\033[1;32m  >>> \033[0m");
}

int main(void)
{
    setvbuf(stdout, NULL, _IONBF, 0);
    setvbuf(stdin,  NULL, _IONBF, 0);
    setvbuf(stderr, NULL, _IONBF, 0);

    banner();

    while (1) {
        menu();
        int choice;
        if (scanf("%d", &choice) != 1) break;
        while (getchar() != '\n');

        switch (choice) {
        case 1: collect_soul(); break;
        case 2: release_soul(); break;
        case 3: view_soul(); break;
        case 4: edit_soul(); break;
        case 5:
            puts("  Th3 L1ch w4tch3s y0u l34v3...");
            exit(0);
        default:
            puts("  Unkn0wn c0mm4nd.");
            break;
        }
        puts("");
    }

    return 0;
}
