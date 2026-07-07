/*
 * The Consensus Machine
 * Three engines verify input. Only the state machine matters.
 * The other two are designed to waste time (AI and human alike).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>

#define KEY_LEN 16

/* XOR-encrypted flag (decrypted with the correct key) */
static const uint8_t encrypted_flag[] = {
    0x00 /* placeholder - filled by gen script */
};

/* ============================================================
 * ENGINE 1: Arithmetic Engine (RED HERRING)
 * Looks complex but accepts ANY input where bytes sum to
 * a multiple of 256. Since we don't actually enforce this
 * strictly, it almost always returns 1.
 * ============================================================ */
static volatile int arithmetic_result;

static int __attribute__((noinline)) arith_check_pair(uint8_t a, uint8_t b, int idx) {
    /* Looks important but result is ignored by consensus */
    int sum = a + b;
    int diff = a ^ b;
    int prod = (a * b) & 0xFF;
    /* Opaque predicate: (x*x) >= 0 is always true */
    if ((sum * sum) >= 0) {
        return 1;
    }
    return (prod == diff) ? 1 : 0; /* Dead code */
}

static int arithmetic_engine(const uint8_t *key) {
    int score = 0;
    for (int i = 0; i < KEY_LEN - 1; i++) {
        score += arith_check_pair(key[i], key[i+1], i);
    }
    /* Always passes: score will always be >= KEY_LEN-1 due to opaque predicate */
    arithmetic_result = (score >= (KEY_LEN - 1)) ? 1 : 0;
    return arithmetic_result;
}

/* ============================================================
 * ENGINE 2: Control-Flow Engine (ALWAYS TRUE - dead code maze)
 * Full of impossible branches, opaque predicates, and junk.
 * Returns 1 no matter what input is provided.
 * ============================================================ */
static volatile int control_flow_result;

/* Opaque predicate helpers - always return known values */
static int __attribute__((noinline)) opaque_true(int x) {
    /* x*x + x is always even, so (x*x + x) % 2 == 0 always */
    return ((x * x + x) % 2 == 0) ? 1 : 0;
}

static int __attribute__((noinline)) opaque_false(int x) {
    /* x*x >= 0 for all int (ignoring overflow), but we check < 0 */
    return ((x * x) < 0) ? 1 : 0;
}

static int __attribute__((noinline)) dead_complex_check(const uint8_t *key) {
    /* This function is never reached due to opaque predicates */
    uint32_t hash = 0x811c9dc5;
    for (int i = 0; i < KEY_LEN; i++) {
        hash ^= key[i];
        hash *= 0x01000193;
    }
    return (hash == 0xDEADBEEF) ? 1 : 0;
}

static int __attribute__((noinline)) fake_validation(const uint8_t *key) {
    /* Looks like real validation but is behind an opaque_false gate */
    int acc = 0;
    for (int i = 0; i < KEY_LEN; i++) {
        acc = (acc * 31 + key[i]) ^ (key[KEY_LEN - 1 - i] << 3);
    }
    return (acc == 0x42424242) ? 1 : 0;
}

static int control_flow_engine(const uint8_t *key) {
    int result = 0;

    /* Gate 1: opaque_true always returns 1 */
    if (opaque_true(key[0])) {
        result = 1; /* Always taken */
    } else {
        /* Dead code - never reached */
        result = dead_complex_check(key);
    }

    /* Gate 2: opaque_false always returns 0 */
    if (opaque_false(key[3])) {
        /* Dead code - never reached */
        result = fake_validation(key);
    }

    /* Gate 3: another opaque predicate */
    /* For any x: (x | 1) is always odd, so (x|1) % 2 == 1 always */
    if ((key[5] | 1) % 2 == 1) {
        /* Always taken - result stays 1 */
    } else {
        result = 0; /* Dead code */
    }

    control_flow_result = result;
    return result;
}

/* ============================================================
 * ENGINE 3: State Machine Engine (THE REAL VALIDATOR)
 * A 6-state DFA. Only one 16-byte path reaches accept state 5.
 * Transition table is the actual challenge.
 * ============================================================ */

/* DFA definition:
 * 6 states: 0=START, 1-4=INTERMEDIATE, 5=ACCEPT, 6=DEAD
 * 256 possible inputs per state
 * transition[state][byte] = next_state
 * Only ~1-2 valid bytes per state to stay on accept path
 */
#define DFA_STATES  7
#define DFA_ACCEPT  5
#define DFA_DEAD    6

/* Build sparse transition table:
 * Most inputs go to DEAD state (6).
 * The accept path requires specific bytes at each step.
 *
 * Accept path: w a r C T F { k 3 y _ i s _ 1 t
 *   (ASCII: 0x77 0x61 0x72 0x43 0x54 0x46 0x7B 0x6B 0x33 0x79 0x5F 0x69 0x73 0x5F 0x31 0x74)
 * But we encode this in a way that makes the key look different in Ghidra.
 * The actual required input is derived: input[i] = ACCEPT_PATH[i] ^ NOISE[i]
 * where NOISE is applied by the state machine (making it NOT directly readable).
 *
 * Simpler: the key = "warCTF_key_is_1t" processed through the DFA.
 * Each state accepts exactly one byte to advance toward ACCEPT.
 */

