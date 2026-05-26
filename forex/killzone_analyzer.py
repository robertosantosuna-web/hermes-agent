#!/usr/bin/env python3
"""
Killzone SMC Analysis — London Open (EURUSD, GBPUSD, EURGBP)
M5 data, M15 structure, sweeps + CHoCH, OB/FVG, 3:1 RR entry simulation
"""

import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import datetime, timedelta, timezone
import warnings
warnings.filterwarnings('ignore')

# ── Config ──────────────────────────────────────────────────
PAIRS = ["EURUSD=X", "GBPUSD=X", "EURGBP=X"]
PAIR_NAMES = {"EURUSD=X": "EURUSD", "GBPUSD=X": "GBPUSD", "EURGBP=X": "EURGBP"}
LOOKBACK_DAYS = 4
CHoCH_WINDOW_HOURS = 2
ATR_PERIOD = 14
RR_RATIO = 3.0

BRT = timezone(timedelta(hours=-3))
NOW = datetime.now(BRT)
print(f"Analysis Time (BRT): {NOW.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Killzone: London Open (05:00-07:00 BRT)")
print()

# ── 1. Download M5 data ─────────────────────────────────────
print("=" * 60)
print("Downloading M5 data...")
print("=" * 60)

data = {}
for pair in PAIRS:
    name = PAIR_NAMES[pair]
    try:
        df = yf.download(pair, period=f"{LOOKBACK_DAYS}d", interval="5m", progress=False, auto_adjust=True)
        if df.empty:
            print(f"  {name}: NO DATA (empty)")
            continue
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        df = df.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
        df.index = pd.to_datetime(df.index)
        if df.index.tz is None:
            df = df.tz_localize('UTC')
        df = df.tz_convert(BRT)
        data[name] = df
        print(f"  {name}: {len(df)} candles, {df.index[0]} to {df.index[-1]}")
    except Exception as e:
        print(f"  {name}: ERROR - {e}")

print()

# ── Helper functions ────────────────────────────────────────

def resample_to_m15(df_m5):
    df = df_m5.copy()
    m15 = df.resample('15min').agg({'open':'first','high':'max','low':'min','close':'last','volume':'sum'}).dropna()
    return m15

def detect_swing_points(df):
    highs, lows = [], []
    for i in range(2, len(df)-2):
        if (df['high'].iloc[i] > df['high'].iloc[i-1] and df['high'].iloc[i] > df['high'].iloc[i-2] and
            df['high'].iloc[i] > df['high'].iloc[i+1] and df['high'].iloc[i] > df['high'].iloc[i+2]):
            highs.append(i)
        if (df['low'].iloc[i] < df['low'].iloc[i-1] and df['low'].iloc[i] < df['low'].iloc[i-2] and
            df['low'].iloc[i] < df['low'].iloc[i+1] and df['low'].iloc[i] < df['low'].iloc[i+2]):
            lows.append(i)
    return highs, lows

def detect_structure(df, swing_highs, swing_lows):
    structure = "NEUTRAL"
    details = []
    if len(swing_highs) >= 2:
        if df['high'].iloc[swing_highs[-1]] > df['high'].iloc[swing_highs[-2]]:
            details.append(f"HH at {df.index[swing_highs[-1]]}")
        elif df['high'].iloc[swing_highs[-1]] < df['high'].iloc[swing_highs[-2]]:
            details.append(f"LH at {df.index[swing_highs[-1]]}")
    if len(swing_lows) >= 2:
        if df['low'].iloc[swing_lows[-1]] > df['low'].iloc[swing_lows[-2]]:
            details.append(f"HL at {df.index[swing_lows[-1]]}")
        elif df['low'].iloc[swing_lows[-1]] < df['low'].iloc[swing_lows[-2]]:
            details.append(f"LL at {df.index[swing_lows[-1]]}")
    if len(swing_highs) >= 3 and len(swing_lows) >= 3:
        h3, h2, h1 = swing_highs[-3], swing_highs[-2], swing_highs[-1]
        l3, l2, l1 = swing_lows[-3], swing_lows[-2], swing_lows[-1]
        bullish = (df['high'].iloc[h1] > df['high'].iloc[h2] and df['low'].iloc[l1] > df['low'].iloc[l2])
        bearish = (df['high'].iloc[h1] < df['high'].iloc[h2] and df['low'].iloc[l1] < df['low'].iloc[l2])
        if bullish: structure = "BULLISH"
        elif bearish: structure = "BEARISH"
        else: structure = "CONSOLIDATION"
    return structure, details

