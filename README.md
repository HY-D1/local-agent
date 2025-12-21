# local-agent (v0.1.0)

A small terminal coding assistant that runs locally using **Ollama**.
It can:
- answer repo-aware questions (`ask`)
- run an interactive chat (`chat`)
- edit a single file safely (`edit`)

## Requirements
- Python 3.10+
- Ollama installed + running

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
