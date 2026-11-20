"""Tiny persistent knowledge base: chunk metadata in JSON, embeddings in .npy, hybrid search (vector + BM25, RRF fusion).
Swappable for pgvector / Chroma / Pinecone in production; the interface stays the same."""

import json
import math
import os
import re
import threading
from collections import Counter

import numpy as np

TOKEN = re.compile(r'[a-z0-9]+(?:[.\-][a-z0-9]+)*', re.I)
STOP = set(
    'a an the and or of to in on for with at by from is are was were be been it this that these those as how what '
    'when where which who why do does did can could should would will my our your i we you they he she them us me not no '
    'if then than there their about into over under per up down out'.split()
)


def tokens(text):
    return [t for t in (w.lower() for w in TOKEN.findall(text)) if t not in STOP]


class Store:
    def __init__(self, root):
        self.root = root
        os.makedirs(root, exist_ok=True)
        self.lock = threading.Lock()
        self.meta_path = os.path.join(root, 'chunks.json')
        self.vec_path = os.path.join(root, 'vectors.npy')
        self.docs_path = os.path.join(root, 'docs.json')
        self.chunks, self.docs, self.vecs = [], {}, None
        self._load()

    # ------------------------------------------------------------------ persistence
    def _load(self):
        if os.path.exists(self.meta_path):
            self.chunks = json.load(open(self.meta_path, encoding='utf-8'))
            self.docs = json.load(open(self.docs_path, encoding='utf-8'))
            self.vecs = np.load(self.vec_path) if os.path.exists(self.vec_path) else None
        self._index()

    def _save(self):
        json.dump(self.chunks, open(self.meta_path, 'w', encoding='utf-8'), ensure_ascii=False)
        json.dump(self.docs, open(self.docs_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        if self.vecs is not None:
            np.save(self.vec_path, self.vecs)
        elif os.path.exists(self.vec_path):
            os.remove(self.vec_path)

    def _index(self):
        self.tf = [Counter(tokens(c['section'] + ' ' + c['text'])) for c in self.chunks]
        self.dl = [sum(t.values()) for t in self.tf]
        self.avgdl = (sum(self.dl) / len(self.dl)) if self.dl else 1.0
        df = Counter()
        for t in self.tf:
            df.update(t.keys())
        n = len(self.tf)
        self.idf = {w: math.log(1 + (n - d + 0.5) / (d + 0.5)) for w, d in df.items()}

    # ------------------------------------------------------------------ mutations
    def add(self, doc, chunks, vectors=None):
        with self.lock:
            self.docs[doc['id']] = doc
            self.chunks.extend(c.to_dict() for c in chunks)
            if vectors is not None:
                v = np.asarray(vectors, dtype=np.float32)
                v /= np.linalg.norm(v, axis=1, keepdims=True) + 1e-9
                self.vecs = v if self.vecs is None else np.vstack([self.vecs, v])
            else:
                self.vecs = None  # mixed state -> fall back to keyword search only
            self._index()
            self._save()

    def remove(self, doc_id):
        with self.lock:
            keep = [i for i, c in enumerate(self.chunks) if c['doc_id'] != doc_id]
            self.chunks = [self.chunks[i] for i in keep]
            if self.vecs is not None:
                self.vecs = self.vecs[keep] if keep else None
            self.docs.pop(doc_id, None)
            self._index()
            self._save()

    def clear(self):
        with self.lock:
            self.chunks, self.docs, self.vecs = [], {}, None
            self._index()
            self._save()

    # ------------------------------------------------------------------ search
    def bm25(self, query, k1=1.4, b=0.75):
        q = tokens(query)
        scores = np.zeros(len(self.chunks), dtype=np.float32)
        for i, tf in enumerate(self.tf):
            s = 0.0
            for w in q:
                f = tf.get(w)
                if f:
                    s += self.idf.get(w, 0) * f * (k1 + 1) / (f + k1 * (1 - b + b * self.dl[i] / self.avgdl))
            scores[i] = s
        return scores

    def search(self, query, qvec=None, k=6, doc_ids=None):
        if not self.chunks:
            return []
        ranked_lists = []
        kw = self.bm25(query)
        ranked_lists.append(np.argsort(-kw))
        if qvec is not None and self.vecs is not None and len(self.vecs) == len(self.chunks):
            q = np.asarray(qvec, dtype=np.float32)
            q /= np.linalg.norm(q) + 1e-9
            sim = self.vecs @ q
            ranked_lists.append(np.argsort(-sim))
        else:
            sim = None
        fused = Counter()
        for lst in ranked_lists:  # reciprocal rank fusion
            for rank, idx in enumerate(lst[:40]):
                if sim is None and kw[idx] <= 0:
                    continue
                fused[int(idx)] += 1.0 / (60 + rank)
        out = []
        for idx, score in fused.most_common():
            c = self.chunks[idx]
            if doc_ids and c['doc_id'] not in doc_ids:
                continue
            out.append({**c, 'score': round(score, 5), 'sim': None if sim is None else round(float(sim[idx]), 3)})
            if len(out) >= k:
                break
        return out

    def get(self, chunk_id):
        return next((c for c in self.chunks if c['id'] == chunk_id), None)
