# Research Sources Audit — 2026-05-24

## Problem Found

The brain's research pipeline (`forex_research_collector.py`) was producing repetitive
data because its sources were stale:

- **YouTube:** 1 channel (ICT Concepts) with placeholder video IDs including `aBcDeFgHiJk`
- **RSS:** 4 generic news feeds (BabyPips, ForexFactory, DailyFX, ForexLive) — news only, no technique
- **Web:** BabyPips Learn + Investopedia — beginner-level education, already consumed
- **Data:** Zero COT, sentiment, or order flow sources
- **Result:** Same FVG counts written to knowledge bridge every 2 hours, zero new insights

## Solution Applied

3 autonomous agents researched ~135 advanced sources. `research_sources.json` completely
overhauled with 4 new categories:

### New YouTube Channels
- **Trader Dale** — Order flow, volume profile, absorption, delta divergence
- **Wyckoff Analytics** — Official Wyckoff method channel
- ICT video IDs updated (removed placeholder, added Breaker/Turtle/Mitigation videos)

### New Web Sources (scraped by collector)
| Category | Sources | Key URL |
|----------|---------|---------|
| ICT Advanced | Breaker, Mitigation, Turtle Soup | innercircletrader.net |
| Order Flow | Delta, CVD, Footprint | atas.net, bookmap.com, trader-dale.com, forexbee.co |
| Wyckoff | Springs, Upthrusts, Effort vs Result | wyckoffanalytics.com, newtraderu.com |
| Price Action | Smart money footprints, institutional levels | newtraderu.com |

### New Data Sources (for the brain to query)
| Category | Sources | Access |
|----------|---------|--------|
| COT Reports | Barchart, COT Base, MacroMicro | Free |
| Retail Sentiment | Myfxbook, Dukascopy, FXSSI | Free |
| Economic Calendar | Trading Economics, ForexFactory | Free |

## Collector Status
- RSS + Web: Fixed (feedparser installed). 17 articles collected on first run with new sources.
- YouTube: Requires youtube-transcript-api v1.2.4 (installed). API: `YouTubeTranscriptApi().fetch(video_id, languages=[...])`.
- All sources saved to `~/.hermes/forex/research/{date}/`

## Files Updated
- `~/.hermes/forex/research_sources.json` — complete overhaul
- `~/.hermes/forex/knowledge_bridge.json` — 3 agent insights written (disc-0050, disc-0051, disc-0052)
- Research reports: `~/forex_advanced_resources.md`, `~/trading_resources.md`, `~/forex_data_sources.md`
