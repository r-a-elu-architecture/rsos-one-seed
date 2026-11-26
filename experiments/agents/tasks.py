"""Task families with exact answers.
A 'warehouse' (structure selection only): multi-step stock arithmetic, tool calc.
C 'orders' (selection family of phase 1b, added 22 Nov after phase 1 hit the ceiling): hidden 30-order ledger, tools orders_where/order_details/calc (renamed 22 Nov 12:15: find/get collided with gpt-oss's built-in browser tool).
B 'staff' (held out): questions over a hidden 24-person table reachable only through tools (filter, lookup, calc).
P 'gsm8k' (public anchor): GSM8K test problems (downloaded on the laptop on first use), tool calc.
A and B are generated from a seed, so the tasks did not exist before the run (no contamination possible)."""
import ast, operator, random, json, os, re, collections
import urllib.request

OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
       ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod, ast.Pow: operator.pow, ast.USub: operator.neg, ast.UAdd: operator.pos}

def calc(expr):
    def ev(n):
        if isinstance(n, ast.Expression): return ev(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)): return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in OPS:
            a, b = ev(n.left), ev(n.right)
            if isinstance(n.op, ast.Pow) and abs(b) > 10: raise ValueError("exponent too large")
            return OPS[type(n.op)](a, b)
        if isinstance(n, ast.UnaryOp) and type(n.op) in OPS: return OPS[type(n.op)](ev(n.operand))
        raise ValueError("only numbers and + - * / // % ** ( )")
    v = ev(ast.parse(expr.replace(",", ""), mode="eval")); return int(v) if float(v).is_integer() else round(v, 6)

