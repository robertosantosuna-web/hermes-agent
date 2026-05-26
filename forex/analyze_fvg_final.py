#!/usr/bin/env python3
"""Final FVG threshold analysis - exact numeric thresholds."""
import json
from collections import defaultdict

with open("/home/roberto/.hermes/forex/simulations/hermes_eurusd_analysis.json") as f:
    eurusd = json.load(f)
with open("/home/roberto/.hermes/forex/simulations/brain_gbpusd_analysis.json") as f:
    gbpusd = json.load(f)

all_results = eurusd["all_results"] + gbpusd["all_results"]
fvg = [r for r in all_results 
       if r.get("pattern_type","") in ("BULLISH_FVG", "BEARISH_FVG")
       and r.get("outcome","") in ("WIN", "LOSS")]

wins = [r for r in fvg if r["outcome"] == "WIN"]
losses = [r for r in fvg if r["outcome"] == "LOSS"]
total = len(wins) + len(losses)
baseline_wr = len(wins) / total * 100

def get_hour(r):
    try: return int(r["timestamp"].split(" ")[1].split(":")[0])
    except: return None

# ==========================================
# THRESHOLD 1: GAP SIZE MINIMUM
# ==========================================
print("=" * 72)
print("THRESHOLD 1: MINIMUM GAP SIZE (pips)")
print("=" * 72)
print()
print("  Baseline: {:.1f}% WR ({:,} total)".format(baseline_wr, total))
print()

print(f"  {'Min Gap':>8}  {'Wins':>5}  {'Loss':>5}  {'Total':>6}  {'WR%':>7}  {'dWR':>7}  {'Volume':>8}  Verdict")
print(f"  {'-'*8}  {'-'*5}  {'-'*5}  {'-'*6}  {'-'*7}  {'-'*7}  {'-'*8}  {'-'*30}")

for gap in range(0, 11):
    w = sum(1 for r in wins if r["gap_size_pips"] >= gap)
    l = sum(1 for r in losses if r["gap_size_pips"] >= gap)
    t = w + l
    wr = w/t*100 if t>0 else 0
    delta = wr - baseline_wr
    pct_retained = t/total*100
    star = " *** KEEP" if wr >= 60 and t >= 100 else ""
    star2 = " *" if wr >= 55 and t >= 200 else ""
    note = star + star2
    print(f"  {gap:>8}  {w:>5}  {l:>5}  {t:>6}  {wr:>6.1f}%  {delta:>+6.1f}%  {pct_retained:>7.1f}%  {note}")

print()
print("  RECOMMENDATION: gap_size_pips >= 5")
print("  - Eliminates gaps 0-4 which are mostly noise patterns")
print("  - gap=0 alone has 35.6% WR (123L vs 68W) -> those are pure losers")
print("  - gap=1 has 41.8% WR -> also below baseline")
print("  - At gap>=5: 67.2% WR with 17.8% volume retained (232 trades)")
print("  - Alternative: gap>=3 yields 66.9% WR with 33.1% retained (432 trades)")
print()

# ==========================================
# THRESHOLD 2: TIME OF DAY (HOUR)
# ==========================================
print("=" * 72)
print("THRESHOLD 2: TIME OF DAY (HOUR FILTER)")
print("=" * 72)
print()
print("  Baseline: {:.1f}% WR".format(baseline_wr))
print()

# Find exact hour thresholds
hour_data = {}
for h in range(24):
    hw = sum(1 for r in wins if get_hour(r) == h)
    hl = sum(1 for r in losses if get_hour(r) == h)
    ht = hw + hl
    wr = hw/ht*100 if ht>0 else 0
    hour_data[h] = (hw, hl, ht, wr)

print(f"  {'Hour':>6}  {'Wins':>5}  {'Loss':>5}  {'Total':>6}  {'WR%':>7}  {'dWR':>7}  Verdict")
print(f"  {'-'*6}  {'-'*5}  {'-'*5}  {'-'*6}  {'-'*7}  {'-'*7}  {'-'*30}")

