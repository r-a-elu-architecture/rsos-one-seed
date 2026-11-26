"""REAL1 row 7 (economics): fetch the real Walmart weekly department sales into real/hosts/data/ (works here and on the
laptop).

Data: Walmart Recruiting "Store Sales Forecasting" (Kaggle), store 1, departments 1, 3, 8, 13, 38, 93, 95, 143 weeks
2010-02-05 .. 2012-10-26, Weekly_Sales in USD. Shipped inside the pip package pytimetk (pytimetk/datasets/
walmart_sales_weekly.csv); fetched from its GitHub source (business-science/pytimetk, master); the same bytes as in the
pytimetk 2.5.3 wheel (sha256 checked below; a mismatch stops the run).
"""
import hashlib, os, sys, urllib.request
URL = ("https://raw.githubusercontent.com/business-science/pytimetk/master/src/pytimetk/datasets/"
       "walmart_sales_weekly.csv")
SHA = "4d7b1a97a1605b07f0c51c39127d2131da01febcba04168ded49f0c1d0747123"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "walmart_sales_weekly.csv")

def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    raw = urllib.request.urlopen(URL, timeout=60).read()
    h = hashlib.sha256(raw).hexdigest()
    if h != SHA: sys.exit(f"sha256 mismatch: {h}")
    open(OUT, "wb").write(raw); print("ok", OUT, h)

if __name__ == "__main__": main()
