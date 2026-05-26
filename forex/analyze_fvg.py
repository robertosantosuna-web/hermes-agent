#!/usr/bin/env python3
"""Deep FVG analysis: find what separates wins from losses."""
import json
from collections import defaultdict, Counter
import math

# Load both files
with open("/home/roberto/.hermes/forex/simulations/hermes_eurusd_analysis.json") as f:
    eurusd = json.load(f)
with open("/home/roberto/.hermes/forex/simulations/brain_gbpusd_analysis.json") as f:
    gbpusd = json.load(f)

# Extract all FVG results (WIN/LOSS only, skip NO_DECISION)
all_results = eurusd["all_results"] + gbpusd["all_results"]
fvg_results = [r for r in all_results 
               if r.get("pattern_type","") in ("BULLISH_FVG", "BEARISH_FVG")
               and r.get("outcome","") in ("WIN", "LOSS")]

wins = [r for r in fvg_results if r["outcome"] == "WIN"]
losses = [r for r in fvg_results if r["outcome"] == "LOSS"]

print(f"Total FVG (WIN+LOSS): {len(fvg_results)}")
print(f"  Wins: {len(wins)} ({len(wins)/len(fvg_results)*100:.1f}%)")
print(f"  Losses: {len(losses)} ({len(losses)/len(fvg_results)*100:.1f}%)")
print()

# ============================================================
# 1. CANDLE INDEX ANALYSIS (time-of-day clustering)
# ============================================================
print("=" * 70)
print("1. CANDLE INDEX ANALYSIS (M15 timeframe: each candle = 15 min)")
print("=" * 70)

# Map candle_index to hour of day. On M15, 4 candles/hour. Need to determine session start.
# candle_index is sequential from start of data. Need to determine what hour each index maps to.
# Since we have timestamps, let's extract hour directly from timestamp
def get_hour(r):
    ts = r.get("timestamp", "")
    if ts:
        try:
            # Format: "2026-04-13 19:00"
            hour = int(ts.split(" ")[1].split(":")[0])
            return hour
        except:
            pass
    return None

def get_minute(r):
    ts = r.get("timestamp", "")
    if ts:
        try:
            minute = int(ts.split(" ")[1].split(":")[1])
            return minute
        except:
            pass
    return None

# Hour analysis
hour_wins = Counter()
hour_losses = Counter()
for r in wins:
    h = get_hour(r)
    if h is not None:
        hour_wins[h] += 1
for r in losses:
    h = get_hour(r)
    if h is not None:
        hour_losses[h] += 1

print("\nHourly win rate:")
print(f"{'Hour':>6} {'Wins':>6} {'Losses':>6} {'Total':>6} {'WR%':>8}")
print("-" * 40)
for h in sorted(set(list(hour_wins.keys()) + list(hour_losses.keys()))):
    w = hour_wins[h]
    l = hour_losses[h]
    t = w + l
    wr = (w / t * 100) if t > 0 else 0
    bar = "█" * int(wr / 5) if wr > 0 else ""
    print(f"{h:>6} {w:>6} {l:>6} {t:>6} {wr:>7.1f}% {bar}")

# Session analysis: Asian (0-7), London (7-12), NY (12-17), Evening (17-24)
sessions = {
    "Asian (0-6)": range(0, 7),
    "London AM (7-9)": range(7, 10),
    "London PM (10-12)": range(10, 13),
    "NY AM (12-14)": range(12, 15),
    "NY PM (15-17)": range(15, 18),
    "Evening (18-23)": range(18, 24)
}

print("\nSession analysis:")
print(f"{'Session':<20} {'Wins':>6} {'Losses':>6} {'Total':>6} {'WR%':>8}")
print("-" * 55)
for sname, hours in sessions.items():
    sw = sum(hour_wins[h] for h in hours)
    sl = sum(hour_losses[h] for h in hours)
    st = sw + sl
    wr = (sw / st * 100) if st > 0 else 0
    bar = "█" * int(wr / 5) if wr > 0 else ""
    print(f"{sname:<20} {sw:>6} {sl:>6} {st:>6} {wr:>7.1f}% {bar}")

# ============================================================
# 2. GAP SIZE DISTRIBUTIONS
# ============================================================
print("\n" + "=" * 70)
print("2. GAP SIZE (pips) DISTRIBUTION")
print("=" * 70)

win_gaps = [r["gap_size_pips"] for r in wins]
loss_gaps = [r["gap_size_pips"] for r in losses]

