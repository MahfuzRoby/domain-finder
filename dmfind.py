#!/usr/bin/env python3
"""
Domain Name Finder
-------------------
Generates random 4-5 word .com domain candidates and checks real WHOIS
records to find ones that are genuinely unregistered.

Usage:
    python domain_finder.py
    python domain_finder.py --count 20 --words 4 --delay 2

Requires: Python 3.7+, no third-party packages (uses raw WHOIS socket query).
Run this on your own computer with internet access (not in a sandboxed
environment with restricted networking).
"""

import argparse
import random
import socket
import string
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Word source
# ---------------------------------------------------------------------------
# Tries to use the system dictionary (common on Linux/Mac at /usr/share/dict/words)
# for variety. Falls back to a built-in list of common short English words
# if no system dictionary is found (e.g. on Windows).

FALLBACK_WORDS = """able acid aged also area army away baby back ball band bank base
bath bear beat been beer bell belt best bike bird bite blue boat body bold bolt
bone book boom boot bore born boss both bowl bulk bull burn bush busy cafe cake
call calm came camp card care case cash cast cave chip city clay clip club coal
coat code cold come cook cool cope copy core cost crew crop dark dart dash data
dawn deal dear debt deep deny desk dial dice diet dirt dish dock does done door
dose down draw drop drug dry due dust duty each earn east easy edge else even
ever evil exit face fact fail fair fall fame farm fast fate fear feed feel fell
felt file fill film find fine fire firm fish fist five flag flat flow fold folk
food foot ford form fort foul four free from fuel full fund fury fuse gain game
gate gave gear gene gift girl give glad glow goal gold gone good gray grid grip
grow gulf hair half hall halt hand hang hard harm hate have head heal heap hear
heat held hell help here hero high hill hint hire hold hole holy home hood hook
hope horn host hour huge hung hunt hurt icon idea idle inch into iron item join
joke jump jury just keen keep kept kick kind king kiss knee knew knit knot know
lack lady lake land lane last late lawn lead leaf lean leap left lend less life
lift like limb limp line link lion list live load loan lock logo lone long look
loop lord lose loss lost loud love luck lung made mail main make mall many mark
mask mass mate math maze meal mean meat meet melt menu mere mesh mild mile milk
mind mine mint miss mode mood moon more most move much must myth name navy near
neat neck need news next nice nine node none note nuts oath obey okay omit once
only onto open oral over pace pack page paid pain pair pale palm park part pass
past path peak pick pile pink pipe plan play plot plug plus poem poet poll pond
pool poor pose post pour pray pump pure push race rack rage rail rain rank rare
rate rays read real rear rely rent rest rice rich ride ring rise risk road rock
role roll roof room root rope rose rule rush rust safe sail sake sale salt same
sand save scan seal seat seed seek seem seen sell send sent sets shed ship shoe
shop shot show shut sick side sign silk sing site size skin slip slow snap snow
soap soft soil sold song soon sort soul soup sour spin spit spot star stay step
stir stop such suit sure swap sway sweet take tale talk tall tank tape task team
tear tell tent term test text than that them then they thin this thus tide tied
tiny tone took tool tour town toys trip true tune turn twin type unit upon used
user vain vast very vest vice view vine void vote wage wait wake walk wall want
warm warn wash wave weak wear weed week well went west what when wide wife wild
will wind wine wing wipe wire wise wish with wolf wood word wore work wrap yard
year your zero zinc zone""".split()


def load_wordlist():
    """Load words from system dictionary if available, else fallback list."""
    candidates = ["/usr/share/dict/words", "/usr/dict/words"]
    for path in candidates:
        p = Path(path)
        if p.exists():
            try:
                words = []
                with open(p, "r", errors="ignore") as f:
                    for line in f:
                        w = line.strip().lower()
                        # keep short, plain alphabetic words, skip names/apostrophes
                        if 3 <= len(w) <= 7 and w.isalpha() and "'" not in w:
                            words.append(w)
                if len(words) > 500:
                    print(f"Loaded {len(words)} words from {path}")
                    return words
            except Exception:
                pass
    print(f"Using built-in word list ({len(FALLBACK_WORDS)} words)")
    return FALLBACK_WORDS


# ---------------------------------------------------------------------------
# Domain generation
# ---------------------------------------------------------------------------

VOWELS = "aeiou"
CONSONANTS = "bcdfghjklmnpqrstvwxyz"


def generate_word_candidate(words, n_words):
    picks = random.sample(words, n_words)
    name = "".join(picks)
    if len(name) > 63:
        return None
    if not all(c in string.ascii_lowercase for c in name):
        return None
    return name + ".com"