def find_sweeps_and_choch(df_m5, m15_swing_highs, m15_swing_lows, df_m15):
    cutoff = NOW - timedelta(hours=CHoCH_WINDOW_HOURS)
    recent_m5 = df_m5[df_m5.index >= cutoff]
    sweeps = []
    choch = None
    if recent_m5.empty:
        return sweeps, choch
    # High sweep
    if len(m15_swing_highs) > 0:
        last_swing_high = df_m15['high'].iloc[m15_swing_highs[-1]]
        recent_highs = recent_m5['high'].values
        if len(recent_highs) > 0 and any(recent_highs > last_swing_high * 1.0001):
            swept_idx = np.where(recent_highs > last_swing_high * 1.0001)[0]
            if len(swept_idx) > 0:
                post_sweep = recent_m5.iloc[swept_idx[-1]:]
                if len(post_sweep) > 2 and post_sweep['close'].iloc[-1] < last_swing_high:
                    sweeps.append({"type":"LIQUIDITY_SWEEP_HIGH","level":float(last_swing_high),
                                   "time":str(recent_m5.index[swept_idx[-1]]),
                                   "description":"Swept above M15 swing high, closed back below"})
    # Low sweep
    if len(m15_swing_lows) > 0:
        last_swing_low = df_m15['low'].iloc[m15_swing_lows[-1]]
        recent_lows = recent_m5['low'].values
        if len(recent_lows) > 0 and any(recent_lows < last_swing_low * 0.9999):
            swept_idx = np.where(recent_lows < last_swing_low * 0.9999)[0]
            if len(swept_idx) > 0:
                post_sweep = recent_m5.iloc[swept_idx[-1]:]
                if len(post_sweep) > 2 and post_sweep['close'].iloc[-1] > last_swing_low:
                    sweeps.append({"type":"LIQUIDITY_SWEEP_LOW","level":float(last_swing_low),
                                   "time":str(recent_m5.index[swept_idx[-1]]),
                                   "description":"Swept below M15 swing low, closed back above"})
    # CHoCH
    if len(m15_swing_highs) >= 2 and len(m15_swing_lows) >= 2:
        if len(m15_swing_lows) >= 3:
            last_low = df_m15['low'].iloc[m15_swing_lows[-1]]
            prev_low_val = df_m15['low'].iloc[m15_swing_lows[-2]]
            if last_low < prev_low_val:
                ph = [df_m15['high'].iloc[i] for i in m15_swing_highs[-3:]]
                pl = [df_m15['low'].iloc[i] for i in m15_swing_lows[-4:-1]]
                if len(ph)>=2 and len(pl)>=2 and ph[-1]>ph[-2] and pl[-1]>pl[-2]:
                    choch = {"type":"BEARISH_CHoCH","time":str(df_m15.index[m15_swing_lows[-1]]),
                             "description":"Break of bullish structure — LH broke below last HL"}
        if choch is None and len(m15_swing_highs) >= 3:
            last_high = df_m15['high'].iloc[m15_swing_highs[-1]]
            prev_high_val = df_m15['high'].iloc[m15_swing_highs[-2]]
            if last_high > prev_high_val:
                ph = [df_m15['high'].iloc[i] for i in m15_swing_highs[-4:-1]]
                pl = [df_m15['low'].iloc[i] for i in m15_swing_lows[-3:]]
                if len(ph)>=2 and len(pl)>=2 and ph[-1]<ph[-2] and pl[-1]<pl[-2]:
                    choch = {"type":"BULLISH_CHoCH","time":str(df_m15.index[m15_swing_highs[-1]]),
                             "description":"Break of bearish structure — HH broke above last LH"}
    return sweeps, choch

