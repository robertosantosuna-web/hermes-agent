#!/usr/bin/env python3
"""Refined FVG analysis: combined time + gap filters, more detail."""
import json
from collections import defaultdict, Counter

with open("/home/roberto/.hermes/forex/simulations/hermes_eurusd_analysis.json") as f:
    eurusd = json.load(f)
with open("/home/roberto/.hermes/forex/simulations/brain_gbpusd_analysis.json") as f:
    gbpusd = json.load(f)

all_results = eurusd["all_results"] + gbpusd["all_results"]
fvg_results = [r for r in all_results 
               if r.get("pattern_type","") in ("BULLISH_FVG", "BEARISH_FVG")
               and r.get("outcome","") in ("WIN", "LOSS")]

wins = [r for r in fvg_results if r["outcome"] == "WIN"]
losses = [r for r in fvg_results if r["outcome"] == "LOSS"]

# Helper
def get_hour(r):
    ts = r.get("timestamp","")
    try: return int(ts.split(" ")[1].split(":")[0])
    except: return None

print("=" * 70)
print("ANALYSIS 1: Gap size vs SL relationship check")
print("=" * 70)
same = sum(1 for r in fvg_results if r["gap_size_pips"] == r["sl_pips"])
diff = sum(1 for r in fvg_results if r["gap_size_pips"] != r["sl_pips"])
print(f"gap == sl_pips: {same}/{len(fvg_results)} ({same/len(fvg_results)*100:.1f}%)")
print(f"gap != sl_pips: {diff}/{len(fvg_results)} ({diff/len(fvg_results)*100:.1f}%)")

# Check strength values for FVG
strengths_fvg = [r.get("strength", "N/A") for r in fvg_results]
print(f"\nStrength values in FVG: {set(strengths_fvg)}")
# Check non-FVG for comparison
non_fvg = [r for r in all_results if "BOS" in r.get("pattern_type","") and r.get("outcome") in ("WIN","LOSS")]
non_fvg_strengths = [r.get("strength", "N/A") for r in non_fvg[:20]]
print(f"Sample BOS strengths: {non_fvg_strengths}")

print("\n" + "=" * 70)
print("ANALYSIS 2: Gap size distribution detail (1-pip buckets)")
print("=" * 70)
gap_buckets = defaultdict(lambda: {"win": 0, "loss": 0})
for r in wins:
    gap_buckets[int(r["gap_size_pips"])]["win"] += 1
for r in losses:
    gap_buckets[int(r["gap_size_pips"])]["loss"] += 1

print(f"{'Gap':>5} {'Wins':>5} {'Losses':>5} {'Total':>5} {'WR%':>7} {'CumW%':>7}")
print("-" * 40)
for g in sorted(gap_buckets.keys()):
    w = gap_buckets[g]["win"]
    l = gap_buckets[g]["loss"]
    t = w + l
    wr = w/t*100 if t>0 else 0
    # Cumulative from this gap up
    cw = sum(gap_buckets[x]["win"] for x in sorted(gap_buckets.keys()) if x >= g)
    cl = sum(gap_buckets[x]["loss"] for x in sorted(gap_buckets.keys()) if x >= g)
    cwr = cw/(cw+cl)*100 if (cw+cl)>0 else 0
    print(f"{g:>5} {w:>5} {l:>5} {t:>5} {wr:>6.1f}% {cwr:>6.1f}%")

print("\n" + "=" * 70)
print("ANALYSIS 3: Hourly WR x Gap threshold combined")
print("=" * 70)

for gap_min in [0, 5, 10]:
    print(f"\n--- For gap >= {gap_min} ---")
    print(f"{'Hour':>5} {'Wins':>5} {'Loss':>5} {'Tot':>5} {'WR%':>7}")
    hour_wr = {}
    for h in range(24):
        hw = sum(1 for r in wins if get_hour(r)==h and r["gap_size_pips"]>=gap_min)
        hl = sum(1 for r in losses if get_hour(r)==h and r["gap_size_pips"]>=gap_min)
        ht = hw+hl
        wr = hw/ht*100 if ht>0 else 0
        if ht > 0:
            print(f"{h:>5} {hw:>5} {hl:>5} {ht:>5} {wr:>6.1f}%")
            hour_wr[h] = wr

    # Best hours
    if hour_wr:
        best = sorted(hour_wr.items(), key=lambda x: x[1], reverse=True)[:5]
        print(f"  Top 5 hours: {best}")

print("\n" + "=" * 70)
print("ANALYSIS 4: Session + Gap combined filter")
print("=" * 70)

