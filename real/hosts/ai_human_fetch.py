"""Fetch the real human dialogue corpus for row 3 (ai_human): Topical-Chat (Amazon Alexa AI, Gopalakrishnan et al. 2019,
https://github.com/alexa/Topical-Chat), file conversations/test_freq.json: 539 real human-human conversations (crowd
workers chatting about topics; ~21.8 turns each, median 18 words per turn). Reachable here (GitHub raw) and on the laptop.
Licence: see the repository (Topical-Chat is released by Amazon for research; not redistributed in this repo: the file is
fetched to real/hosts/data/ and should stay out of git).
24 Nov (owner: the own future is read from the REAL TREE): also conversations/train.json, the TRAINING split (8628
conversations, disjoint from test_freq: 0 shared ids, checked here). It is used ONLY to estimate the empirical
probabilities of the host's model (ai_human_tree.py); the test conversations used in cells are never read for that.
Usage: python real/hosts/ai_human_fetch.py       (idempotent; verifies the sha256 recorded on 24 Nov 2026)"""
import hashlib, os, sys, urllib.request

URL = "https://raw.githubusercontent.com/alexa/Topical-Chat/master/conversations/test_freq.json"
SHA256 = "3c65693d59e40a1fb58ead35dcfe85fbcc88ea93a4d74557df620996f72c8f08"   # fetched here 24 Nov 2026
PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "topical_chat", "test_freq.json")
TRAIN_URL = "https://raw.githubusercontent.com/alexa/Topical-Chat/master/conversations/train.json"
TRAIN_SHA256 = "39a079d8464ea5f44f0fd78dbc85fd4eed96303347cbf4f9301f823e3c0f437f"   # fetched here 24 Nov 2026 (60.8 MB)
TRAIN_PATH = os.path.join(os.path.dirname(PATH), "train.json")

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

def _get(url, path, want, quiet):
    if os.path.exists(path) and sha(path) == want: return path
    os.makedirs(os.path.dirname(path), exist_ok=True); tmp = path + ".part"
    urllib.request.urlretrieve(url, tmp); h = sha(tmp)
    if h != want:
        os.remove(tmp); raise RuntimeError(f"sha256 mismatch: got {h}, expected {want} (upstream file changed: stop and report)")
    os.replace(tmp, path)
    if not quiet: print("fetched", path, h)
    return path

def fetch(quiet=False): return _get(URL, PATH, SHA256, quiet)

def fetch_train(quiet=False): return _get(TRAIN_URL, TRAIN_PATH, TRAIN_SHA256, quiet)

if __name__ == "__main__":
    p = fetch(); print("ok", p, SHA256)
    p = fetch_train(); print("ok", p, TRAIN_SHA256)
