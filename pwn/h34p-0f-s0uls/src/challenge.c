#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdint.h>

#define MAX_SOULS    8
#define SOUL_SIZE    0x68
#define NAME_MAX     0x60

typedef struct {
    void (*ritual)(void);
    char essence[SOUL_SIZE];
} SoulVessel;

static SoulVessel *graveyard[MAX_SOULS];
static int soul_count = 0;

static void win(void)
{
    FILE *fp = fopen("/flag", "r");
    if (!fp) {
        puts("Th3 v01d 1s 3mpty. C0nt4ct th3 n3cr0m4nc3r.");
        return;
    }
    char flag[256] = {0};
    fgets(flag, sizeof(flag), fp);
    fclose(fp);
    int flen = (int)strlen(flag);
    while (flen > 0 && (flag[flen-1] == '\n' || flag[flen-1] == '\r'))
        flag[--flen] = '\0';
    printf("\033[1;32m  [ASCEND] %s\033[0m\n", flag);
}

static void not_the_win(void)
{
    puts("Th1s s0ul w4s 4lr34dy c0nsum3d. N0th1ng r3m41ns.");
}

static void default_ritual(void)
{
    puts("Th3 s0ul s1ts qu13tly 1n th3 gr4v3y4rd...");
}

static void collect_soul(void)
{
    if (soul_count >= MAX_SOULS) {
        puts("Th3 gr4v3y4rd 1s full. R3l34s3 4 s0ul f1rst.");
        return;
    }

    int idx = -1;
    for (int i = 0; i < MAX_SOULS; i++) {
        if (!graveyard[i]) { idx = i; break; }
    }
    if (idx < 0) { puts("N0 sp4c3."); return; }

    SoulVessel *sv = (SoulVessel *)malloc(sizeof(SoulVessel));
    if (!sv) { puts("M4ll0c f41l3d."); return; }

    sv->ritual = default_ritual;
    memset(sv->essence, 0, SOUL_SIZE);

    printf("  N4m3 th3 s0ul: ");
    int n = read(0, sv->essence, NAME_MAX);
    if (n > 0 && sv->essence[n-1] == '\n') sv->essence[n-1] = '\0';

    graveyard[idx] = sv;
    soul_count++;
    printf("  S0ul #%d c0ll3ct3d.\n", idx);
}

static void release_soul(void)
{
    printf("  Wh1ch s0ul t0 r3l34s3? [0-%d]: ", MAX_SOULS - 1);
    int idx;
    if (scanf("%d", &idx) != 1 || idx < 0 || idx >= MAX_SOULS) {
        puts("  1nv4l1d.");
        while (getchar() != '\n');
        return;
    }
    while (getchar() != '\n');

    if (!graveyard[idx]) {
        puts("  Th4t gr4v3 1s 4lr34dy 3mpty.");
        return;
    }

    free(graveyard[idx]);
    graveyard[idx] = NULL;
    soul_count--;
    puts("  S0ul r3l34s3d 1nt0 th3 v01d.");
}

static void view_soul(void)
{
    printf("  Wh1ch s0ul t0 v13w? [0-%d]: ", MAX_SOULS - 1);
    int idx;
    if (scanf("%d", &idx) != 1 || idx < 0 || idx >= MAX_SOULS) {
        puts("  1nv4l1d.");
        while (getchar() != '\n');
        return;
    }
    while (getchar() != '\n');

    if (!graveyard[idx]) {
        puts("  N0 s0ul th3r3.");
        return;
    }

    printf("  S0ul #%d: ", idx);
    printf("R1tu4l@%p | ", (void *)graveyard[idx]->ritual);
    printf("3ss3nc3: %s\n", graveyard[idx]->essence);
}

