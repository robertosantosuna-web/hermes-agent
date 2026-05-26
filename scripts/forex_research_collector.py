#!/usr/bin/env python3
"""
Forex Research Collector — Coleta automática de material de estudo.
Fontes: YouTube (transcripts), RSS feeds, sites de forex.

no_agent — zero tokens. Apenas coleta e salva.
Roda diariamente às 03:00 BRT (madrugada, sem tráfego).

Output: ~/.hermes/forex/research/{date}/
"""
import json, os, sys, hashlib, time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import xml.etree.ElementTree as ET

HERMES = Path(os.path.expanduser('~/.hermes'))
RESEARCH_DIR = HERMES / 'forex' / 'research'
CONFIG_FILE = HERMES / 'forex' / 'research_sources.json'

# ─── Default Sources ───────────────────────────────────────────────────

DEFAULT_SOURCES = {
    "youtube_channels": [
        {
            "name": "ICT Concepts",
            "channel_id": "UCG5_OTqBh6HdR5VPS0zR3_Q",
            "description": "Inner Circle Trader — institutional trading concepts",
            "priority": "high",
            "video_ids": [
                "tZViCrc7Nfc",  # ICT Mentorship 2024 Core Content
                "aBcDeFgHiJk",  # placeholder
            ]
        },
        {
            "name": "Forex Education",
            "channel_id": "UCxT5luy_Iz3inS7J8LkCgHg",
            "description": "General forex education",
            "priority": "medium",
            "video_ids": []
        }
    ],
    "rss_feeds": [
        {
            "name": "BabyPips",
            "url": "https://www.babypips.com/blogs/piponomics.rss",
            "priority": "high",
            "category": "education"
        },
        {
            "name": "ForexFactory News",
            "url": "https://www.forexfactory.com/news_rss",
            "priority": "high", 
            "category": "news"
        },
        {
            "name": "DailyFX",
            "url": "https://www.dailyfx.com/feeds/all",
            "priority": "medium",
            "category": "analysis"
        },
        {
            "name": "ForexLive",
            "url": "https://www.forexlive.com/feed",
            "priority": "medium",
            "category": "news"
        }
    ],
    "web_sources": [
        {
            "name": "BabyPips Learn",
            "url": "https://www.babypips.com/learn/forex",
            "priority": "high",
            "category": "education",
            "method": "scrape_sections"
        },
        {
            "name": "Investopedia Forex",
            "url": "https://www.investopedia.com/forex-4427687",
            "priority": "medium",
            "category": "education"
        }
    ]
}

# ─── Helpers ────────────────────────────────────────────────────────────

def load_config():
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except:
            pass
    # Save defaults
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(DEFAULT_SOURCES, indent=2))
    return DEFAULT_SOURCES

def save_article(date_dir, source_name, title, content, content_type="text"):
    """Save collected article to research directory."""
    date_dir.mkdir(parents=True, exist_ok=True)
    
    safe_title = "".join(c for c in title[:80] if c.isalnum() or c in ' _-').strip()
    if not safe_title:
        safe_title = hashlib.md5(title.encode()).hexdigest()[:8]
    
    filename = f"{source_name}_{safe_title}.{content_type}"
    filepath = date_dir / filename
    
    # Don't overwrite if exists
    if filepath.exists():
        return None
    
    filepath.write_text(content)
    return str(filepath)

