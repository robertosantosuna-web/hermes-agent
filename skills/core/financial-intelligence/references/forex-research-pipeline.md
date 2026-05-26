# Forex Research Pipeline

Pipeline de pesquisa e estudo de padrões forex, integrado ao cérebro bi-neural.

## MÓDULOS

### 1. Research Collector (`forex_research_collector.py`)
- **Schedule:** diário 03:00 BRT (no_agent, zero tokens)
- **Fontes RSS:** BabyPips, ForexFactory, DailyFX, ForexLive
- **YouTube:** ICT Concepts, Forex Education (config: `~/.hermes/forex/research_sources.json`)
- **Web:** BabyPips School of Pipsology, Investopedia Forex
- **Output:** `~/.hermes/forex/research/YYYY-MM-DD/`

### 2. Chart Pattern Study (`chart_pattern_study.py`)
- **Schedule:** seg-sex 08:00 BRT (no_agent, zero tokens)
- **Padrões detectados:** CHoCH, FVG, Order Blocks, Structure Breaks (BOS), Liquidity Levels
- **Método:** Fractal swing detection + ICT concepts
- **Output:** `~/.hermes/forex/patterns/pattern_library.json` (cumulativo)
- **Reports diários:** `~/.hermes/forex/patterns/YYYY-MM-DD/pattern_report.json`
- **ASCII charts:** renderizados para inspeção visual de setups high-quality

### 3. Weekly Analyzer (LLM)
- **Schedule:** domingo 11:00 BRT (~500 tokens/semana)
- **Input:** Research collector + Pattern library + Trade performance + Pair weights
- **Output:** Insights acionáveis, alertas, recomendações

## INTEGRAÇÃO COM NEURAL KB

O Chart Pattern Study escreve na Neural KB:
- `chart_patterns.dominant_patterns` — padrões mais frequentes
- `chart_patterns.pattern_quality_by_pair` — setups high-quality por par
- Cria sinapses para N. Accumbens quando detecta divergência (padrões de qualidade em par pausado)

O N. Accumbens escreve na Neural KB:
- `n_accumbens.pair_weights` — WR real por par
- `n_accumbens.learning_observations` — mudanças de recomendação
- Cria sinapses para Chart Patterns com pares ativos no regime atual

## FONTES DE DADOS EXTERNAS

### RSS Feeds ativos
| Fonte | URL | Categoria |
|-------|-----|-----------|
| BabyPips | babypips.com/blogs/piponomics.rss | educação |
| ForexFactory | forexfactory.com/news_rss | notícias |
| DailyFX | dailyfx.com/feeds/all | análise |
| ForexLive | forexlive.com/feed | notícias |

### YouTube (configurável)
Video IDs em `~/.hermes/forex/research_sources.json` → `youtube_channels[].video_ids[]`
API: `youtube-transcript-api` (instalado via pip)

## PATTERN LIBRARY

`~/.hermes/forex/patterns/pattern_library.json`:
- 5 tipos de padrão ICT
- Máximo 50 exemplos por tipo (rotativo)
- Cada exemplo inclui: timestamp, preço, qualidade, snapshot de candles, ASCII chart
- Primeira execução: 20,650 padrões em 5 pares