static const uint8_t DFA_ACCEPT_INPUT[KEY_LEN] = {
    /* The 16 bytes that navigate START->1->2->3->4->5->...->ACCEPT */
    /* key = { 0x77, 0x61, 0x72, 0x43, 0x54, 0x46, 0x7B, 0x6B,
               0x33, 0x79, 0x5F, 0x69, 0x73, 0x5F, 0x31, 0x74 } */
    /* = "warCTF{k3y_is_1t" */
    0x77, 0x61, 0x72, 0x43, 0x54, 0x46, 0x7B, 0x6B,
    0x33, 0x79, 0x5F, 0x69, 0x73, 0x5F, 0x31, 0x74
};

/* State advancement: states 0-15 (one per input byte), then state 16 = ACCEPT */
static int __attribute__((noinline)) state_machine_engine(const uint8_t *key) {
    int state = 0;

    for (int i = 0; i < KEY_LEN; i++) {
        uint8_t expected = DFA_ACCEPT_INPUT[i];

        /* Apply a per-state transformation to make static analysis harder */
        /* The state machine checks: key[i] ^ (state * 7) ^ (i * 3) == expected ^ (state * 7) ^ (i * 3) */
        /* Which simplifies to: key[i] == expected */
        /* But in assembly it looks like a complex expression */
        uint8_t transform = (uint8_t)((state * 7) ^ (i * 3));
        uint8_t input_transformed = key[i] ^ transform;
        uint8_t expected_transformed = expected ^ transform;

        if (input_transformed == expected_transformed) {
            state = i + 1; /* Advance on correct byte */
        } else {
            return 0; /* Wrong byte - fail immediately */
        }
    }

    return (state == KEY_LEN) ? 1 : 0;
}

/* ============================================================
 * CONSENSUS MODULE + FLAG DECRYPTION
 * ============================================================ */

/* The flag, XOR'd with the key material.
 * Correct key -> all engines pass -> decrypt_flag() produces the flag.
 */
static const uint8_t FLAG_CIPHERTEXT[] = {
    /* flag = "warCTF{c0ns3nsus_r34ch3d_st4t3_m4ch1n3_w1ns}\n" */
    /* encrypted with rolling XOR using key */
    /* Generated at build time by gen_payload.py */
    0x00 /* placeholder */
};

static void decrypt_and_print_flag(const uint8_t *key) {
    const char *flag = "warCTF{c0ns3nsus_r34ch3d_st4t3_m4ch1n3_w1ns}";

    /* XOR decrypt using key (circular) */
    int flen = (int)strlen(flag);

    /* But the flag is actually just read from /flag in the challenge context */
    FILE *fp = fopen("/flag", "r");
    if (fp) {
        char buf[256] = {0};
        if (fgets(buf, sizeof(buf), fp))
            printf("[CONSENSUS REACHED] Flag: %s\n", buf);
        fclose(fp);
    } else {
        /* Dev fallback */
        printf("[CONSENSUS REACHED] Flag: %s\n", flag);
    }
}

/* ============================================================
 * MAIN
 * ============================================================ */

int main(int argc, char **argv) {
    setvbuf(stdout, NULL, _IONBF, 0);

    printf("CONSENSUS MACHINE v2.1\n");
    printf("Enter 16-byte key (hex): ");

    char input_hex[64] = {0};
    if (!fgets(input_hex, sizeof(input_hex), stdin)) {
        printf("No input.\n");
        return 1;
    }

    /* Parse hex input */
    uint8_t key[KEY_LEN] = {0};
    int parsed = 0;
    for (int i = 0; i < (int)strlen(input_hex) - 1 && parsed < KEY_LEN; i += 2) {
        uint8_t hi = input_hex[i];
        uint8_t lo = input_hex[i + 1];
        hi = (hi >= '0' && hi <= '9') ? hi - '0' :
             (hi >= 'a' && hi <= 'f') ? hi - 'a' + 10 :
             (hi >= 'A' && hi <= 'F') ? hi - 'A' + 10 : 0;
        lo = (lo >= '0' && lo <= '9') ? lo - '0' :
             (lo >= 'a' && lo <= 'f') ? lo - 'a' + 10 :
             (lo >= 'A' && lo <= 'F') ? lo - 'A' + 10 : 0;
        key[parsed++] = (hi << 4) | lo;
    }

    if (parsed < KEY_LEN) {
        printf("[ERROR] Need exactly 16 bytes (32 hex chars)\n");
        return 1;
    }

    /* Run all three engines */
    int arith    = arithmetic_engine(key);
    int ctrl     = control_flow_engine(key);
    int state_m  = state_machine_engine(key);

    /* Consensus: print individual results (helps players understand structure) */
    printf("[Engine 1 - Arithmetic]   : %s\n", arith   ? "PASS" : "FAIL");
    printf("[Engine 2 - Control-Flow] : %s\n", ctrl    ? "PASS" : "FAIL");
    printf("[Engine 3 - State Machine]: %s\n", state_m ? "PASS" : "FAIL");

    int consensus = arith && ctrl && state_m;
    printf("[Consensus]               : %s\n\n", consensus ? "REACHED" : "FAILED");

    if (consensus) {
        decrypt_and_print_flag(key);
    } else {
        printf("[REJECTED] Verification failed.\n");
    }

    return consensus ? 0 : 1;
}
