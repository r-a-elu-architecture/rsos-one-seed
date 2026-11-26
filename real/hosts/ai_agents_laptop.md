# REAL1 rows 1 and 3 on the laptop (PowerShell, OpenRouter)

Key: the OpenRouter key `rsos-seed-test` (credit limit $20). Typed hidden, lives only in this PowerShell window, never in a
file or a chat.

## Setup (once)
```powershell
cd <your clone of RSOS-Multimodal-World>
git pull
pip install requests numpy
$k = Read-Host -AsSecureString "OpenRouter key"; $env:OPENROUTER_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringAuto([Runtime.InteropServices.Marshal]::SecureStringToBSTR($k))
```

## Check without a key (seconds; must print 16 lines for row 1 and 8 for row 3)
```powershell
python real/hosts/ai_agents_quick.py
python real/hosts/ai_human_fetch.py
python real/hosts/ai_human_quick.py
```

## Row 1, ai_agents (ReAct and self-consistency, tasks staff/orders on new seeds)
```powershell
python real/hosts/ai_agents_quick.py openrouter:meta-llama/llama-3.1-8b-instruct | Tee-Object real/hosts/ai_agents_quick_llama8b.txt
python real/hosts/ai_agents_quick.py openrouter:openai/gpt-oss-20b              | Tee-Object real/hosts/ai_agents_quick_gptoss20b.txt
```
Size: 4 cells x 2 standards (react, selfcons) x 2 modes (seed, default) = 16 episodes of 4 tasks per model. From phase 3
(react ~4,150 tokens per task, selfcons ~9,300) about 0.5 M tokens per model, plus the seed's forecast calls (one short call
per task, one more per branch every 4 calls). At current OpenRouter prices for these two models this is cents; check
https://openrouter.ai/models before the run. Wall time: roughly 5-20 minutes per model (sequential calls).
Note: gpt-oss may spend the 300-token forecast reply on hidden reasoning and return nothing; the host then uses the
fallback forecast (4 calls, confidence 0.87) and still charges the tokens.

## Row 3, ai_human (Topical-Chat, reply under a 48-token budget)
```powershell
python real/hosts/ai_human_fetch.py
python real/hosts/ai_human_quick.py openrouter:meta-llama/llama-3.1-8b-instruct      | Tee-Object real/hosts/ai_human_quick_llama8b.txt
python real/hosts/ai_human_quick.py openrouter:mistralai/mistral-small-3.2-24b-instruct | Tee-Object real/hosts/ai_human_quick_mistral.txt
```
Size: 4 cells x 2 modes x 8 short replies = 64 calls per model (~40k tokens). Do not use reasoning models (gpt-oss) for
row 3: hidden reasoning would consume the 48-token reply budget and give empty replies.

If a model id is refused, open https://openrouter.ai/models, find the current id, and send it; do not change anything else.
Then commit and push the four `*_quick_*.txt` files. Delete or disable the key after the confirmatory run.
