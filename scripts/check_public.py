"""Read-only recheck. Makes six sequential page GETs and fetches three public scripts."""
import hashlib
import json
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'evidence' / 'recheck'
OUT.mkdir(exist_ok=True)

class MetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.policies = []
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta' and a.get('http-equiv', '').lower() == 'content-security-policy':
            self.policies.append(a.get('content', ''))

def get(url, name):
    header = OUT / (name + '.headers.txt')
    body = OUT / (name + '.body')
    result = subprocess.run(['curl', '-sS', '--compressed', '--max-time', '30',
        '-D', str(header), '-o', str(body), '-w', '%{json}', url],
        capture_output=True, text=True, check=True)
    metrics = json.loads(result.stdout)
    # Keep readable headers; the bytes hashed below refer to decoded content.
    header.write_text('\n'.join(s.rstrip() for s in header.read_text().splitlines()).rstrip() + '\n')
    content = body.read_bytes()
    headers = {}
    for line in header.read_text().splitlines():
        if ':' in line:
            key, value = line.split(':', 1)
            headers[key.lower()] = value.strip()
    return content, headers, metrics

pages = []
for round_number in (1, 2):
    for name, path in [('home', '/'), ('contact', '/contact'), ('courses', '/bitelevate')]:
        url = 'https://www.cynbit.in' + path
        content, headers, metrics = get(url, f'{name}-{round_number}')
        parser = MetaParser()
        parser.feed(content.decode('utf-8'))
        pages.append({'round': round_number, 'url': url,
            'checked_at': datetime.now(timezone.utc).isoformat(),
            'status': metrics['http_code'], 'ttfb_seconds': metrics['time_starttransfer'],
            'cache': headers.get('x-vercel-cache'),
            'content_encoding': headers.get('content-encoding'),
            'csp': headers.get('content-security-policy'),
            'csp_meta': parser.policies,
            'x_frame_options': headers.get('x-frame-options'),
            'x_content_type_options': headers.get('x-content-type-options'),
            'hsts': headers.get('strict-transport-security'),
            'decoded_body_sha256': hashlib.sha256(content).hexdigest()})
        time.sleep(1)

# Re-fetch previously observed public assets, not guessed endpoints.
records = json.loads((ROOT / 'evidence' / 'actions.json').read_text())
selected = ['submitInquiry', 'createBitelevateCashfreeOrder', 'submitCandidateApplication']
sources = []
for name in selected:
    previous = next(r for r in records if r['action'] == name)
    content, headers, metrics = get(previous['url'], name)
    digest = hashlib.sha256(content).hexdigest()
    sources.append({'action': name, 'url': previous['url'], 'status': metrics['http_code'],
        'sha256': digest, 'matches_previous_source': digest == previous['sha256'],
        'action_declaration_present': previous['context'].encode() in content})
    time.sleep(1)
(OUT / 'results.json').write_text(json.dumps({'pages': pages, 'sources': sources}, indent=2) + '\n')
print(json.dumps({'pages': pages, 'sources': sources}, indent=2))