def warehouse(seed):
    r = random.Random(seed); s = r.randint(200, 900) * 2; lines = [f"A warehouse starts the week with {s} units."]
    for _ in range(r.randint(5, 7)):
        k = r.choice(["recv", "ship", "dmg", "ret", "split"])
        if k == "recv": a, b = r.randint(3, 19), r.randint(12, 48); s += a * b; lines.append(f"It receives {a} crates of {b} units each.")
        elif k == "ship": c = r.randint(40, max(41, s // 3)); s -= c; lines.append(f"It ships {c} units.")
        elif k == "dmg": d = r.randint(2, 30); s -= d; lines.append(f"{d} units are damaged and thrown away.")
        elif k == "ret": e = r.randint(5, 60); s += e; lines.append(f"Customers return {e} units.")
        else:
            f = r.choice([d for d in (2, 3, 4, 5, 6, 8) if s % d == 0] or [1])
            if f == 1: continue
            s -= s // f; lines.append(f"It transfers exactly 1/{f} of its current stock to a branch.")
    return {"id": f"A{seed}", "family": "warehouse", "question": " ".join(lines) + " How many units does it hold at the end?",
            "answer": s, "tools": ["calc"]}

NAMES = ["Ada", "Bo", "Cyra", "Dan", "Eli", "Fay", "Gus", "Hana", "Ivo", "Juna", "Kai", "Lior", "Mira", "Nils", "Oona", "Pavel",
         "Quin", "Rhea", "Sven", "Tala", "Uma", "Vik", "Wren", "Yusuf"]
DEPTS, CITIES = ["Sales", "Ops", "Research", "Finance", "Legal"], ["Lyon", "Oslo", "Porto", "Riga"]

def staff(seed):
    r = random.Random(seed); T = {n: {"dept": r.choice(DEPTS), "city": r.choice(CITIES), "salary": r.randrange(3000, 9000, 50),
                                      "years": r.randint(1, 20)} for n in NAMES}
    q = r.choice(["sum", "max", "count", "avg"]); d, c = r.choice(DEPTS), r.choice(CITIES)
    if q == "sum":
        y = r.randint(3, 12); ans = sum(v["salary"] for v in T.values() if v["dept"] == d and v["years"] > y)
        text = f"What is the total salary of all {d} employees with more than {y} years of service?"
    elif q == "max":
        pool = {n: v for n, v in T.items() if v["city"] == c} or T; m = max(v["salary"] for v in pool.values())
        ties = [n for n, v in pool.items() if v["salary"] == m]; ans = sorted(ties)[0]
        text = f"Who is the highest-paid employee in {c}? If several are tied, give the name that comes first alphabetically."
    elif q == "count":
        s = r.randrange(4000, 8000, 500); ans = sum(1 for v in T.values() if v["dept"] == d and v["city"] == c and v["salary"] > s)
        text = f"How many {d} employees in {c} earn more than {s}?"
    else:
        pool = [v["years"] for v in T.values() if v["dept"] == d] or [0]; ans = sum(pool) // len(pool)
        text = f"What is the average years of service of {d} employees, rounded down to a whole number?"
    return {"id": f"B{seed}", "family": "staff", "question": text, "answer": ans, "table": T, "tools": ["filter", "lookup", "calc"]}

PRODUCTS, STATUS = ["lamp", "desk", "chair", "shelf", "rug"], ["shipped", "pending", "refunded"]

def orders(seed):
    """Family C (selection family for phase 1b, 22 Nov): a hidden ledger of 30 orders reachable only through tools.
    The tool orders_where() takes ONE condition, so every question needs several finds, an intersection, records and arithmetic."""
    r = random.Random(seed); cust = {n: r.choice(CITIES) for n in r.sample(NAMES, 10)}
    T = {}
    for i in range(1, 31):
        c = r.choice(sorted(cust)); T[f"O{i:02d}"] = {"customer": c, "city": cust[c], "product": r.choice(PRODUCTS),
            "qty": r.randint(1, 20), "price": r.randrange(5, 205, 5), "status": r.choices(STATUS, [6, 2, 2])[0]}
    val = lambda o: o["qty"] * o["price"]; q = r.choice(["city_value", "top_customer", "net", "refund_units"])
    for _ in range(100):  # pick product and city so the answer is not 0 (a guessed 0 must not score)
        p, c = r.choice(PRODUCTS), r.choice(sorted(set(cust.values())))
        if q == "city_value" and any(o["status"] == "shipped" and o["product"] == p and o["city"] == c for o in T.values()): break
        if q == "refund_units" and any(o["status"] == "refunded" and o["product"] == p and o["city"] == c for o in T.values()): break
        if q == "net" and any(o["product"] == p and o["status"] == "refunded" for o in T.values()): break
        if q == "top_customer": break
    if q == "city_value":
        ans = sum(val(o) for o in T.values() if o["status"] == "shipped" and o["product"] == p and o["city"] == c)
        text = f"What is the total value (quantity times unit price) of all shipped {p} orders from customers in {c}?"
    elif q == "top_customer":
        tot = collections.Counter()
        for o in T.values():
            if o["status"] == "shipped": tot[o["customer"]] += val(o)
        m = max(tot.values()); ans = sorted(n for n, v in tot.items() if v == m)[0]
        text = "Which customer has the largest total value (quantity times unit price) of shipped orders? If tied, give the name first in the alphabet."
    elif q == "net":
        ans = sum(val(o) for o in T.values() if o["product"] == p and o["status"] == "shipped") - \
              sum(val(o) for o in T.values() if o["product"] == p and o["status"] == "refunded")
        text = f"For product {p}: what is the value of shipped orders minus the value of refunded orders (value = quantity times unit price)?"
    else:
        ans = sum(o["qty"] for o in T.values() if o["product"] == p and o["status"] == "refunded" and o["city"] == c)
        text = f"How many units of {p} were refunded to customers in {c}?"
    return {"id": f"C{seed}", "family": "orders", "question": text, "answer": ans, "table": T, "tools": ["orders_where", "order_details", "calc"]}

GSM_URL = "https://raw.githubusercontent.com/openai/grade-school-math/master/grade_school_math/data/test.jsonl"
def gsm8k(idx):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gsm8k_test.jsonl")
    if not os.path.exists(path): urllib.request.urlretrieve(GSM_URL, path)
    rows = [json.loads(l) for l in open(path)]; x = rows[idx]
    return {"id": f"P{idx}", "family": "gsm8k", "question": x["question"], "answer": int(x["answer"].split("####")[-1].strip().replace(",", "")), "tools": ["calc"]}

def run_tool(task, name, args):
    if name not in task["tools"]: return f"error: tool {name} not available (tools: {', '.join(task['tools'])})"
    try:
        if name == "calc": return str(calc(args))
        T = task["table"]
        if name == "orders_where":
            m = re.match(r"\s*(\w+)\s*=\s*['\"]?([\w ]+?)['\"]?\s*$", args)
            fields = ("customer", "city", "product", "status")
            if not m or m.group(1) not in fields: return "error: use orders_where(field=value) with ONE condition, field in " + ", ".join(fields)
            return ", ".join(k for k, row in T.items() if str(row[m.group(1)]).lower() == m.group(2).lower()) or "(none)"
        if name == "order_details":
            ids = [a.strip().strip("'\"") for a in args.split(",") if a.strip()]
            if len(ids) > 10: return "error: at most 10 ids per order_details call"
            return "\n".join(f"{k}: {json.dumps(T[k])}" if k in T else f"{k}: not found" for k in ids)
        if name == "lookup":
            out = []
            for n in [a.strip().strip("'\"") for a in args.split(",") if a.strip()]:
                out.append(f"{n}: {json.dumps(T[n])}" if n in T else f"{n}: not found")
            return "\n".join(out)
        if name == "filter":
            m = re.match(r"\s*(\w+)\s*=\s*['\"]?([\w ]+?)['\"]?\s*$", args)
            if not m: return "error: use filter(field=value), field in dept, city"
            f, v = m.group(1), m.group(2)
            if f not in ("dept", "city"): return "error: filter field must be dept or city"
            return ", ".join(n for n, row in T.items() if str(row[f]).lower() == v.lower()) or "(none)"
    except Exception as e:
        return f"error: {e}"

TOOL_HELP = {"calc": "calc(expression): exact arithmetic, e.g. calc(12*37-5)",
             "filter": "filter(field=value): names whose dept or city equals value, e.g. filter(dept=Sales)",
             "lookup": "lookup(name1, name2, ...): the records (dept, city, salary, years) of those people",
             "orders_where": "orders_where(field=value): ids of orders matching ONE condition; field is customer, city, product or status, e.g. orders_where(product=lamp)",
             "order_details": "order_details(id1, id2, ...): the records (customer, city, product, qty, price, status) of up to 10 orders, e.g. order_details(O03, O17)"}

def correct(task, given):
    if given is None: return False
    g = str(given).strip().rstrip(".").replace(",", "")
    if isinstance(task["answer"], int):
        try: return abs(float(re.findall(r"-?\d+(?:\.\d+)?", g)[0]) - task["answer"]) < 1e-6
        except Exception: return False
    return g.lower() == str(task["answer"]).lower()

def make(family, seeds):
    f = {"warehouse": warehouse, "staff": staff, "orders": orders, "gsm8k": gsm8k}[family]; return [f(s) for s in seeds]