def stats(arr):
    arr_s = sorted(arr)
    n = len(arr_s)
    return {
        "count": n,
        "min": min(arr_s),
        "max": max(arr_s),
        "mean": sum(arr_s) / n,
        "median": arr_s[n // 2],
        "p25": arr_s[n // 4],
        "p75": arr_s[3 * n // 4],
        "p10": arr_s[n // 10],
        "p90": arr_s[9 * n // 10],
    }

ws = stats(win_gaps)
ls = stats(loss_gaps)
print(f"\nWin gap stats:  mean={ws['mean']:.1f}, median={ws['median']:.1f}, p25={ws['p25']:.1f}, p75={ws['p75']:.1f}, p10={ws['p10']:.1f}, p90={ws['p90']:.1f}")
print(f"Loss gap stats: mean={ls['mean']:.1f}, median={ls['median']:.1f}, p25={ls['p25']:.1f}, p75={ls['p75']:.1f}, p10={ls['p10']:.1f}, p90={ls['p90']:.1f}")

# Bucket analysis for gap sizes
print("\nGap size buckets (every 5 pips):")
bucket_size = 5
all_gaps = win_gaps + loss_gaps
max_gap = max(all_gaps)
buckets = defaultdict(lambda: {"win": 0, "loss": 0})
for r in wins:
    b = int(r["gap_size_pips"] // bucket_size) * bucket_size
    buckets[b]["win"] += 1
for r in losses:
    b = int(r["gap_size_pips"] // bucket_size) * bucket_size
    buckets[b]["loss"] += 1

print(f"{'Gap Range':>12} {'Wins':>6} {'Losses':>6} {'Total':>6} {'WR%':>8}")
print("-" * 45)
for b in sorted(buckets.keys()):
    w = buckets[b]["win"]
    l = buckets[b]["loss"]
    t = w + l
    wr = (w / t * 100) if t > 0 else 0
    bar = "█" * int(wr / 5) if wr > 0 else ""
    print(f"{b}-{b+bucket_size-1:>3}: {w:>6} {l:>6} {t:>6} {wr:>7.1f}% {bar}")

# Find optimal gap thresholds
print("\nWR by gap_size threshold (gap >= X):")
for thresh in range(5, 31, 5):
    w = sum(1 for g in win_gaps if g >= thresh)
    l = sum(1 for g in loss_gaps if g >= thresh)
    t = w + l
    wr = (w / t * 100) if t > 0 else 0
    print(f"  gap >= {thresh:>3}: {w:>4} wins, {l:>4} losses, {t:>4} total, WR={wr:.1f}%")

print("\nWR by gap_size threshold (gap <= X):")
for thresh in range(10, 41, 5):
    w = sum(1 for g in win_gaps if g <= thresh)
    l = sum(1 for g in loss_gaps if g <= thresh)
    t = w + l
    wr = (w / t * 100) if t > 0 else 0
    print(f"  gap <= {thresh:>3}: {w:>4} wins, {l:>4} losses, {t:>4} total, WR={wr:.1f}%")

# ============================================================
# 3. SL DISTANCE EFFECTS
# ============================================================
print("\n" + "=" * 70)
print("3. SL DISTANCE (pips) EFFECTS")
print("=" * 70)

win_sls = [r["sl_pips"] for r in wins]
loss_sls = [r["sl_pips"] for r in losses]

sl_win_stats = stats(win_sls)
sl_loss_stats = stats(loss_sls)
print(f"\nWin SL stats:  mean={sl_win_stats['mean']:.1f}, median={sl_win_stats['median']:.1f}, p25={sl_win_stats['p25']:.1f}, p75={sl_win_stats['p75']:.1f}")
print(f"Loss SL stats: mean={sl_loss_stats['mean']:.1f}, median={sl_loss_stats['median']:.1f}, p25={sl_loss_stats['p25']:.1f}, p75={sl_loss_stats['p75']:.1f}")

print("\nSL bucket analysis:")
sl_buckets = defaultdict(lambda: {"win": 0, "loss": 0})
for r in wins:
    b = int(r["sl_pips"] // 5) * 5
    sl_buckets[b]["win"] += 1
for r in losses:
    b = int(r["sl_pips"] // 5) * 5
    sl_buckets[b]["loss"] += 1

print(f"{'SL Range':>12} {'Wins':>6} {'Losses':>6} {'Total':>6} {'WR%':>8}")
print("-" * 45)
for b in sorted(sl_buckets.keys()):
    w = sl_buckets[b]["win"]
    l = sl_buckets[b]["loss"]
    t = w + l
    wr = (w / t * 100) if t > 0 else 0
    bar = "█" * int(wr / 5) if wr > 0 else ""
    print(f"{b}-{b+4:>3}: {w:>6} {l:>6} {t:>6} {wr:>7.1f}% {bar}")

# ============================================================
# 4. STRENGTH ANALYSIS
# ============================================================
print("\n" + "=" * 70)
print("4. PATTERN STRENGTH ANALYSIS")
print("=" * 70)

win_strengths = [r.get("strength", 0) for r in wins]
loss_strengths = [r.get("strength", 0) for r in losses]

ws_str = stats(win_strengths)
ls_str = stats(loss_strengths)
print(f"\nWin strength:  mean={ws_str['mean']:.4f}, median={ws_str['median']:.4f}, p25={ws_str['p25']:.4f}")
print(f"Loss strength: mean={ls_str['mean']:.4f}, median={ls_str['median']:.4f}, p25={ls_str['p25']:.4f}")

# Strength thresholds
print("\nWR by strength threshold (strength >= X):")
for thresh in [round(x*0.1, 1) for x in range(0, 10)]:
    w = sum(1 for s in win_strengths if s >= thresh)
    l = sum(1 for s in loss_strengths if s >= thresh)
    t = w + l
    wr = (w / t * 100) if t > 0 else 0
    print(f"  strength >= {thresh:.1f}: {w:>4} wins, {l:>4} losses, {t:>4} total, WR={wr:.1f}%")

# ============================================================
# 5. CONSECUTIVE WINS/LOSSES
# ============================================================
print("\n" + "=" * 70)
print("5. CONSECUTIVE PATTERNS (streak analysis)")
print("=" * 70)

# Sort by timestamp and analyze streaks
fvg_sorted = sorted(fvg_results, key=lambda r: r.get("timestamp", ""))
streaks = []
current_outcome = fvg_sorted[0]["outcome"] if fvg_sorted else None
current_len = 0
for r in fvg_sorted:
    if r["outcome"] == current_outcome:
        current_len += 1
    else:
        streaks.append((current_outcome, current_len))
        current_outcome = r["outcome"]
        current_len = 1
if current_len > 0:
    streaks.append((current_outcome, current_len))

win_streaks = [s[1] for s in streaks if s[0] == "WIN"]
loss_streaks = [s[1] for s in streaks if s[0] == "LOSS"]

print(f"Total streaks: {len(streaks)}")
print(f"Win streaks: {len(win_streaks)} (mean={sum(win_streaks)/len(win_streaks):.1f}, max={max(win_streaks)})")
print(f"Loss streaks: {len(loss_streaks)} (mean={sum(loss_streaks)/len(loss_streaks):.1f}, max={max(loss_streaks)})")

print(f"\nStreak distribution:")
for length in range(1, max(max(win_streaks), max(loss_streaks)) + 1):
    wc = win_streaks.count(length)
    lc = loss_streaks.count(length)
    print(f"  Length {length}: {wc} win streaks, {lc} loss streaks")

# ============================================================
# 6. RR_ACHIEVED DISTRIBUTION
# ============================================================
print("\n" + "=" * 70)
print("6. RR ACHIEVED DISTRIBUTION (WIN trades only)")
print("=" * 70)

win_rrs = [r["rr_achieved"] for r in wins]
loss_rrs = [r["rr_achieved"] for r in losses]

print(f"\nWin RR: mean={sum(win_rrs)/len(win_rrs):.2f}, min={min(win_rrs):.2f}, max={max(win_rrs):.2f}")
print(f"Win RR distribution:")
rr_buckets = Counter()
for rr in win_rrs:
    b = int(rr // 0.5) * 0.5
    rr_buckets[b] += 1
for b in sorted(rr_buckets.keys()):
    print(f"  RR {b:.1f}: {rr_buckets[b]} trades")

# ============================================================
# 7. DIRECTION ANALYSIS
# ============================================================
print("\n" + "=" * 70)
print("7. DIRECTION (BULLISH vs BEARISH FVG)")
print("=" * 70)

for ptype in ["BULLISH_FVG", "BEARISH_FVG"]:
    pt_wins = [r for r in wins if r["pattern_type"] == ptype]
    pt_losses = [r for r in losses if r["pattern_type"] == ptype]
    total = len(pt_wins) + len(pt_losses)
    wr = len(pt_wins) / total * 100 if total > 0 else 0
    print(f"  {ptype:<15}: {len(pt_wins):>4} wins, {len(pt_losses):>4} losses, {total:>4} total, WR={wr:.1f}%")

# ============================================================
# 8. COMBINED THRESHOLD TESTING
# ============================================================
print("\n" + "=" * 70)
print("8. COMBINED FILTER ANALYSIS (grid search)")
print("=" * 70)

print(f"\n{'Gap>=':>7} {'SL<=':>7} {'Str>=':>7} {'Wins':>6} {'Losses':>6} {'Total':>6} {'WR%':>8}")
print("-" * 60)

best_wr = 0
best_combo = None

for gap_min in [0, 5, 10, 15, 20, 25]:
    for sl_max in [10, 15, 20, 25, 30, 50, 999]:
        for str_min in [0.0, 0.1, 0.2, 0.3]:
            w = sum(1 for r in wins 
                    if r["gap_size_pips"] >= gap_min 
                    and r["sl_pips"] <= sl_max
                    and r.get("strength", 0) >= str_min)
            l = sum(1 for r in losses 
                    if r["gap_size_pips"] >= gap_min 
                    and r["sl_pips"] <= sl_max
                    and r.get("strength", 0) >= str_min)
            t = w + l
            wr = w / t * 100 if t > 0 else 0
            if t >= 30:  # minimum sample
                if wr > best_wr:
                    best_wr = wr
                    best_combo = (gap_min, sl_max, str_min, w, l, t, wr)
                if wr >= 55:
                    print(f"{gap_min:>7} {sl_max:>7} {str_min:>7.1f} {w:>6} {l:>6} {t:>6} {wr:>7.1f}%")

print(f"\nBest filter: gap>={best_combo[0]}, SL<={best_combo[1]}, str>={best_combo[2]:.1f}")
print(f"  Result: {best_combo[3]} wins, {best_combo[4]} losses, {best_combo[5]} total, WR={best_combo[6]:.1f}%")
print(f"  Remaining from {len(wins)+len(losses)} total patterns: {best_combo[5]}")
print(f"  Filter rate: {(1 - best_combo[5]/(len(wins)+len(losses)))*100:.1f}% removed")

# ============================================================
# 9. CANDLE INDEX PATTERNS WITHIN SESSIONS
# ============================================================
print("\n" + "=" * 70)
print("9. CANDLE INDEX DISTRIBUTION (ordinal position)")
print("=" * 70)

# Check if later candle indices (more recent in dataset) perform differently
win_indices = [r["candle_index"] for r in wins]
loss_indices = [r["candle_index"] for r in losses]

wi_stats = stats(win_indices)
li_stats = stats(loss_indices)
print(f"\nWin candle_index:  mean={wi_stats['mean']:.0f}, median={wi_stats['median']:.0f}")
print(f"Loss candle_index: mean={li_stats['mean']:.0f}, median={li_stats['median']:.0f}")

# Bucket by 200-candle ranges
idx_buckets = defaultdict(lambda: {"win": 0, "loss": 0})
for r in wins:
    b = (r["candle_index"] // 200) * 200
    idx_buckets[b]["win"] += 1
for r in losses:
    b = (r["candle_index"] // 200) * 200
    idx_buckets[b]["loss"] += 1

print(f"\n{'Candle Range':>14} {'Wins':>6} {'Losses':>6} {'Total':>6} {'WR%':>8}")
print("-" * 45)
for b in sorted(idx_buckets.keys()):
    w = idx_buckets[b]["win"]
    l = idx_buckets[b]["loss"]
    t = w + l
    wr = (w / t * 100) if t > 0 else 0
    bar = "█" * int(wr / 5) if wr > 0 else ""
    print(f"{b:>5}-{b+199:>5}: {w:>6} {l:>6} {t:>6} {wr:>7.1f}% {bar}")

# ============================================================
# 10. SUMMARY & RECOMMENDED THRESHOLDS
# ============================================================
print("\n" + "=" * 70)
print("10. SUMMARY: RECOMMENDED FILTER THRESHOLDS")
print("=" * 70)

print("""
Based on the analysis above, here are the specific numeric thresholds
that can filter out losers:

1. GAP SIZE MINIMUM: Filter out patterns with gap < X pips
   (check the gap bucket table for the threshold where WR drops)

2. SL DISTANCE MAXIMUM: Filter out patterns with SL > Y pips
   (too-wide stops correlate with lower WR in certain ranges)

3. STRENGTH MINIMUM: Filter out patterns with strength < Z
   (weaker patterns have lower WR)

4. SESSION FILTER: Avoid trading during low-WR sessions
   (check session table for sessions with WR below baseline)

5. GAP RANGE (too large): Very large gaps may also be problematic
   (check if gap > N reduces WR)
""")
