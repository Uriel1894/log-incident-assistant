"""Summarise an NGINX access log, focusing on 5xx errors.

Can be run on its own or imported by incident_assistant.py.
Usage: python3 preprocess.py <logfile>
"""
import sys, re
from collections import Counter


def mask_ips(text):
    """Replace IPv4 addresses with x.x.x.x so no personal data is sent to the LLM."""
    return re.sub(r"\b\d{1,3}(\.\d{1,3}){3}\b", "x.x.x.x", text)


def summarize(path):
    """Read an NGINX access log and return a short text summary of its 5xx errors."""
    requests_number = 0
    code_number = Counter()
    client_set = set()
    url_errors = Counter()
    error_codes = Counter()
    error_times = []
    sample_lines = []
    with open(path) as f:
        for line in f:
            parts = line.split()
            # Skip malformed or truncated lines: they would raise an IndexError
            if len(parts) < 9:
                continue
            requests_number += 1
            # NGINX "combined" format: [0] client IP, [3] date, [6] URL, [8] status code
            http_code = parts[8]
            code_number[http_code[0] + "xx"] += 1
            if http_code[0] == "5":
                error_codes[http_code] += 1
                url_errors[parts[6]] += 1
                client_set.add(parts[0])
                error_times.append(parts[3].lstrip("["))
                sample_lines.append(line.strip())

    lines = []
    lines.append(f"Total requests: {requests_number}")
    lines.append(f"Status: 2xx={code_number['2xx']}, 4xx={code_number['4xx']}, 5xx={code_number['5xx']}")
    # Exact codes matter: 502 (bad upstream response) and 504 (upstream timeout) point to different causes
    code_parts = []
    for code, count in sorted(error_codes.items()):
        code_parts.append(f"{code}={count}")
    lines.append(f"5xx codes: {', '.join(code_parts)}")
    if error_times:
        lines.append(f"5xx window: {error_times[0]} -> {error_times[-1]}")
    else:
        lines.append("5xx window: none")
    lines.append("Top URLs with 5xx:")
    for url, count in url_errors.most_common(5):
        lines.append(f"  {url} {count}")
    lines.append(f"Distinct clients affected: {len(client_set)}")
    # A few masked examples give the LLM context without sending the whole log
    lines.append("Sample error lines:")
    for sample in sample_lines[:3]:
        lines.append("  " + mask_ips(sample))

    return "\n".join(lines)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 preprocess.py <logfile>", file=sys.stderr)
        sys.exit(2)

    try:
        print(summarize(sys.argv[1]))
    except FileNotFoundError:
        print(f"File not found: {sys.argv[1]}", file=sys.stderr)
        sys.exit(1)