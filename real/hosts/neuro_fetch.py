"""REAL1 row 9 data fetch (run on the laptop; DANDI is not reachable from the build machine).

Dataset (exact): DANDI:000140 "MC_Maze_Small", Neural Latents Benchmark (Pei et al., NeurIPS Datasets & Benchmarks 2021;
Churchland lab, monkey Jenkins, motor + premotor cortex, Utah arrays, sorted units, delayed-reach maze task). The
training NWB file (path containing "train") is used. Size: a few tens of MB.

Output: an .npz with
  counts : (bins, N) spike counts in 50 ms bins over the whole recording, the N most active units (default 32)
  group  : (N,) channel group per unit (electrode group if the file has it, else 4 equal blocks by unit order)
  unit_ids, bin_s, source
Use: python3 real/hosts/neuro_quick.py <out.npz>   (cells 1..4 = the first four 23 s windows of the recording)
Needs: pip install dandi pynwb
"""
import argparse, os
import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="neuro_mc_maze_small.npz")
    ap.add_argument("--dir", default="dandi_000140")
    ap.add_argument("--n", type=int, default=32)
    ap.add_argument("--bin", type=float, default=0.05)
    a = ap.parse_args()
    from dandi.dandiapi import DandiAPIClient
    from pynwb import NWBHDF5IO
    os.makedirs(a.dir, exist_ok=True)
    with DandiAPIClient() as client:
        ds = client.get_dandiset("000140")
        asset = [x for x in ds.get_assets() if "train" in x.path][0]
        path = os.path.join(a.dir, os.path.basename(asset.path))
        if not os.path.exists(path):
            asset.download(path)
    print("file:", path)
    with NWBHDF5IO(path, "r") as io:
        nwb = io.read(); units = nwb.units
        spikes = [np.asarray(units["spike_times"][i]) for i in range(len(units))]
        cols = units.colnames
        if "electrodes" in cols:
            try:
                grp = [str(units["electrodes"][i]["group_name"].iloc[0]) for i in range(len(units))]
            except Exception:
                grp = None
        else:
            grp = None
    t0 = min(s.min() for s in spikes if len(s)); t1 = max(s.max() for s in spikes if len(s))
    edges = np.arange(t0, t1 + a.bin, a.bin)
    counts = np.stack([np.histogram(s, edges)[0] for s in spikes], 1)
    top = np.sort(np.argsort(-counts.sum(0))[: a.n])
    counts = counts[:, top]
    if grp is not None:
        names = sorted(set(grp[i] for i in top)); group = np.array([names.index(grp[i]) for i in top])
    else:
        group = np.arange(len(top)) * 4 // len(top)
    np.savez_compressed(a.out, counts=counts.astype(np.int32), group=group, unit_ids=top, bin_s=a.bin,
                        source="DANDI:000140 MC_Maze_Small (Neural Latents Benchmark), " + os.path.basename(path))
    print(f"saved {a.out}: {counts.shape[0]} bins x {counts.shape[1]} units, "
          f"mean rate {counts.mean() / a.bin:.1f} Hz, {counts.shape[0] // 460} windows of 460 bins")


if __name__ == "__main__":
    main()