for h in range(24):
    hw, hl, ht, wr = hour_data[h]
    if ht == 0: continue
    delta = wr - baseline_wr
    if wr >= 65 and ht >= 20:
        v = "*** BEST"
    elif wr >= 60 and ht >= 15:
        v = "* GOOD"
    elif wr >= baseline_wr:
        v = "ok"
    elif wr < 40 and ht >= 10:
        v = "XXX AVOID"
    elif wr < 45:
        v = "xx weak"
    else:
        v = ""
    print(f"  {h:>6}  {hw:>5}  {hl:>5}  {ht:>6}  {wr:>6.1f}%  {delta:>+6.1f}%  {v}")

# Session WRs
print()
print("  Session Summary:")
session_hours = {
    "Asian (0-6)": range(0, 7),
    "London AM (7-9)": range(7, 10),
    "London PM (10-12)": range(10, 13),
    "NY AM (12-14)": range(12, 15),
    "NY PM (15-17)": range(15, 18),
    "Evening (18-23)": range(18, 24),
}
for sname, hours in session_hours.items():
    sw = sum(hour_data[h][0] for h in hours)
    sl = sum(hour_data[h][1] for h in hours)
    st = sw + sl
    wr = sw/st*100 if st>0 else 0
    delta = wr - baseline_wr
    print(f"  {sname:<20}: {sw:>4}W {sl:>4}L  {st:>4}T  {wr:>5.1f}% WR  ({delta:+.1f}%)")

print()
print("  RECOMMENDED HOUR FILTERS:")
print("  AVOID: hour 20 (11.1% WR), hour 21 (25.0%)")
print("  AVOID ALL: hour >= 18 (evening: 37.1% WR)")
print("  AVOID: hour 2 (26.9%), hour 3 (34.5%)")
print("  BEST: hours 6-7 (London open, 73.3-73.8%)")
print("  BEST: hours 15-16 (NY PM, 68.0-70.9%)")
print("  GOOD: hours 9, 11, 12, 13, 14 (all >55%)")
print()

# ==========================================
# THRESHOLD 3: COMBINED GAP + TIME
# ==========================================
print("=" * 72)
print("THRESHOLD 3: COMBINED GAP + TIME FILTER")
print("=" * 72)
print()

time_gap_combos = []
for exclude_evening in [True, False]:
    for gap_min in [0, 3, 4, 5, 6]:
        w = 0; l = 0
        for r in wins:
            h = get_hour(r)
            if h is None: continue
            if exclude_evening and h >= 18: continue
            if r["gap_size_pips"] >= gap_min:
                w += 1
        for r in losses:
            h = get_hour(r)
            if h is None: continue
            if exclude_evening and h >= 18: continue
            if r["gap_size_pips"] >= gap_min:
                l += 1
        t = w + l
        if t < 30: continue
        wr = w/t*100
        label = f"gap>={gap_min}" + (" + NOT evening" if exclude_evening else "")
        time_gap_combos.append((wr, w, l, t, label))

time_gap_combos.sort(reverse=True)
print(f"  {'Filter':<35}  {'W':>4}  {'L':>4}  {'T':>5}  {'WR%':>7}")
print(f"  {'-'*35}  {'-'*4}  {'-'*4}  {'-'*5}  {'-'*7}")
for wr, w, l, t, label in time_gap_combos:
    print(f"  {label:<35}  {w:>4}  {l:>4}  {t:>5}  {wr:>6.1f}%")

print()
print("  RECOMMENDED: gap>=5 AND hour NOT in [18..23]")
print("  Result: 144W 66L -> 68.6% WR on 210 trades")
print()

# ==========================================
# THRESHOLD 4: DIRECTION
# ==========================================
print("=" * 72)
print("THRESHOLD 4: DIRECTION (BULLISH vs BEARISH FVG)")
print("=" * 72)
print()

for direction in ["BULLISH_FVG", "BEARISH_FVG"]:
    for gap in [0, 4, 5]:
        w = sum(1 for r in wins if r["pattern_type"]==direction and r["gap_size_pips"]>=gap)
        l = sum(1 for r in losses if r["pattern_type"]==direction and r["gap_size_pips"]>=gap)
        t = w + l
        wr = w/t*100 if t>0 else 0
        print(f"  {direction:<15} gap>={gap}: {w:>4}W {l:>4}L {t:>4}T WR={wr:.1f}%")

