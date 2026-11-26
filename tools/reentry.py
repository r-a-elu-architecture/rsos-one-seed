import json,sys,re
d=json.load(open(sys.argv[1],encoding='utf-8'))
msgs=d['messages']
def toks(s): return re.findall(r"\w+",s.lower())
N=int(sys.argv[2]) if len(sys.argv)>2 else 8
prev_asst=[]  # list of (turn, set of ngrams)
rows=[]
for m in msgs:
    t=toks(m['text'])
    if m['role']=='assistant':
        g=set(tuple(t[i:i+N]) for i in range(len(t)-N+1)); prev_asst.append((m['turn'],g)); continue
    if not prev_asst: continue
    ug=[tuple(t[i:i+N]) for i in range(len(t)-N+1)]
    # coverage: fraction of user tokens inside an N-gram matching any previous assistant msg; source turn of best match
    best=None; cov=[False]*len(t)
    hits={}
    for i,g in enumerate(ug):
        for (at,ag) in reversed(prev_asst):
            if g in ag:
                for k in range(i,i+N): cov[k]=True
                hits[at]=hits.get(at,0)+1; break
    c=sum(cov); 
    if c:
        src=max(hits,key=hits.get); lag=m['turn']-src
        rows.append((m['turn'],len(t),c,round(c/len(t),3),src,lag))
    else: rows.append((m['turn'],len(t),0,0.0,None,None))
ut=[r for r in rows]
re_=[r for r in rows if r[2]>0]
print("user msgs",len(ut),"with >=%d-gram re-entry"%N,len(re_))
print("turn,len,reentered_tokens,share,source_turn,lag")
for r in re_: print(*r,sep=",")
tot=sum(r[1] for r in ut); ren=sum(r[2] for r in ut)
print("token share re-entered overall",round(ren/tot,4))
from collections import Counter
print("lag dist",Counter(r[5] for r in re_))