def fetch_url(url, timeout=15):
    """Fetch URL with standard browser headers."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    try:
        req = Request(url, headers=headers)
        resp = urlopen(req, timeout=timeout)
        return resp.read().decode('utf-8', errors='replace')
    except (URLError, HTTPError, OSError) as e:
        return None

# ─── YouTube Collection ─────────────────────────────────────────────────

def collect_youtube(date_dir, channels):
    """Fetch transcripts from curated YouTube channels."""
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api.formatters import TextFormatter
    
    collected = []
    formatter = TextFormatter()
    yt_api = YouTubeTranscriptApi()
    
    for channel in channels:
        channel_name = channel['name']
        video_ids = channel.get('video_ids', [])
        
        if not video_ids:
            continue
        
        for vid in video_ids:
            if vid == "aBcDeFgHiJk":  # Skip placeholder
                continue
            
            try:
                # New API: instance.fetch(video_id, languages=[...])
                transcript = yt_api.fetch(vid, languages=['en', 'pt'])
                text = formatter.format_transcript(transcript)
                
                # Save
                path = save_article(date_dir, channel_name, f"transcript_{vid}", text, "txt")
                if path:
                    collected.append({
                        'source': channel_name,
                        'type': 'youtube',
                        'video_id': vid,
                        'path': path,
                        'chars': len(text),
                    })
                
                # Rate limit
                time.sleep(2)
                
            except Exception as e:
                # Video might not have transcript or be unavailable
                pass
    
    return collected

# ─── RSS Collection ─────────────────────────────────────────────────────

def collect_rss(date_dir, feeds):
    """Fetch articles from RSS feeds."""
    import feedparser
    
    collected = []
    
    for feed in feeds:
        try:
            parsed = feedparser.parse(feed['url'])
            
            for entry in parsed.entries[:5]:  # Last 5 articles
                title = entry.get('title', 'Untitled')
                content = entry.get('summary', entry.get('description', ''))
                link = entry.get('link', '')
                
                # Clean HTML
                import re
                content = re.sub(r'<[^>]+>', ' ', content)
                content = re.sub(r'\s+', ' ', content).strip()
                
                full = f"Title: {title}\nSource: {feed['name']}\nLink: {link}\n\n{content}"
                
                path = save_article(date_dir, feed['name'], title, full, "txt")
                if path:
                    collected.append({
                        'source': feed['name'],
                        'type': 'rss',
                        'title': title,
                        'path': path,
                        'chars': len(full),
                    })
        except Exception as e:
            pass
    
    return collected

# ─── Web Collection ─────────────────────────────────────────────────────

def collect_web(date_dir, sources):
    """Fetch educational content from forex websites."""
    import re
    
    collected = []
    
    for source in sources:
        try:
            html = fetch_url(source['url'])
            if not html:
                continue
            
            # Extract text content (simple approach)
            # Remove scripts, styles, and HTML tags
            html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
            html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', ' ', html)
            text = re.sub(r'\s+', ' ', text).strip()
            
            # Limit size
            text = text[:50000]
            
            if len(text) > 500:
                path = save_article(date_dir, source['name'], source['category'], text, "txt")
                if path:
                    collected.append({
                        'source': source['name'],
                        'type': 'web',
                        'category': source.get('category', ''),
                        'path': path,
                        'chars': len(text),
                    })
        except Exception as e:
            pass
    
    return collected

# ─── BabyPips Learn Scraper ─────────────────────────────────────────────

def collect_babypips(date_dir):
    """Scrape BabyPips School of Pipsology (structured forex education)."""
    collected = []
    
    # BabyPips school pages are well-structured
    base_url = "https://www.babypips.com/learn/forex/"
    sections = [
        "what-is-forex",
        "how-to-make-money-trading-forex",
        "technical-analysis",
        "fundamental-analysis",
        "sentiment-analysis",
        "trading-strategies",
        "risk-management",
    ]
    
    for section in sections:
        try:
            html = fetch_url(base_url + section)
            if not html:
                continue
            
            import re
            html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
            html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
            text = re.sub(r'<[^>]+>', ' ', html)
            text = re.sub(r'\s+', ' ', text).strip()[:30000]
            
            if len(text) > 300:
                path = save_article(date_dir, "BabyPips", section, text, "txt")
                if path:
                    collected.append({
                        'source': 'BabyPips',
                        'type': 'education',
                        'section': section,
                        'path': path,
                    })
            
            time.sleep(2)  # Be respectful
        except:
            pass
    
    return collected

# ─── Main ───────────────────────────────────────────────────────────────

def main():
    now = datetime.now(timezone.utc)
    today = now.strftime('%Y-%m-%d')
    date_dir = RESEARCH_DIR / today
    
    print(f"📚 Forex Research Collector — {today}")
    
    config = load_config()
    
    all_collected = []
    
    # 1. YouTube transcripts
    print("▶ YouTube transcripts...")
    yt = collect_youtube(date_dir, config.get('youtube_channels', []))
    all_collected.extend(yt)
    print(f"  {len(yt)} transcripts")
    
    # 2. RSS feeds
    print("▶ RSS feeds...")
    rss = collect_rss(date_dir, config.get('rss_feeds', []))
    all_collected.extend(rss)
    print(f"  {len(rss)} articles")
    
    # 3. Web content
    print("▶ Web content...")
    web = collect_web(date_dir, config.get('web_sources', []))
    all_collected.extend(web)
    print(f"  {len(web)} pages")
    
    # 4. BabyPips school
    print("▶ BabyPips Learn...")
    bp = collect_babypips(date_dir)
    all_collected.extend(bp)
    print(f"  {len(bp)} sections")
    
    # Summary
    summary = {
        'date': today,
        'total_collected': len(all_collected),
        'by_type': {},
        'items': all_collected,
    }
    
    for item in all_collected:
        t = item.get('type', 'unknown')
        summary['by_type'][t] = summary['by_type'].get(t, 0) + 1
    
    summary_path = date_dir / '_summary.json'
    summary_path.write_text(json.dumps(summary, indent=2, default=str))
    
    print(f"\n✅ Total: {len(all_collected)} itens coletados")
    for t, n in summary['by_type'].items():
        print(f"  {t}: {n}")

if __name__ == '__main__':
    main()