def generate_letters_candidate(length, pronounceable=True):
    """Generate a short domain of pure letters, length 4 or 5."""
    if not pronounceable:
        name = "".join(random.choice(string.ascii_lowercase) for _ in range(length))
        return name + ".com"

    # Alternate consonant/vowel for something speakable, e.g. "zovek", "talu"
    name = ""
    start_with_consonant = random.choice([True, False])
    for i in range(length):
        is_consonant_slot = (i % 2 == 0) == start_with_consonant
        name += random.choice(CONSONANTS if is_consonant_slot else VOWELS)
    return name + ".com"


# ---------------------------------------------------------------------------
# WHOIS availability check
# ---------------------------------------------------------------------------

WHOIS_SERVER = "whois.verisign-grs.com"  # authoritative registry for .com
WHOIS_PORT = 43

# Phrases that indicate a domain is NOT registered, seen across registrars
NOT_FOUND_MARKERS = [
    "no match for",
    "not found",
    "no entries found",
    "no data found",
    "status: free",
    "no matching record",
]


def check_domain_available(domain, timeout=8):
    """
    Returns True if domain appears unregistered, False if registered,
    None if the check failed/was inconclusive (e.g. rate limited).
    """
    try:
        with socket.create_connection((WHOIS_SERVER, WHOIS_PORT), timeout=timeout) as s:
            s.sendall((domain + "\r\n").encode())
            response = b""
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                response += chunk
        text = response.decode(errors="ignore").lower()
        if not text.strip():
            return None
        return any(marker in text for marker in NOT_FOUND_MARKERS)
    except (socket.timeout, OSError) as e:
        print(f"  [warn] WHOIS check failed for {domain}: {e}")
        return None


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Find available 4-5 word .com domains")
    parser.add_argument("--count", type=int, default=10,
                         help="How many available domains to find before stopping (default: 10)")
    parser.add_argument("--mode", type=str, default="pronounceable",
                         choices=["words", "pronounceable", "random-letters"],
                         help="'words' = 4-5 real words joined, 'pronounceable' = speakable "
                              "nonsense like 'zovek' (default), 'random-letters' = pure "
                              "random letters like 'xqvk'")
    parser.add_argument("--words", type=str, default="4-5",
                         help="[words mode] Number of words per domain, e.g. '4', '5', or '4-5'")
    parser.add_argument("--length", type=str, default="4-5",
                         help="[pronounceable/random-letters mode] Domain length in letters, "
                              "e.g. '4', '5', or '4-5' (default: 4-5)")
    parser.add_argument("--delay", type=float, default=1.5,
                         help="Seconds to wait between WHOIS lookups, be polite to the server (default: 1.5)")
    parser.add_argument("--max-tries", type=int, default=2000,
                         help="Safety cap on total candidates checked (default: 2000)")
    parser.add_argument("--output", type=str, default="available_domains.txt",
                         help="File to save results to (default: available_domains.txt)")
    args = parser.parse_args()

    def parse_range(s):
        if "-" in s:
            lo, hi = s.split("-")
            return (int(lo), int(hi))
        return (int(s), int(s))

    word_range = parse_range(args.words)
    length_range = parse_range(args.length)

    words = load_wordlist() if args.mode == "words" else None
    found = []
    tried = set()
    attempts = 0

    mode_desc = {
        "words": f"{word_range[0]}-{word_range[1]} words each",
        "pronounceable": f"pronounceable, {length_range[0]}-{length_range[1]} letters each",
        "random-letters": f"pure random letters, {length_range[0]}-{length_range[1]} letters each",
    }[args.mode]
    print(f"\nSearching for {args.count} available .com domains ({mode_desc})...\n")

    while len(found) < args.count and attempts < args.max_tries:
        if args.mode == "words":
            n_words = random.randint(*word_range)
            domain = generate_word_candidate(words, n_words)
        else:
            length = random.randint(*length_range)
            domain = generate_letters_candidate(
                length, pronounceable=(args.mode == "pronounceable")
            )
        if not domain or domain in tried:
            continue
        tried.add(domain)
        attempts += 1

        result = check_domain_available(domain)
        if result is True:
            print(f"  ✅ AVAILABLE   {domain}")
            found.append(domain)
        elif result is False:
            print(f"  ❌ taken       {domain}")
        else:
            print(f"  ⚠️  skipped     {domain} (inconclusive)")

        time.sleep(args.delay)

    out_path = Path(args.output)
    out_path.write_text("\n".join(found) + ("\n" if found else ""))

    print(f"\nDone. Checked {attempts} candidates, found {len(found)} available domains.")
    print(f"Saved to: {out_path.resolve()}")
    if not found:
        print("Tip: try increasing --max-tries or --count, or widen the word range.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(0)
