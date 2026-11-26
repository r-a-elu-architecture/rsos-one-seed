import json,sys,re,random
d=json.load(open(sys.argv[1],encoding='utf-8')); N=8
drafts=set(map(int,sys.argv[2].split(','))) if len(sys.argv)>2 else {6,69,76,78,81,83,88,98,104,16,17,23,61}  # default = chat 1 drafts
def toks(s): return re.findall(r"\w+",s.lower())
A={}; U=[]
for m in d['messages']:
    t=toks(m['text'])
    if m['role']=='assistant': A.setdefault(m['turn'],set()).update(tuple(t[i:i+N]) for i in range(len(t)-N+1))
    elif m['turn'] not in drafts: U.append((m['turn'],t))
at=sorted(A)
def hit(t,g): return any(tuple(t[i:i+N]) in g for i in range(len(t)-N+1))
obs=sum(hit(t,A[u-1]) for u,t in U if u-1 in A)
n=sum(1 for u,t in U if u-1 in A)
# control: same user msg vs a LATER assistant reply (cannot have been quoted) at lag +5..+20
random.seed(1); ctrl=[]
for rep in range(200):
    c=0;k=0
    for u,t in U:
        cand=[a for a in at if a>=u+5]
        if not cand: continue
        k+=1; c+=hit(t,A[random.choice(cand)])
    ctrl.append(c/k)
ctrl.sort()
print(f"observed: {obs}/{n} = {obs/n:.1%} quote the immediately preceding reply")
print(f"control (future reply, lag>=5, 200 draws): mean {sum(ctrl)/len(ctrl):.1%}, 95% range {ctrl[4]:.1%}-{ctrl[195]:.1%}")