def find_order_blocks(df_m5, sweeps):
    obs = []
    if not sweeps: return obs
    for sweep in sweeps:
        level = sweep['level']
        sweep_time = pd.Timestamp(sweep['time'])
        before = df_m5[df_m5.index < sweep_time]
        if len(before)==0: continue
        if sweep['type']=='LIQUIDITY_SWEEP_HIGH':
            near = before[(before['high']>=level*0.999)&(before['high']<=level*1.005)]
            if len(near)>0:
                bear = near[near['close']<near['open']]
                if len(bear)>0:
                    lb = bear.iloc[-1]
                    obs.append({"type":"BEARISH_OB","zone_top":float(lb['open']),"zone_bottom":float(lb['close']),
                               "time":str(lb.name),"description":"OB — last bearish candle before sweep"})
        elif sweep['type']=='LIQUIDITY_SWEEP_LOW':
            near = before[(before['low']<=level*1.005)&(before['low']>=level*0.999)]
            if len(near)>0:
                bull = near[near['close']>near['open']]
                if len(bull)>0:
                    lb = bull.iloc[-1]
                    obs.append({"type":"BULLISH_OB","zone_top":float(lb['close']),"zone_bottom":float(lb['open']),
                               "time":str(lb.name),"description":"OB — last bullish candle before sweep"})
    return obs

def find_fvg(df):
    fvgs = []
    for i in range(1,len(df)-1):
        p,c,n = df.iloc[i-1], df.iloc[i], df.iloc[i+1]
        if c['low'] > p['high']:
            fvgs.append({"type":"BULLISH_FVG","gap_top":float(c['low']),"gap_bottom":float(p['high']),
                        "time":str(c.name),"description":"FVG — price gapped up"})
        elif c['high'] < p['low']:
            fvgs.append({"type":"BEARISH_FVG","gap_top":float(p['low']),"gap_bottom":float(c['high']),
                        "time":str(c.name),"description":"FVG — price gapped down"})
    return fvgs

def calculate_atr(df, period=ATR_PERIOD):
    h,l,c = df['high'].astype(float), df['low'].astype(float), df['close'].astype(float)
    tr1 = h - l
    tr2 = abs(h - c.shift(1))
    tr3 = abs(l - c.shift(1))
    tr = pd.concat([tr1,tr2,tr3],axis=1).max(axis=1)
    return tr.rolling(window=period).mean()

def score_setup(sweeps, choch, obs, fvgs, structure):
    score = 0
    reasons = []
    if not sweeps:
        return 0, ["No sweep — score 0"]
    score += 3; reasons.append("Liquidity sweep detected (+3)")
    if choch:
        score += 3; reasons.append(f"CHoCH: {choch['type']} (+3)")
    if obs:
        score += 2; reasons.append(f"Order Block identified (+2)")
    if fvgs:
        recent_f = [f for f in fvgs if pd.Timestamp(f['time'])> (NOW-timedelta(hours=6))]
        if recent_f:
            score += 2; reasons.append("Recent FVG present (+2)")
    if structure in ["BULLISH","BEARISH"]:
        reasons.append(f"Clear structure: {structure}")
    return score, reasons

def simulate_entry(sweeps, atr_val, current_price, direction):
    if not sweeps: return None
    sweep = sweeps[0]
    level = sweep['level']
    entry = current_price
    sl_buffer = atr_val*0.10 if atr_val and not np.isnan(atr_val) else current_price*0.002
    if direction=="SHORT":
        sl = level + sl_buffer
        tp = entry - abs(entry-sl)*RR_RATIO
    else:
        sl = level - sl_buffer
        tp = entry + abs(entry-sl)*RR_RATIO
    is_jpy = "JPY" in sweep.get('type','')
    mult = 100 if is_jpy else 10000
    return {"direction":direction,"entry":round(float(entry),5),"stop_loss":round(float(sl),5),
            "take_profit":round(float(tp),5),"sl_pips":round(abs(entry-sl)*mult,1),
            "tp_pips":round(abs(entry-tp)*mult,1),"risk_reward":"1:3"}

# ── 2-6. Analysis per pair ──────────────────────────────────
print("="*60)
print("SMC ANALYSIS")
print("="*60)

results = {}

