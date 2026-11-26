# REAL1 row 2 (ai_ai): run on the laptop (PowerShell)

Two real models over OpenRouter: A = `openrouter:openai/gpt-oss-20b`, B = `openrouter:meta-llama/llama-3.1-8b-instruct`.
Forks never call a model; each episode makes at most 2 calls per round x 6 rounds = 12 calls (about 300-600 tokens
each). The quick test (4 cells x 2 modes) is at most 96 calls: well under $0.05.

## Setup (once)
```powershell
cd <your clone of RSOS-Multimodal-World>
git pull
pip install requests numpy
$k = Read-Host -AsSecureString "OpenRouter key"; $env:OPENROUTER_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($k))
$env:REASONING_EFFORT = "low"   # gpt-oss: keeps hidden reasoning from using the whole reply budget (phase 1 finding)
```
The key lives only in this PowerShell window. Never paste it into a chat or a file.

## Dry run (no key, seconds)
```powershell
cd real/hosts
python ai_ai_quick.py mock:0,mock:0
```

## Quick test on the real models (development cells 1..4)
```powershell
cd real/hosts
$env:REAL1_AIAI_MODELS = "openrouter:openai/gpt-oss-20b,openrouter:meta-llama/llama-3.1-8b-instruct"
python ai_ai_quick.py | Tee-Object -FilePath ai_ai_quick_laptop.txt
```
(or pass the models as the first argument: `python ai_ai_quick.py openrouter:openai/gpt-oss-20b,openrouter:meta-llama/llama-3.1-8b-instruct`)

Send `ai_ai_quick_laptop.txt` back (commit it or paste it). If a model id is refused, check https://openrouter.ai/models
and send the current id; do not change anything else.

The confirmatory run uses the cells and commands of the combined seal, not these.