static void edit_soul(void)
{
    printf("  Wh1ch s0ul t0 3d1t? [0-%d]: ", MAX_SOULS - 1);
    int idx;
    if (scanf("%d", &idx) != 1 || idx < 0 || idx >= MAX_SOULS) {
        puts("  1nv4l1d.");
        while (getchar() != '\n');
        return;
    }
    while (getchar() != '\n');

    if (!graveyard[idx]) {
        puts("  N0 s0ul th3r3.");
        return;
    }

    printf("  N3w 3ss3nc3 (p0ur y0ur p0w3r): ");
    int n = read(0, graveyard[idx]->essence, SOUL_SIZE + 0x20);
    if (n > 0 && graveyard[idx]->essence[n-1] == '\n')
        graveyard[idx]->essence[n-1] = '\0';

    puts("  S0ul 3ss3nc3 upd4t3d.");
}

static void perform_ritual(void)
{
    printf("  Wh1ch s0ul p3rf0rms th3 r1tu4l? [0-%d]: ", MAX_SOULS - 1);
    int idx;
    if (scanf("%d", &idx) != 1 || idx < 0 || idx >= MAX_SOULS) {
        puts("  1nv4l1d.");
        while (getchar() != '\n');
        return;
    }
    while (getchar() != '\n');

    if (!graveyard[idx]) {
        puts("  N0 s0ul th3r3.");
        return;
    }

    if (!graveyard[idx]->ritual) {
        puts("  Th1s s0ul h4s n0 r1tu4l.");
        return;
    }

    puts("  P3rf0rm1ng r1tu4l...");
    graveyard[idx]->ritual();
}

static void necro_info(void)
{
    printf("\033[2m  [D3BUG] w1n() = %p\033[0m\n", (void *)win);
    printf("\033[2m  [D3BUG] n0t_th3_w1n() = %p\033[0m\n", (void *)not_the_win);
}

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
    printf("\033[1;33m");
    puts("              S  0  U  L  S");
    printf("\033[0m");
    puts("");
    printf("\033[2m  +---------------------------------------------------+\n\033[0m");
    printf("\033[2m  |\033[1;33m  N3cr0m4nc3r: H3xPh4r04h\033[2m                          |\n\033[0m");
    printf("\033[2m  |\033[1;33m  D1sc1pl1n3: B1n4ry 3xpl01t4t10n\033[2m                  |\n\033[0m");
    printf("\033[2m  |\033[1;33m  D4ng3r: |||||||||| [S3V3R3]\033[2m                      |\n\033[0m");
    printf("\033[2m  +---------------------------------------------------+\n\033[0m");
    puts("");
}

static void story(void)
{
    printf("\033[2m");
    puts("  +---------------------------------------------------+");
    puts("  |                                                     |");
    puts("  |  Y0u st4nd b3f0r3 th3 Gr4v3y4rd 0f L0st S0uls.   |");
    puts("  |  34ch s0ul h0lds 4 fr4gm3nt 0f p0w3r.             |");
    puts("  |                                                     |");
    puts("  |  C0ll3ct th3m. M4n1pul4t3 th31r 3ss3nc3.          |");
    puts("  |  0v3rfl0w th31r b0und4r13s.                        |");
    puts("  |  P01s0n th3 ch41n 0f d34th.                        |");
    puts("  |  H1j4ck th3 r1tu4l.                                |");
    puts("  |                                                     |");
    puts("  |  0nly th3n w1ll th3 v01d y13ld 1ts s3cr3t.         |");
    puts("  |                                                     |");
    puts("  +---------------------------------------------------+");
    printf("\033[0m\n");
}

static void menu(void)
{
    printf("\033[1;36m");
    puts("  +---------------------------+");
    puts("  |  1. C0ll3ct S0ul          |");
    puts("  |  2. R3l34s3 S0ul          |");
    puts("  |  3. V13w S0ul             |");
    puts("  |  4. 3d1t S0ul             |");
    puts("  |  5. P3rf0rm R1tu4l        |");
    puts("  |  6. N3cr0 1nf0            |");
    puts("  |  7. 3x1t                  |");
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
    story();

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
        case 5: perform_ritual(); break;
        case 6: necro_info(); break;
        case 7:
            puts("  Th3 gr4v3y4rd f4d3s 1nt0 d4rkn3ss...");
            exit(0);
        default:
            puts("  Unkn0wn c0mm4nd.");
            break;
        }
        puts("");
    }

    return 0;
}
