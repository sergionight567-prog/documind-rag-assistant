"""DocuMind - AI assistant that answers questions from your own documents, with page-level citations.
Run:  uvicorn app.main:app --port 8000"""

import hashlib
import json
import os
import re
import shutil
import time
from collections import defaultdict, deque

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import llm
from .ingest import ingest
from .store import Store

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'data')
FILES = os.path.join(DATA, 'files')
SAMPLES = os.path.join(ROOT, 'sample_docs')
COMPANY = os.getenv('WORKSPACE_NAME', 'Solvane Energy')
MAX_UPLOAD_MB = 25
MAX_PAGES = int(os.getenv('MAX_PAGES', '80'))
os.makedirs(FILES, exist_ok=True)

app = FastAPI(title='DocuMind')
store = Store(os.path.join(DATA, 'index'))
app.mount('/static', StaticFiles(directory=os.path.join(ROOT, 'static')), name='static')


# ---------------------------------------------------------------------------------------- knowledge base
def add_file(path, title=None):
    doc_id = hashlib.sha1(open(path, 'rb').read()).hexdigest()[:10]
    if doc_id in store.docs:
        return store.docs[doc_id]
    dst = os.path.join(FILES, doc_id + os.path.splitext(path)[1].lower())
    if os.path.abspath(path) != os.path.abspath(dst):
        shutil.copyfile(path, dst)
    chunks, doc_title, pages = ingest(dst, doc_id, title)
    if pages > MAX_PAGES:
        os.remove(dst)
        raise HTTPException(413, f'This demo accepts documents up to {MAX_PAGES} pages.')
    vecs = llm.embed([f'{c.doc_title} - {c.section}\n{c.text}' for c in chunks]) if llm.can_embed() and chunks else None
    doc = {
        'id': doc_id,
        'title': doc_title,
        'file': os.path.basename(dst),
        'pages': pages,
        'chunks': len(chunks),
        'added': int(time.time()),
    }
    store.add(doc, chunks, vecs)
    return doc


def load_samples():
    for f in sorted(os.listdir(SAMPLES)):
        if f.lower().endswith(('.pdf', '.txt', '.md')):
            add_file(os.path.join(SAMPLES, f))


@app.on_event('startup')
def startup():
    if not store.docs:
        load_samples()


# ---------------------------------------------------------------------------------------- tiny rate limit (public demo)
HITS = defaultdict(deque)


def client_ip(request):
    fwd = request.headers.get('x-forwarded-for', '')
    return fwd.split(',')[0].strip() if fwd else (request.client.host if request.client else 'x')


DAILY_CAP = int(os.getenv('DAILY_CAP', '300'))  # public demo: hard cap on model calls per day, protects the API budget
_day = {'date': '', 'count': 0}


def over_daily_cap():
    today = time.strftime('%Y-%m-%d')
    if _day['date'] != today:
        _day.update(date=today, count=0)
    _day['count'] += 1
    return _day['count'] > DAILY_CAP


def limited(ip, n=30, window=600):
    q = HITS[ip]
    now = time.time()
    while q and now - q[0] > window:
        q.popleft()
    if len(q) >= n:
        return True
    q.append(now)
    return False


# ---------------------------------------------------------------------------------------- API
@app.get('/', response_class=HTMLResponse)
def index():
    return open(os.path.join(ROOT, 'static', 'index.html'), encoding='utf-8').read()


@app.get('/api/status')
def status():
    return {
        'workspace': COMPANY,
        'provider': llm.PROVIDER,
        'model': llm.chat_model(),
        'semantic_search': store.vecs is not None,
        'documents': len(store.docs),
        'chunks': len(store.chunks),
    }


@app.get('/api/docs')
def docs():
    return sorted(store.docs.values(), key=lambda d: d['added'])


@app.post('/api/docs')
async def upload(file: UploadFile = File(...)):
    name = os.path.basename(file.filename or 'document')
    if not name.lower().endswith(('.pdf', '.txt', '.md')):
        raise HTTPException(400, 'Please upload a PDF, TXT or Markdown file.')
    data = await file.read()
    if len(data) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f'Files up to {MAX_UPLOAD_MB} MB, please.')
    tmp = os.path.join(DATA, 'upload_' + re.sub(r'[^\w.\-]', '_', name))
    open(tmp, 'wb').write(data)
    try:
        title = os.path.splitext(name)[0].replace('_', ' ')
        doc = add_file(tmp, title=title)
    finally:
        os.remove(tmp)
    if not doc['chunks']:
        store.remove(doc['id'])
        raise HTTPException(422, 'No readable text found (scanned PDFs need OCR, which this demo does not run).')
    return doc


