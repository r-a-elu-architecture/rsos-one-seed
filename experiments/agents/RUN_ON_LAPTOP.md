# Agents test: run on your laptop (PowerShell)

## Setup (once, ~10 minutes)
```powershell
cd <your clone of RSOS-Multimodal-World>
git pull
cd experiments/agents
pip install requests scipy
```
Keys: one per provider you use, typed hidden, never pasted into a chat or a file:
```powershell
$k = Read-Host -AsSecureString "OpenAI key";    $env:OPENAI_API_KEY    = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($k))
$k = Read-Host -AsSecureString "Gemini key";    $env:GEMINI_API_KEY    = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($k))
$k = Read-Host -AsSecureString "Anthropic key"; $env:ANTHROPIC_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($k))
```
The keys live only in this PowerShell window and disappear when it closes. Delete the keys at the providers after the run.

### Chosen route (owner, 22 Nov 10:40): open models on Groq
1. Sign up at https://console.groq.com, add billing, set a spending limit of $20 (Settings, Billing, Limits).
2. Create an API key (API Keys, Create). Copy it once, never into a chat or a file.
3. In PowerShell:
```powershell
$k = Read-Host -AsSecureString "Groq key"; $env:GROQ_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($k))
```
4. Smoke run (2 tasks, a few cents at most). Check that every model answers:
```powershell
python run.py --models groq:llama-3.1-8b-instant,groq:llama-3.3-70b-versatile,groq:openai/gpt-oss-120b,groq:qwen/qwen3-32b --family staff --seeds 1-2 --arms plain,rsos_11011 --out smoke.jsonl
```
If a model name is refused, open https://console.groq.com/docs/models and send me the current names.

## Dry run (no keys, 1 minute)
```powershell
python run.py --models mock:0 --family staff --seeds 1-3 --arms all --out dry.jsonl
```

## Phase 1: find the structure (one cheap model, about 1-2 hours)
On Groq, MODEL = groq:llama-3.1-8b-instant (about $1 for the whole phase):
```powershell
python run.py --models MODEL --family warehouse --seeds 1000-1099 --arms all --out phase1.jsonl
python select_structure.py phase1.jsonl
```
Commit and push phase1.jsonl and PHASE1_DECISION.json. If it says STOP, we stop and rethink. If CONTINUE, I seal
phase 3 with the chosen structure before you start it.

## Phase 3: confirmatory (only after the seal)
The exact commands (models, seeds, arms) are in the sealed PREREG_AGENTS.md. Do not change anything in them.
