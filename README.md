# Domain Name Finder

A simple Python script that generates random 4-5 letter (or word-based) `.com` domain candidates and checks **real WHOIS records** to find ones that are genuinely available to register.

No paid APIs, no API keys, no third-party packages — just Python's standard library and a raw WHOIS query.

## Features

- **Three generation modes:**
  - `pronounceable` (default) — speakable nonsense like `zovek.com`, `talune.com`
  - `random-letters` — pure random letters like `xqvk.com`
  - `words` — combines 4-5 real dictionary words like `quietfoxmarket.com`
- Checks live `.com` availability against the Verisign WHOIS registry
- Saves all available results to a text file
- Configurable length, count, and delay between checks

## Requirements

- Python 3.7 or higher
- An internet connection (no installs needed — uses only built-in libraries)

## Usage

Run with defaults (finds 10 pronounceable 4-5 letter domains):

```bash
python dmfind.py
```

### Options

| Flag | Description | Default |
|------|-------------|---------|
| `--count` | How many available domains to find before stopping | `10` |
| `--mode` | `pronounceable`, `random-letters`, or `words` | `pronounceable` |
| `--length` | Domain length in letters (e.g. `4`, `5`, or `4-5`) — used in `pronounceable`/`random-letters` modes | `4-5` |
| `--words` | Number of words per domain (e.g. `4`, `5`, or `4-5`) — used in `words` mode | `4-5` |
| `--delay` | Seconds to wait between WHOIS lookups | `1.5` |
| `--max-tries` | Safety cap on total candidates checked | `2000` |
| `--output` | File to save results to | `available_domains.txt` |

### Examples

Pure random 4-letter combos:
```bash
python dmfind.py --mode random-letters --length 4
```

Find 20 word-based domains, save to a custom file:
```bash
python dmfind.py --mode words --count 20 --output my_domains.txt
```

Slower, more polite checking (avoids rate limits):
```bash
python dmfind.py --delay 3
```

## How it works

1. Generates a candidate domain name based on the selected mode
2. Sends a WHOIS query to `whois.verisign-grs.com` (the authoritative `.com` registry)
3. Parses the response for "no match" / "not found" markers to determine availability
4. Available domains are printed live and saved to the output file

## Notes & limitations

- Only checks `.com` domains (other TLDs use different WHOIS servers)
- Short domains (4-5 letters) are heavily registered/parked — expect many "taken" results before finding an available one
- Be mindful of the `--delay` setting; querying too fast may get you rate-limited by the WHOIS server
- Checking availability does not reserve the domain — register it promptly through a registrar once you find one you like

## Disclaimer

This tool is for personal research/discovery purposes. Always verify availability directly with a domain registrar before assuming a name is yours to use.
