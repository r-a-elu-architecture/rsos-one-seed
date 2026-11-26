"""REAL1 row 6 (energy): fetch the real household load series into real/hosts/data/ (works here and on the laptop).

Load: UCI "Individual household electric power consumption" (Hebrail & Berard, one household in Sceaux, France),
Global_active_power resampled to hourly sums of the minute kW readings (kWh = value / 60), 1000 hours
2006-12-16 18:00 .. 2007-01-27 09:00. Mirror on GitHub (only GitHub/pip reachable here):
  marcopeix/AppliedTimeSeriesForecastingInPython, branch master, data/household_power_consumption.csv
Solar: no download; pvlib ships the real TMY3 file 723170TYA.CSV (Greensboro, NC) in pvlib/data.
The file is checked against the sha256 below; a mismatch stops the run.
"""
import hashlib, os, sys, urllib.request
URL = ("https://raw.githubusercontent.com/marcopeix/AppliedTimeSeriesForecastingInPython/master/"
       "data/household_power_consumption.csv")
SHA = "7195b2765721906d8a90db861eb8224e6531d3ea22e7657cf9f738b4ff00140a"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "household_load_uci_hourly.csv")

def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    raw = urllib.request.urlopen(URL, timeout=60).read()
    h = hashlib.sha256(raw).hexdigest()
    if h != SHA: sys.exit(f"sha256 mismatch: {h}")
    open(OUT, "wb").write(raw); print("ok", OUT, h)

if __name__ == "__main__": main()