session_hours = {
    "Asian (0-6)": range(0, 7),
    "London AM (7-9)": range(7, 10),
    "London PM (10-12)": range(10, 13),
    "NY AM (12-14)": range(12, 15),
    "NY PM (15-17)": range(15, 18),
    "Evening (18-23)": range(18, 24)
}

print(f"{'Filter':<40} {'Wins':>5} {'Loss':>5} {'Tot':>5} {'WR%':>7}")
print("-" * 65)

for sname, hours in session_hours.items():
    for gap_min in [0, 5, 10]:
        w = sum(1 for r in wins 
                if get_hour(r) in hours and r["gap_size_pips"] >= gap_min)
        l = sum(1 for r in losses 
                if get_hour(r) in hours and r["gap_size_pips"] >= gap_min)
        t = w + l
        wr = w/t*100 if t>0 else 0
        label = f"{sname} + gap>={gap_min}"
        print(f"{label:<40} {w:>5} {l:>5} {t:>5} {wr:>6.1f}%")

print("\n" + "=" * 70)
print("ANALYSIS 5: Best hour ranges + gap combined")
print("=" * 70)

# Try specific hour ranges
hour_ranges = [
    ("6-9 (London open)", range(6, 10)),
    ("7-9 (London AM)", range(7, 10)),
    ("7-16 (London+NY)", range(7, 17)),
    ("7-17 (full trading)", range(7, 18)),
    ("12-17 (NY)", range(12, 18)),
    ("15-17 (NY PM)", range(15, 18)),
    ("6-8", range(6, 9)),
    ("6-17", range(6, 18)),
    ("9-16", range(9, 17)),
    ("NOT 18-23 (no evening)", lambda h: h is not None and h < 18),
    ("NOT 20-23 (no late)", lambda h: h is not None and not (20 <= h <= 23)),
]

print(f"{'Filter':<45} {'Wins':>5} {'Loss':>5} {'Tot':>5} {'WR%':>7}")
print("-" * 70)

for label, hours in hour_ranges:
    for gap_min in [0, 5, 10]:
        if callable(hours):
            pred = hours
        else:
            pred = lambda h, hrs=hours: h in hrs
        w = sum(1 for r in wins 
                if pred(get_hour(r)) and r["gap_size_pips"] >= gap_min)
        l = sum(1 for r in losses 
                if pred(get_hour(r)) and r["gap_size_pips"] >= gap_min)
        t = w + l
        wr = w/t*100 if t>0 else 0
        full_label = f"{label} + gap>={gap_min}"
        print(f"{full_label:<45} {w:>5} {l:>5} {t:>5} {wr:>6.1f}%")

print("\n" + "=" * 70)
print("ANALYSIS 6: Direction + gap combined")
print("=" * 70)

for direction in ["BULLISH_FVG", "BEARISH_FVG"]:
    for gap_min in [0, 5, 10, 15]:
        w = sum(1 for r in wins 
                if r["pattern_type"]==direction and r["gap_size_pips"]>=gap_min)
        l = sum(1 for r in losses 
                if r["pattern_type"]==direction and r["gap_size_pips"]>=gap_min)
        t = w + l
        wr = w/t*100 if t>0 else 0
        print(f"  {direction:<15} + gap>={gap_min:>2}: {w:>4}W {l:>4}L {t:>4}T WR={wr:.1f}%")

print("\n" + "=" * 70)
print("ANALYSIS 7: Triple filter (session + gap + direction)")
print("=" * 70)

# Best sessions from above
best_sessions = [
    ("NY PM (15-17)", range(15, 18)),
    ("London AM (7-9)", range(7, 10)),
    ("NY (12-17)", range(12, 18)),
    ("London+NY (7-17)", range(7, 18)),
]

print(f"{'Filter Combo':<55} {'Wins':>5} {'Loss':>5} {'Tot':>5} {'WR%':>7}")
print("-" * 80)

for sname, hours in best_sessions:
    for gap_min in [0, 5]:
        for direction in ["BULLISH_FVG", "BEARISH_FVG", "BOTH"]:
            w = sum(1 for r in wins 
                    if get_hour(r) in hours 
                    and r["gap_size_pips"] >= gap_min
                    and (direction=="BOTH" or r["pattern_type"]==direction))
            l = sum(1 for r in losses 
                    if get_hour(r) in hours 
                    and r["gap_size_pips"] >= gap_min
                    and (direction=="BOTH" or r["pattern_type"]==direction))
            t = w + l
            wr = w/t*100 if t>0 else 0
            d_label = direction.split("_")[0]
            label = f"{sname} + gap>={gap_min} + {d_label}"
            print(f"{label:<55} {w:>5} {l:>5} {t:>5} {wr:>6.1f}%")

