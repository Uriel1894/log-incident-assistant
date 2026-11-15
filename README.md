# Log Incident Assistant

A small Python tool that turns an NGINX access log into a **draft incident report**, using a **local LLM** (Ollama, llama3.1:8b).

The code does the reliable part (counting, masking personal data), the LLM does the interpretation (probable causes, diagnostic commands), and an engineer reviews the result.

## How it works

```
access.log -> preprocess.py -> summary (counts, masked IPs) -> local LLM -> report.md
```

1. `preprocess.py` reads the log and builds a short summary: status codes (2xx/4xx/5xx and exact 5xx codes), incident window, most affected URLs, number of clients affected, and 3 sample error lines with IP addresses masked.
2. `incident_assistant.py` sends this summary to the LLM with a system prompt that forces a fixed structure and forbids inventing facts.
3. The analysis is written to `report.md`, with a warning that it is a draft to be reviewed.

## Design choices

- **Local LLM**: logs never leave the machine. The model runs on CPU and answers in under 30 seconds.
- **Summary instead of raw logs**: a real log can have millions of lines; only a compact summary is sent, and the numbers come from code, not from the model.
- **IP masking**: client IP addresses are personal data, so they are replaced with `x.x.x.x` before anything reaches the LLM.
- **OpenAI-compatible API**: switching to a hosted endpoint (e.g. OVHcloud AI Endpoints) only means changing `base_url` and `api_key`.
- **Clear errors**: wrong usage exits with code 2, missing file or unreachable Ollama exits with code 1 and a readable message.

## Requirements

- Python 3
- [Ollama](https://ollama.com) with the `llama3.1:8b` model

## Usage

```bash
ollama pull llama3.1:8b
python3 -m venv .venv
source .venv/bin/activate
pip install openai

python3 preprocess.py samples/access.log           # summary only
python3 incident_assistant.py samples/access.log   # full report in report.md
```

`samples/access.log` contains a simulated incident: 502 and 504 errors on `/api/orders` and `/api/payment` over about 2.5 minutes.

## Example output (excerpt)

```
## Probable causes (with a confidence level: low, medium or high)
* High: NGINX upstream server or proxy is not responding (502 errors)
* Medium: NGINX upstream server or proxy is experiencing high latency (504 errors)
* Low: No other probable causes can be determined from the provided log summary
```

## Limitations observed

I tested the tool on the sample log and compared reports between versions and runs.

- **Input quality matters more than model settings.** The first version only gave the model "5xx" counts. It suggested an unsupported cause ("high volume of requests", for 19 requests) and cited Apache logs. Adding the exact codes (502/504) and the NGINX context made it identify the upstream server as the most likely cause.
- **Reports are not fully reproducible.** Without `temperature=0` the report changed on every run. With `temperature=0` and `seed=42`, consecutive runs are identical, but the first run after a pause can produce a different version. My hypothesis is Ollama's prompt cache, not confirmed.
- **The two versions do not have the same quality.** One distinguishes 502 from 504 correctly; the other suggests a `tcpdump` command with invalid options (`-W` and `-G` without `-w`) and outdated tools (`netstat` instead of `ss`).
- **Conclusion: a single answer cannot be trusted.** This is why every report starts with a "to be reviewed by an engineer" warning.

## Next steps

- Connect it to my [Terraform and Ansible project](https://github.com/Uriel1894/terraform-ansible-nginx-lab): an Ansible playbook fetches the NGINX logs from the EC2 instance, then the assistant analyses them.
- Add the NGINX error log to the summary, so the model sees why the upstream failed.
- Test the same code against a hosted endpoint (OVHcloud AI Endpoints) and compare quality and speed.

## Licence

MIT