#!/usr/bin/env python3
"""Check Gmail for emails from specific senders or with keywords.
Usage: python3 check_email.py [--sender SENDER] [--keyword KEYWORD] [--days N] [--limit N]
"""
import imaplib, email, re, sys, os
from email.header import decode_header
from datetime import datetime, timedelta

CREDS = {
    'email': 'robertosantos.una@gmail.com',
    'password': 'exnlrvfswckioces',
}

def clean_html(html):
    """Remove style/head/script tags and extract text from HTML."""
    html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL)
    html = re.sub(r'<head>.*?</head>', '', html, flags=re.DOTALL)
    html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    html = re.sub(r'<br[^>]*>', '\n', html)
    html = re.sub(r'<[^>]+>', '', html)
    html = re.sub(r'&nbsp;', ' ', html)
    html = re.sub(r'&amp;', '&', html)
    html = re.sub(r'\n\s*\n\s*\n', '\n\n', html)
    return html

def search_emails(sender=None, keyword=None, days=14, limit=20):
    """Search Gmail INBOX and return matching emails."""
    mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
    mail.login(CREDS['email'], CREDS['password'])
    mail.select('INBOX')
    
    # Build search query
    since_date = (datetime.now() - timedelta(days=days)).strftime('%d-%b-%Y')
    query_parts = [f'SINCE "{since_date}"']
    if sender:
        query_parts.append(f'FROM "{sender}"')
    
    query = ' '.join(query_parts)
    status, msgs = mail.search(None, query)
    ids = msgs[0].split()
    
    # Limit results (newest first)
    ids = ids[-limit:] if len(ids) > limit else ids
    
    results = []
    for mid in reversed(ids):
        status, data = mail.fetch(mid, '(RFC822)')
        msg = email.message_from_bytes(data[0][1])
        
        subj_raw = decode_header(msg['Subject'])[0][0]
        subj = subj_raw.decode() if isinstance(subj_raw, bytes) else str(subj_raw)
        date = msg['Date']
        
        body = ''
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == 'text/plain':
                    body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                    break
                elif part.get_content_type() == 'text/html':
                    html = part.get_payload(decode=True).decode('utf-8', errors='replace')
                    body = clean_html(html)
        else:
            body = msg.get_payload(decode=True).decode('utf-8', errors='replace')
            if '<html' in body.lower():
                body = clean_html(body)
        
        # Filter by keyword if specified
        if keyword and keyword.lower() not in subj.lower() and keyword.lower() not in body.lower():
            continue
        
        # Filter boilerplate
        skip = ['cancelar', 'inscrição', 'newsletter', 'direitos', 'visualizar',
                'navegador', 'unsubscribe', 'instagram', 'facebook', 'whatsapp',
                'google play', 'app store', 'baixar app', 'política de privacidade']
        lines = [l.strip() for l in body.split('\n') if len(l.strip()) > 10]
        lines = [l for l in lines if not any(k in l.lower() for k in skip)]
        
        results.append({
            'date': date,
            'subject': subj,
            'body_clean': '\n'.join(lines[:30]),
        })
    
    mail.logout()
    return results

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Check Gmail for emails')
    parser.add_argument('--sender', help='Sender to filter by (e.g. 99freelas)')
    parser.add_argument('--keyword', help='Keyword to search in subject/body')
    parser.add_argument('--days', type=int, default=14, help='Days to look back')
    parser.add_argument('--limit', type=int, default=20, help='Max emails to return')
    args = parser.parse_args()
    
    if not args.sender and not args.keyword:
        parser.error('Must specify --sender or --keyword')
    
    results = search_emails(sender=args.sender, keyword=args.keyword,
                           days=args.days, limit=args.limit)
    
    print(f'Found {len(results)} emails')
    print()
    for r in results:
        print(f'[{r["date"]}] {r["subject"][:120]}')
        print(r['body_clean'][:400])
        print('---')