print("\n" + "=" * 70)
print("ANALYSIS 8: Gap threshold WR vs sample size trade-off")
print("=" * 70)

print(f"{'Gap>=':>6} {'Wins':>5} {'Loss':>5} {'Total':>6} {'WR%':>7} {'Retained%':>9}")
print("-" * 50)
total = len(wins) + len(losses)
for gap_min in range(0, 21):
    w = sum(1 for r in wins if r["gap_size_pips"] >= gap_min)
    l = sum(1 for r in losses if r["gap_size_pips"] >= gap_min)
    t = w + l
    wr = w/t*100 if t>0 else 0
    retained = t/total*100 if total>0 else 0
    bar = "█" * int(wr/5) if wr>0 else ""
    print(f"{gap_min:>6} {w:>5} {l:>5} {t:>6} {wr:>6.1f}% {retained:>8.1f}% {bar}")

print("\n" + "=" * 70)
print("ANALYSIS 9: Streak analysis within filtered set (gap>=5)")
print("=" * 70)

filtered = [r for r in fvg_results if r["gap_size_pips"] >= 5]
filtered_sorted = sorted(filtered, key=lambda r: r.get("timestamp", ""))

streaks = []
if filtered_sorted:
    curr = filtered_sorted[0]["outcome"]
    length = 0
    for r in filtered_sorted:
        if r["outcome"] == curr:
            length += 1
        else:
            streaks.append((curr, length))
            curr = r["outcome"]
            length = 1
    streaks.append((curr, length))

win_streaks = [s[1] for s in streaks if s[0] == "WIN"]
loss_streaks = [s[1] for s in streaks if s[0] == "LOSS"]

print(f"Filtered set: {sum(win_streaks)} wins, {sum(loss_streaks)} losses")
print(f"Win streaks: {len(win_streaks)} (mean={sum(win_streaks)/len(win_streaks):.1f}, max={max(win_streaks) if win_streaks else 0})")
print(f"Loss streaks: {len(loss_streaks)} (mean={sum(loss_streaks)/len(loss_streaks):.1f}, max={max(loss_streaks) if loss_streaks else 0})")

for length in range(1, 8):
    wc = win_streaks.count(length)
    lc = loss_streaks.count(length)
    print(f"  Length {length}: {wc}W / {lc}L")

print("\n" + "=" * 70)
print("ANALYSIS 10: Check NO_DECISION rate by filter")
print("=" * 70)

all_fvg = [r for r in all_results if r.get("pattern_type","") in ("BULLISH_FVG", "BEARISH_FVG")]
for gap_min in [0, 5, 10]:
    total = sum(1 for r in all_fvg if r["gap_size_pips"] >= gap_min)
    nd = sum(1 for r in all_fvg if r["gap_size_pips"] >= gap_min and r["outcome"] == "NO_DECISION")
    rate = nd/total*100 if total>0 else 0
    print(f"  gap>={gap_min}: {nd} NO_DECISION out of {total} total ({rate:.1f}%)")

print("\n" + "=" * 70)
print("FINAL SUMMARY: TOP FILTER COMBINATIONS")
print("=" * 70)

# Comprehensive grid of best combos
print(f"\n{'#':>3} {'Filter':<50} {'W':>4} {'L':>4} {'T':>5} {'WR%':>7}")
print("-" * 75)

combos = []

for sname, hours in session_hours.items():
    for gap_min in [0, 5]:
        for direction in ["BULLISH_FVG", "BEARISH_FVG", "BOTH"]:
            w = sum(1 for r in wins 
                    if get_hour(r) in hours 
                    and r["gap_size_pips"] >= gap_min
                    and (direction=="BOTH" or r["pattern_type"]==direction))
            l = sum(1 for r in losses 
                    if get_hour(r) in hours 
                    and r["gap_size_pips"] >= gap_min
                    and (direction=="BOTH" or r["pattern_type"]==direction))
            t = w + l
            if t < 10: continue
            wr = w/t*100
            combos.append((wr, w, l, t, f"{sname} gap>={gap_min} {direction.split('_')[0]}"))

combos.sort(reverse=True)
for i, (wr, w, l, t, label) in enumerate(combos[:30]):
    print(f"{i+1:>3} {label:<50} {w:>4} {l:>4} {t:>5} {wr:>6.1f}%")