print()
print("  BEARISH_FVG outperforms BULLISH_FVG without filters (54.6% vs 47.3%)")
print("  With gap>=5 they converge: 66.0% vs 68.3%")
print("  For conservative filtering: prefer BEARISH_FVG when no gap filter")
print()

# ==========================================
# THRESHOLD 5: CONSECUTIVE PATTERNS
# ==========================================
print("=" * 72)
print("THRESHOLD 5: STREAK BEHAVIOR & RISK MANAGEMENT")
print("=" * 72)
print()

# Sorted by timestamp
fvg_sorted = sorted(fvg, key=lambda r: r.get("timestamp", ""))
streaks = []
if fvg_sorted:
    curr = fvg_sorted[0]["outcome"]
    length = 0
    for r in fvg_sorted:
        if r["outcome"] == curr:
            length += 1
        else:
            streaks.append((curr, length))
            curr = r["outcome"]
            length = 1
    streaks.append((curr, length))

win_streaks = [s[1] for s in streaks if s[0] == "WIN"]
loss_streaks = [s[1] for s in streaks if s[0] == "LOSS"]

print(f"  Unfiltered data ({len(streaks)} total streaks):")
print(f"    Win streaks:  mean={sum(win_streaks)/len(win_streaks):.1f}, max={max(win_streaks)}")
print(f"    Loss streaks: mean={sum(loss_streaks)/len(loss_streaks):.1f}, max={max(loss_streaks)}")
print(f"    Streaks >= 5: {sum(1 for s in win_streaks if s>=5)} win, {sum(1 for s in loss_streaks if s>=5)} loss")
print(f"    Streaks >= 10: {sum(1 for s in win_streaks if s>=10)} win, {sum(1 for s in loss_streaks if s>=10)} loss")

# Gap >= 5 streaks
fvg_filt = [r for r in fvg if r["gap_size_pips"] >= 5]
fvg_filt_sorted = sorted(fvg_filt, key=lambda r: r.get("timestamp", ""))
fstreaks = []
if fvg_filt_sorted:
    curr = fvg_filt_sorted[0]["outcome"]
    length = 0
    for r in fvg_filt_sorted:
        if r["outcome"] == curr:
            length += 1
        else:
            fstreaks.append((curr, length))
            curr = r["outcome"]
            length = 1
    fstreaks.append((curr, length))

fw = [s[1] for s in fstreaks if s[0] == "WIN"]
fl = [s[1] for s in fstreaks if s[0] == "LOSS"]

print(f"\n  Filtered (gap>=5) data ({len(fstreaks)} total streaks):")
print(f"    Win streaks:  mean={sum(fw)/len(fw):.1f}, max={max(fw)}")
print(f"    Loss streaks: mean={sum(fl)/len(fl):.1f}, max={max(fl)}")
print(f"    Streaks >= 5: {sum(1 for s in fw if s>=5)} win, {sum(1 for s in fl if s>=5)} loss")
print(f"    Streaks >= 10: {sum(1 for s in fw if s>=10)} win, {sum(1 for s in fl if s>=10)} loss")

print()
print("  KEY FINDING: With gap>=5 filter, max loss streak drops from 20->7")
print("  and 80% of loss streaks are length 1-2. Much more manageable.")
print()

# ==========================================
# THRESHOLD 6: SL DISTANCE
# ==========================================
print("=" * 72)
print("THRESHOLD 6: SL DISTANCE (not useful as filter)")
print("=" * 72)
print()
sl_vals = set(r["sl_pips"] for r in fvg)
print(f"  Unique SL values in FVG: {sorted(sl_vals)[:20]}")
print(f"  97% of trades use SL=5 pips. SL distance is NOT a differentiating factor.")
print()

