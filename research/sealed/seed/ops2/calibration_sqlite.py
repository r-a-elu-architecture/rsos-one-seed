import sqlite3, time, random, sys, os, multiprocessing as mp
path="/tmp/sqlcal/db2.sqlite"
def writer(seed, sleep, stop):
    r=random.Random(seed); w=sqlite3.connect(path,timeout=5,isolation_level=None); w.execute("PRAGMA synchronous=OFF")
    while not stop.is_set():
        try:
            w.execute("BEGIN IMMEDIATE"); w.execute("update kv set v=? where k=?",(str(r.random()),f"k{r.randrange(300)}")); w.execute("COMMIT")
        except sqlite3.OperationalError:
            try: w.execute("ROLLBACK")
            except: pass
        time.sleep(sleep)
if __name__=="__main__":
    if os.path.exists(path): os.remove(path)
    c=sqlite3.connect(path); c.execute("PRAGMA journal_mode=DELETE"); c.execute("create table kv(k text primary key, v text)")
    c.executemany("insert into kv values(?,?)",[(f"k{i}",str(i)) for i in range(300)]); c.commit(); c.close()
    sleep=float(sys.argv[1]); nw=int(sys.argv[2]); stop=mp.Event()
    ps=[mp.Process(target=writer,args=(i,sleep,stop)) for i in range(nw)]; [p.start() for p in ps]; time.sleep(0.5)
    rd=sqlite3.connect(path,timeout=0,isolation_level=None); fail=0; N=5000
    for i in range(N):
        try: rd.execute("select v from kv where k=?",(f"k{i%300}",)).fetchone()
        except sqlite3.OperationalError: fail+=1
    stop.set(); [p.join() for p in ps]; print(sleep, nw, fail/N)
