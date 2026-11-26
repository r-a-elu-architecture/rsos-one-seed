import json,collections,re
last={}
for p in ["phase3_staff.jsonl","phase3_orders.jsonl"]:
    for l in open(p):
        r=json.loads(l); last[(r["model"],r["arm"],r["task"])]=r
T="rsos_01100"; arms=["react","reflexion","selfcons","planexec",T]
keys=sorted({(m,t) for m,a,t in last})
def cls(r):
    tr=r.get("trace") or []
    outs=[x.get("out","") for x in tr]
    acts=[o for o in outs if "ACTION:" in o]
    verd=[o for o in outs if "VERDICT" in o]
    wrongv=[o for o in verd if "WRONG" in o]
    rep=len(acts)-len(set(a.strip() for a in acts))
    noans = r["given"] in (None,"")
    return dict(calls=r["calls"],tok=r["tokens"],nact=len(acts),rep=rep,nver=len(verd),nwrong=len(wrongv),noans=noans,ans_changed=None)
W=[];L=[]
for k in keys:
    a=last[(k[0],T,k[1])]; b=last[(k[0],"react",k[1])]
    if a["correct"] and not b["correct"]: W.append((k,a,b))
    if b["correct"] and not a["correct"]: L.append((k,a,b))
print("wins",len(W),"losses",len(L))
def summ(lst,label):
    c=collections.Counter()
    for k,a,b in lst:
        ca,cb=cls(a),cls(b)
        c["model:"+k[0].split("/")[-1]]+=1; c["fam:"+a["family"]]+=1
        c["rsos_noans" if ca["noans"] else "rsos_answered"]+=1
        c["react_noans" if cb["noans"] else "react_answered"]+=1
        c["rsos_calls>=12" if ca["calls"]>=12 else "rsos_calls<12"]+=1
        c["react_calls>=12" if cb["calls"]>=12 else "react_calls<12"]+=1
        c["rsos_has_repeat" if ca["rep"] else "rsos_norepeat"]+=1
        c["rsos_verdict_wrong>0" if ca["nwrong"] else "rsos_verdict_never_wrong"]+=1
        c["rsos_tok>=16000" if (a["tokens"] or 0)>=15000 else "rsos_tok<15000"]+=1
    print(label); [print("  ",x,v) for x,v in sorted(c.items())]
summ(W,"WINS (rsos right, react wrong)"); summ(L,"LOSSES (react right, rsos wrong)")
print("\n--- mechanism ---")
ANS=re.compile(r"ANSWER:\s*(.+)")
def norm(x): return str(x).strip().rstrip(".").lower().replace(",","")
def first_ans(r):
    for x in r.get("trace") or []:
        o=x.get("out","")
        if "VERDICT" in o: continue
        m=None
        for line in reversed([l for l in o.splitlines() if l.strip()]):
            m=ANS.search(line); 
            if m: break
        if m and "ACTION:" not in o.splitlines()[-1]: return m.group(1)
    return None
def mech(a,b,win):
    ca=cls(a)
    if ca["nwrong"]:
        f=first_ans(a); fc = f is not None and norm(f)==norm(a["answer"])
        if win: return "verify caught wrong first answer -> fixed" if not fc else "verify WRONG but first was right(?)"
        return "verify flipped a RIGHT first answer to wrong/none" if fc else "verify caught wrong, re-plan still wrong/none"
    if ca["noans"]: return "rsos no answer (budget/token exhausted), no WRONG verdict"
    if not win and ca["rep"]: return "same-path drift + repeated actions"
    return "path diverged (same loop, verdict OK) = run-to-run variance"
for lst,w,lab in [(W,True,"WINS"),(L,False,"LOSSES")]:
    c=collections.Counter(mech(a,b,w) for k,a,b in lst); print(lab); [print("  ",v,x) for x,v in c.most_common()]
# no-answer details in losses
na=[a for k,a,b in L if cls(a)["noans"]]
print("loss no-ans: calls>=12",sum(a["calls"]>=12 for a in na),"tok>=15000",sum((a["tokens"] or 0)>=15000 for a in na),
 "with repeats",sum(cls(a)["rep"]>0 for a in na))
# overall noans rate per arm
for arm in arms:
    rs=[last[(m,arm,t)] for m,t in keys]; print(arm,"noans",sum(r["given"] in (None,"") for r in rs),"of",len(rs))
print("\n--- verdict-OK discordant: where do paths split? ---")
def acts(r): return [x.get("out","").strip().splitlines()[-1] if x.get("out","").strip() else "" for x in (r.get("trace") or []) if "VERDICT" not in x.get("out","")]
for lst,w,lab in [(W,True,"WINS"),(L,False,"LOSSES")]:
    c=collections.Counter()
    for k,a,b in lst:
        if mech(a,b,w).startswith("path"):
            A,B=acts(a),acts(b); i=0
            while i<min(len(A),len(B)) and A[i]==B[i]: i+=1
            c["split at step %d"%i if i<3 else "split at step 3+"]+=1
            c["react_noans" if b["given"] in (None,"") else "react_wrong_answer"]+=1
    print(lab,dict(c))
print("\n--- fallback: rsos had an answer earlier but ended with none ---")
TRUTH={}
for k,a,b in L:
    if a["given"] in (None,""):
        fa=first_ans(a); 
        if fa: print(k, "first:",fa,"truth:",a["answer"], "match", norm(fa)==norm(a["answer"]))
n=0
for m,t in keys:
    a=last[(m,T,t)]
    if a["given"] in (None,"") and first_ans(a): n+=1
print("all rsos rows with an earlier answer but final none:",n)
