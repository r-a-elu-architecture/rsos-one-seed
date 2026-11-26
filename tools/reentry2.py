import json,sys,re
d=json.load(open(sys.argv[1],encoding='utf-8')); N=8
drafts=set(map(int,sys.argv[2].split(','))) if len(sys.argv)>2 else {6,69,76,78,81,83,88,98,104,16,17,23,61}  # default = chat 1 drafts
msgs=d['messages']
def toks(s): return re.findall(r"\w+",s.lower())
prev=[]; out=[]
for m in msgs:
    t=toks(m['text'])
    if m['role']=='assistant':
        prev.append((m['turn'],t,set(tuple(t[i:i+N]) for i in range(len(t)-N+1)))); continue
    if m['turn'] in drafts or not prev: continue
    cov=[False]*len(t); spans=[]
    i=0
    last=prev[-1]
    while i<=len(t)-N:
        g=tuple(t[i:i+N])
        if g in last[2]:
            j=i+N
            while j<len(t) and tuple(t[j-N+1:j+1]) in last[2]: j+=1
            for k in range(i,j): cov[k]=True
            spans.append(" ".join(t[i:j])); i=j
        else: i+=1
    out.append((m['turn'],len(t),sum(cov),spans))
n=len(out); k=sum(1 for o in out if o[2]); 
print("unique answered user msgs",n,"quoting previous reply (>=8-gram)",k, f"{k/n:.1%}")
mx=max(o[0] for o in out); third=(mx+1)//3
# phases: chat 1 keeps its original split (T0-38, T39-75, T76-108); other chats use equal thirds
phases=[(0,38),(39,75),(76,108)] if mx==108 else [(0,third-1),(third,2*third-1),(2*third,mx)]
for lo,hi in phases:
    name=f"T{lo}-{hi}"
    s=[o for o in out if lo<=o[0]<=hi]; kk=sum(1 for o in s if o[2]); tok=sum(o[1] for o in s); rt=sum(o[2] for o in s)
    if not s: continue
    print(name,"msgs",len(s),"quoting",kk,f"{kk/len(s):.0%}","token share",f"{rt/tok:.1%}")
cav=re.compile(r"\b(not|no|cannot|does not|doesn t|unverified|unproven|not yet|not established|limitation|bottleneck|but|however|only)\b")
c=0; tot=0
for o in out:
    for s in o[3]:
        tot+=1; c+= bool(cav.search(s))
print("quoted spans",tot,"containing hedge/limit words",c)
for o in out:
    if o[3]: print(o[0], "|", o[3][0][:150])