@app.delete('/api/docs/{doc_id}')
def delete(doc_id: str):
    d = store.docs.get(doc_id)
    if not d:
        raise HTTPException(404)
    store.remove(doc_id)
    try:
        os.remove(os.path.join(FILES, d['file']))
    except OSError:
        pass
    return {'ok': True}


@app.post('/api/reset')
def reset():
    store.clear()
    for f in os.listdir(FILES):
        os.remove(os.path.join(FILES, f))
    load_samples()
    return docs()


@app.get('/files/{name}')
def get_file(name: str):
    p = os.path.join(FILES, os.path.basename(name))
    if not os.path.exists(p):
        raise HTTPException(404)
    return FileResponse(p, media_type='application/pdf' if p.endswith('.pdf') else 'text/plain')


class Ask(BaseModel):
    question: str
    history: list = []
    doc_ids: list = []


SYSTEM = """You are DocuMind, a careful assistant for {company}. You answer questions using ONLY the numbered excerpts from the company's documents below.

Rules:
- Cite every factual statement with the excerpt number in square brackets right after it, e.g. "... within 30 days [2]." Use several when needed: [1][3].
- If the excerpts do not contain the answer, say in one sentence that the documents don't cover it, with no citations. If an excerpt names who to contact about it, add who. Never guess or use outside knowledge.
- Reply entirely in the language of the question: translate the wording of rules and times too. Keep only product names, model numbers and error codes as written, and keep numbers exact.
- Never point to "above", "below" or "this section"; the reader cannot see the document. Say what it says instead.
- Start with the direct answer in one or two sentences. Add short bullet points only when they help (steps, lists, conditions).
- Use **bold** for the key figure or rule. No headings, no preamble, no closing pleasantries.

Excerpts:
{excerpts}"""

CONDENSE = """Rewrite the user's latest message as one standalone search query for the company's documents, using the conversation for context. Keep the user's language and any codes or product names. Output only the query."""


def sse(event, data):
    return f'event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n'


@app.post('/api/ask')
def ask(body: Ask, request: Request):
    q = (body.question or '').strip()[:1200]
    if not q:
        raise HTTPException(400, 'Empty question')
    if limited(client_ip(request)):
        raise HTTPException(429, 'Too many questions in a short time - please wait a few minutes.')
    if over_daily_cap():
        raise HTTPException(429, 'The public demo has reached its daily limit. Please come back tomorrow.')
    history = [m for m in body.history[-6:] if m.get('role') in ('user', 'assistant') and m.get('content')]

    def gen():
        t0 = time.time()
        query = q
        if history and llm.PROVIDER != 'none':
            try:
                convo = '\n'.join(f'{m["role"]}: {m["content"][:600]}' for m in history) + f'\nuser: {q}'
                query = llm.complete(CONDENSE, [{'role': 'user', 'content': convo}], max_tokens=80).strip() or q
            except Exception:
                query = q
        qvec = None
        if llm.can_embed() and store.vecs is not None:
            qvec = llm.embed([query])[0]
        hits = store.search(query, qvec, k=6, doc_ids=body.doc_ids or None)
        sources = [
            {
                'n': i + 1,
                'id': h['id'],
                'doc_id': h['doc_id'],
                'doc_title': h['doc_title'],
                'page': h['page'],
                'section': h['section'],
                'text': h['text'],
                'file': store.docs.get(h['doc_id'], {}).get('file'),
            }
            for i, h in enumerate(hits)
        ]
        yield sse('sources', {'query': query, 'sources': sources})
        if not hits:
            yield sse('token', {'t': "I couldn't find anything about this in the documents."})
            yield sse('done', {'ms': int((time.time() - t0) * 1000)})
            return
        excerpts = '\n\n'.join(
            f'[{s["n"]}] ({s["doc_title"]}, page {s["page"]}, {s["section"]})\n{s["text"]}' for s in sources
        )
        msgs = history + [{'role': 'user', 'content': q}]
        try:
            for t in llm.stream(SYSTEM.format(company=COMPANY, excerpts=excerpts), msgs):
                yield sse('token', {'t': t})
        except Exception as e:
            yield sse('error', {'message': f'The model could not answer right now ({type(e).__name__}).'})
        yield sse('done', {'ms': int((time.time() - t0) * 1000), 'model': llm.chat_model()})

    return StreamingResponse(
        gen(), media_type='text/event-stream', headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'}
    )
