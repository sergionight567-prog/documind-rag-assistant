"""PDF / text ingestion: page-aware extraction and chunking with section headings kept as context."""

import hashlib
import re
from dataclasses import asdict, dataclass

import pymupdf

CHUNK_CHARS = 1100  # ~250 tokens: small enough to cite precisely, big enough to keep a rule together
OVERLAP_CHARS = 180


@dataclass
class Chunk:
    id: str
    doc_id: str
    doc_title: str
    page: int
    section: str
    text: str

    def to_dict(self):
        return asdict(self)


def _clean(t: str) -> str:
    t = t.replace('­', '').replace(' ', ' ')
    t = re.sub(r'[ \t]+', ' ', t)
    t = re.sub(r'\n{3,}', '\n\n', t)
    return t.strip()


def extract_pdf(path):
    """Return [(page_no, section, text)], skipping running headers/footers."""
    doc = pymupdf.open(path)
    out, section, h1 = [], '', ''
    for pno, page in enumerate(doc, start=1):
        h = page.rect.height
        # drop header/footer lines: blocks in the top 7% or bottom 6% of the page
        keep = []
        d = page.get_text('dict')
        for b in d['blocks']:
            if 'lines' not in b:
                continue
            y0, y1 = b['bbox'][1], b['bbox'][3]
            if y1 < h * 0.07 or y0 > h * 0.94:
                continue
            spans = [s for line in b['lines'] for s in line['spans'] if s['text'].strip()]
            if not spans:
                continue
            text = _clean(' '.join(''.join(s['text'] for s in line['spans']) for line in b['lines']))
            sizes = [s['size'] for s in spans]
            keep.append((text, max(sizes), all('Bold' in s['font'] or 'SemiBold' in s['font'] for s in spans)))
        weight = {}
        for text, size, _ in keep:  # body size = the size carrying the most characters
            weight[round(size, 1)] = weight.get(round(size, 1), 0) + len(text)
        body = max(weight, key=weight.get) if weight else 10
        buf = []
        for text, size, bold in keep:
            short = len(text) < 90 and not text.endswith('.')
            is_h1 = short and size >= body * 1.25
            is_h2 = short and bold and body * 1.05 <= size < body * 1.25
            if is_h1 or is_h2:
                if buf:
                    out.append((pno, section, '\n'.join(buf)))
                    buf = []
                if is_h1:
                    h1 = text
                    section = text
                else:
                    section = f'{h1} › {text}' if h1 else text
            else:
                buf.append(text)
        if buf:
            out.append((pno, section, '\n'.join(buf)))
    return out, doc.metadata.get('title') or ''


def extract_text_file(path):
    with open(path, encoding='utf-8', errors='ignore') as f:
        txt = _clean(f.read())
    return [(1, '', txt)], ''


def chunk(doc_id, doc_title, pieces):
    """Merge consecutive pieces of the same page+section, then split long ones with overlap."""
    chunks = []
    merged = []
    for pno, sec, txt in pieces:
        if merged and merged[-1][0] == pno and merged[-1][1] == sec and len(merged[-1][2]) + len(txt) < CHUNK_CHARS:
            merged[-1] = (pno, sec, merged[-1][2] + '\n' + txt)
        else:
            merged.append((pno, sec, txt))
    for pno, sec, txt in merged:
        start = 0
        while start < len(txt):
            end = min(len(txt), start + CHUNK_CHARS)
            if end < len(txt):  # break on a sentence/line boundary when possible
                cut = max(txt.rfind('\n', start, end), txt.rfind('. ', start, end))
                if cut > start + CHUNK_CHARS * 0.5:
                    end = cut + 1
            body = txt[start:end].strip()
            if len(body) > 40:
                cid = hashlib.sha1(f'{doc_id}:{pno}:{start}:{body[:40]}'.encode()).hexdigest()[:12]
                chunks.append(Chunk(cid, doc_id, doc_title, pno, sec, body))
            if end >= len(txt):
                break
            start = max(end - OVERLAP_CHARS, start + 1)
    return chunks


def ingest(path, doc_id, display_title=None):
    if path.lower().endswith('.pdf'):
        pieces, meta_title = extract_pdf(path)
    else:
        pieces, meta_title = extract_text_file(path)
    title = display_title or meta_title or path.rsplit('/', 1)[-1]
    pages = max((p for p, _, _ in pieces), default=1)
    return chunk(doc_id, title, pieces), title, pages