for name in PAIR_NAMES.values():
    if name not in data: continue
    print(f"\n{'─'*50}")
    print(f"  {name}")
    print(f"{'─'*50}")
    df_m5 = data[name]
    df_m15 = resample_to_m15(df_m5)
    atr_series = calculate_atr(df_m5)
    current_atr = float(atr_series.iloc[-1]) if not atr_series.empty and not np.isnan(atr_series.iloc[-1]) else None
    current_price = float(df_m5['close'].iloc[-1])
    print(f"  Current Price: {current_price:.5f}")
    print(f"  ATR(14): {current_atr:.5f}" if current_atr else "  ATR(14): N/A")
    swing_highs, swing_lows = detect_swing_points(df_m15)
    structure, struct_details = detect_structure(df_m15, swing_highs, swing_lows)
    print(f"  Structure: {structure}")
    for d in struct_details: print(f"    - {d}")
    sweeps, choch = find_sweeps_and_choch(df_m5, swing_highs, swing_lows, df_m15)
    print(f"  Sweeps: {len(sweeps)}")
    for s in sweeps: print(f"    - {s['type']} @ {s['level']:.5f} ({s['time']})")
    if choch: print(f"  CHoCH: {choch['type']} at {choch['time']}\n    {choch['description']}")
    else: print(f"  CHoCH: None")
    obs = find_order_blocks(df_m5, sweeps)
    print(f"  Order Blocks: {len(obs)}")
    for o in obs: print(f"    - {o['type']}: {o['zone_bottom']:.5f}–{o['zone_top']:.5f}")
    all_fvgs = find_fvg(df_m5)
    recent_fvgs = [f for f in all_fvgs if pd.Timestamp(f['time'])>(NOW-timedelta(hours=24))]
    print(f"  Recent FVGs (24h): {len(recent_fvgs)}")
    for f in recent_fvgs[-3:]: print(f"    - {f['type']}: {f['gap_bottom']:.5f}–{f['gap_top']:.5f} ({f['time']})")
    score, score_reasons = score_setup(sweeps, choch, obs, recent_fvgs, structure)
    print(f"  Setup Score: {score}/10")
    for r in score_reasons: print(f"    {r}")
    direction = None
    if score>0:
        if choch:
            direction = "SHORT" if "BEARISH" in choch['type'] else "LONG"
        elif sweeps:
            direction = "SHORT" if sweeps[0]['type']=='LIQUIDITY_SWEEP_HIGH' else "LONG"
    entry_sim = simulate_entry(sweeps, current_atr, current_price, direction) if direction and current_atr else None
    if entry_sim:
        print(f"  ▶ ENTRY: {entry_sim['direction']} @ {entry_sim['entry']:.5f}")
        print(f"    SL: {entry_sim['stop_loss']:.5f} ({entry_sim['sl_pips']} pips)")
        print(f"    TP: {entry_sim['take_profit']:.5f} ({entry_sim['tp_pips']} pips)")
        print(f"    RR: {entry_sim['risk_reward']}")
    results[name] = {"current_price":current_price,"atr":current_atr,"structure":structure,
                     "structure_details":struct_details,"sweeps":sweeps,"choch":choch,
                     "order_blocks":obs,"recent_fvgs":recent_fvgs[-5:],"score":score,
                     "score_reasons":score_reasons,"entry_simulation":entry_sim}

# ── Summary ─────────────────────────────────────────────────
print("\n"+"="*60)
print("SUMMARY")
print("="*60)
valid_setups = {k:v for k,v in results.items() if v['score']>0}
if not valid_setups:
    print("\n  ❌ Sem setups válidos — nenhum par atingiu score > 0")
else:
    for n,r in valid_setups.items():
        e = r['entry_simulation']
        print(f"\n  ✅ {n} | Score: {r['score']}/10 | Structure: {r['structure']}")
        if e: print(f"     {e['direction']} @ {e['entry']:.5f} | SL: {e['stop_loss']:.5f} | TP: {e['take_profit']:.5f}")

# Save
output = {"analysis_time":NOW.strftime('%Y-%m-%d %H:%M:%S BRT'),
          "killzone":"London Open (05:00-07:00 BRT)",
          "pairs_analyzed":list(results.keys()),"valid_setups":len(valid_setups),"results":{}}
for name,res in results.items():
    output["results"][name] = {k:res[k] for k in ["current_price","atr","structure","structure_details",
        "sweeps","choch","order_blocks","recent_fvgs","score","score_reasons","entry_simulation"]}
with open('/home/roberto/.hermes/forex/killzone_analysis.json','w') as f:
    json.dump(output, f, indent=2, default=str)
print(f"\n✅ Results saved to ~/.hermes/forex/killzone_analysis.json")