# ==========================================
# THRESHOLD 7: STRENGTH
# ==========================================
print("=" * 72)
print("THRESHOLD 7: PATTERN STRENGTH (not available for FVG)")
print("=" * 72)
print()
print("  All FVG patterns have strength='N/A'. The strength field is only computed")
print("  for BOS/CHOCH patterns. Cannot use this for FVG filtering.")
print()

# ==========================================
# RECOMMENDED TIERED FILTERS
# ==========================================
print("=" * 72)
print("FINAL: RECOMMENDED FILTER TIERS")
print("=" * 72)
print()

tiers = []

# Tier 1: Conservative - gap>=5 + active hours
for gap_min, label in [(5, "gap>=5"), (4, "gap>=4"), (3, "gap>=3")]:
    for hour_rule, hour_label in [
        (lambda h: h is not None and h < 18, "NOT evening (h<18)"),
        (lambda h: h is not None and 6 <= h <= 16, "h 6-16 only"),
        (lambda h: h is not None and 7 <= h <= 16, "h 7-16 only"),
        (lambda h: h is not None, "no time filter"),
    ]:
        w = sum(1 for r in wins if hour_rule(get_hour(r)) and r["gap_size_pips"] >= gap_min)
        l = sum(1 for r in losses if hour_rule(get_hour(r)) and r["gap_size_pips"] >= gap_min)
        t = w + l
        if t < 30: continue
        wr = w/t*100
        delta = wr - baseline_wr
        tiers.append((wr, delta, t, w, l, f"{label} + {hour_label}"))

tiers.sort(reverse=True)

print(f"  {'Rank':>4}  {'Filter':<45}  {'W':>4}  {'L':>4}  {'T':>5}  {'WR%':>7}  {'dWR':>6}")
print(f"  {'-'*4}  {'-'*45}  {'-'*4}  {'-'*4}  {'-'*5}  {'-'*7}  {'-'*6}")
for i, (wr, delta, t, w, l, label) in enumerate(tiers[:20]):
    pfx = "***" if wr >= 68 else ("**" if wr >= 63 else " *" if wr >= 58 else "")
    print(f"  {i+1:>4}  {label:<45}  {w:>4}  {l:>4}  {t:>5}  {wr:>6.1f}%  {delta:>+5.1f}% {pfx}")

print()
print("  TOP RECOMMENDATION:")
print("  gap_size_pips >= 5  AND  hour NOT in [18, 19, 20, 21, 22, 23]")
print("  -> 68.6% WR, 210 trades, +17.5% over baseline")
print()
print("  AGGRESSIVE RECOMMENDATION:")
print("  gap_size_pips >= 3  AND  hour NOT in [18..23]")
print("  -> 66.7% WR, 389 trades, +15.6% over baseline (more volume)")
print()

# ==========================================
# GAP 0-1 DEEP DIVE (why they're bad)
# ==========================================
print("=" * 72)
print("DEEP DIVE: Why gaps 0-1 are toxic")
print("=" * 72)
print()

for gap in [0, 1]:
    gap_wins = [r for r in wins if r["gap_size_pips"] == gap]
    gap_losses = [r for r in losses if r["gap_size_pips"] == gap]
    print(f"  Gap = {gap}:")
    print(f"    {len(gap_wins)} wins, {len(gap_losses)} losses -> WR={len(gap_wins)/(len(gap_wins)+len(gap_losses))*100:.1f}%")
    # Check their hour distribution
    for h in range(24):
        hw = sum(1 for r in gap_wins if get_hour(r) == h)
        hl = sum(1 for r in gap_losses if get_hour(r) == h)
        if hw + hl >= 10:
            wr = hw/(hw+hl)*100
            print(f"    Hour {h}: {hw}W {hl}L -> {wr:.1f}%")
    print()

# Evening distribution
print("  Evening losses breakdown (hours 18-23):")
for h in range(18, 24):
    hw = sum(1 for r in wins if get_hour(r) == h)
    hl = sum(1 for r in losses if get_hour(r) == h)
    ht = hw + hl
    if ht > 0:
        wr = hw/ht*100
        print(f"    Hour {h}: {hw}W {hl}L {ht}T -> {wr:.1f}% WR")
