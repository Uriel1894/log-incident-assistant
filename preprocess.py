import sys, re
from collections import Counter

def mask_ips(text):
    return re.sub(r"\b\d{1,3}(\.\d{1,3}){3}\b", "x.x.x.x", text)

if len(sys.argv) != 2:
    print("Usage: python3 preprocess.py <logfile>",file=sys.stderr)
    sys.exit(2)

requests_number = 0
code_number = Counter()
client_set = set()
url_errors = Counter()
error_times = []
sample_lines = []

try:
    with open(sys.argv[1]) as f:
        for line in f:
            parts = line.split()
            if len(parts) < 9:
                continue
            requests_number += 1
            http_code = parts[8]
            code_number[http_code[0] + "xx"] += 1
            if http_code[0] == "5":
                url_errors[parts[6]] += 1
                client_set.add(parts[0])
                error_times.append(parts[3].lstrip("["))
                sample_lines.append(line.strip())
except FileNotFoundError:
    print(f"File not found: {sys.argv[1]}",file=sys.stderr)
    sys.exit(1)

print(f"Total requests: {requests_number}")
print(f"Status: 2xx={code_number['2xx']}, 4xx={code_number['4xx']}, 5xx={code_number['5xx']}")
if error_times:
    print(f"5xx window: {error_times[0]} -> {error_times[-1]}")
else:
    print("5xx window: none")
print("Top URLs with 5xx:")
for url, count in url_errors.most_common(5):
    print(f"  {url} {count}")
print(f"Distinct clients affected: {len(client_set)}")
print("Sample error lines:")
for sample in sample_lines[:3]:
    print("  " + mask_ips(sample))