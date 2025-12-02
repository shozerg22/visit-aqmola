import os
import json
import hashlib
import math
from typing import List, Dict, Any, Optional
from app.config import settings
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app import models


def _ensure_dir(path: str) -> None:
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


class VectorStore:
    # Простейший файловый стор документов + наивный поиск по пересечению токенов
    def __init__(self, data_dir: str | None = None, mode: str | None = None):
        self.data_dir = data_dir or settings.RAG_DATA_DIR
        _ensure_dir(self.data_dir)
        self.mode = (mode or settings.RAG_SEARCH_MODE).lower()
        self._embeddings_enabled = False
        self._openai = None
        if self.mode == "embeddings":
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                try:
                    from openai import OpenAI
                    self._openai = OpenAI(api_key=api_key)
                    self._embeddings_enabled = True
                except Exception:
                    self._embeddings_enabled = False

    def _doc_path(self, doc_id: str) -> str:
        return os.path.join(self.data_dir, f"{doc_id}.json")

    def _embed_path(self, doc_id: str) -> str:
        return os.path.join(self.data_dir, f"{doc_id}.emb.json")

    def add_document(self, title: str, text: str, lang: str | None = None, tags: List[str] | None = None) -> Dict[str, Any]:
        payload = {
            "id": hashlib.sha1(f"{title}\n{text}".encode("utf-8")).hexdigest()[:16],
            "title": title,
            "text": text,
            "lang": (lang or "").upper() if lang else None,
            "tags": tags or [],
        }
        with open(self._doc_path(payload["id"]), "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        # Предварительно запишем эмбеддинг, если режим embeddings и доступно.
        if self.mode == "embeddings" and self._embeddings_enabled:
            vec = self._embed(f"{title} {text}")
            if vec:
                try:
                    with open(self._embed_path(payload["id"]), "w", encoding="utf-8") as ef:
                        json.dump({"embedding": vec}, ef)
                except Exception:
                    pass
        return payload

    def _iter_docs(self):
        for fname in os.listdir(self.data_dir):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(self.data_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    yield json.load(f)
            except Exception:
                continue

    def _tokenize(self, text: str) -> List[str]:
        return [t for t in text.lower().split() if t]

    def _simple_search(self, query: str, k: int) -> List[Dict[str, Any]]:
        if not query:
            return []
        q_tokens = set(self._tokenize(query))
        scored: List[Dict[str, Any]] = []
        for doc in self._iter_docs():
            text = f"{doc.get('title','')}\n{doc.get('text','')}"
            d_tokens = set(self._tokenize(text))
            inter = q_tokens.intersection(d_tokens)
            score = len(inter)
            if score > 0:
                scored.append({
                    "id": doc.get("id"),
                    "title": doc.get("title"),
                    "score": score,
                    "snippet": doc.get("text", "")[:200],
                })
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:k]

    def _tfidf_search(self, query: str, k: int) -> List[Dict[str, Any]]:
        if not query:
            return []
        docs = list(self._iter_docs())
        if not docs:
            return []
        corpus_tokens: List[List[str]] = []
        for d in docs:
            text = f"{d.get('title','')} {d.get('text','')}"
            corpus_tokens.append(self._tokenize(text))
        # Document frequency
        df: Dict[str, int] = {}
        for toks in corpus_tokens:
            for t in set(toks):
                df[t] = df.get(t, 0) + 1
        N = len(docs)
        # Query TF
        q_tokens = self._tokenize(query)
        q_tf: Dict[str, float] = {}
        for t in q_tokens:
            q_tf[t] = q_tf.get(t, 0.0) + 1.0
        for t in list(q_tf.keys()):
            q_tf[t] /= len(q_tokens) or 1
        idf: Dict[str, float] = {t: (math.log((N + 1) / (df.get(t, 0) + 1)) + 1.0) for t in df.keys()}
        results: List[Dict[str, Any]] = []
        for idx, d in enumerate(docs):
            toks = corpus_tokens[idx]
            d_tf: Dict[str, float] = {}
            for t in toks:
                d_tf[t] = d_tf.get(t, 0.0) + 1.0
            for t in list(d_tf.keys()):
                d_tf[t] /= len(toks) or 1
            num = 0.0
            denom_q = 0.0
            denom_d = 0.0
            for t in set(q_tf.keys()) | set(d_tf.keys()):
                wq = q_tf.get(t, 0.0) * idf.get(t, 0.0)
                wd = d_tf.get(t, 0.0) * idf.get(t, 0.0)
                num += wq * wd
                denom_q += wq * wq
                denom_d += wd * wd
            score = num / (math.sqrt(denom_q) * math.sqrt(denom_d) + 1e-9)
            if score > 0:
                results.append({
                    "id": d.get("id"),
                    "title": d.get("title"),
                    "score": round(score, 4),
                    "snippet": d.get("text", "")[:200],
                })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:k]

    def _embed(self, text: str) -> List[float]:
        # Возвращает вектор эмбеддинга через OpenAI; иначе пусто
        if not self._embeddings_enabled or not self._openai:
            return []
        try:
            resp = self._openai.embeddings.create(
                model=os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small"),
                input=text,
            )
            vec = resp.data[0].embedding
            return vec
        except Exception:
            return []

    def _embeddings_search(self, query: str, k: int) -> List[Dict[str, Any]]:
        # Если embeddings недоступны — fallback на tfidf
        if not self._embeddings_enabled:
            return self._tfidf_search(query, k)
        q_vec = self._embed(query)
        if not q_vec:
            return self._tfidf_search(query, k)
        results: List[Dict[str, Any]] = []
        # косинусная схожесть вручную
        import math
        q_norm = math.sqrt(sum(v * v for v in q_vec)) + 1e-9
        for d in self._iter_docs():
            doc_id = d.get("id")
            text = f"{d.get('title','')} {d.get('text','')}"
            d_vec: List[float] | None = None
            # Пытаемся прочитать из кэша
            if doc_id:
                ep = self._embed_path(doc_id)
                if os.path.exists(ep):
                    try:
                        with open(ep, "r", encoding="utf-8") as ef:
                            edata = json.load(ef)
                            d_vec = edata.get("embedding")
                    except Exception:
                        d_vec = None
            # Если нет в кэше — считаем и сохраняем
            if not d_vec:
                d_vec = self._embed(text)
                if d_vec and doc_id:
                    try:
                        with open(self._embed_path(doc_id), "w", encoding="utf-8") as ef:
                            json.dump({"embedding": d_vec}, ef)
                    except Exception:
                        pass
            if not d_vec:
                continue
            num = 0.0
            for i in range(min(len(q_vec), len(d_vec))):
                num += q_vec[i] * d_vec[i]
            d_norm = math.sqrt(sum(v * v for v in d_vec)) + 1e-9
            score = num / (q_norm * d_norm)
            if score > 0:
                results.append({
                    "id": d.get("id"),
                    "title": d.get("title"),
                    "score": round(score, 4),
                    "snippet": d.get("text", "")[:200],
                })
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:k]

    def search(self, query: str, k: int = 3) -> List[Dict[str, Any]]:
        if self.mode == "embeddings":
            return self._embeddings_search(query, k)
        if self.mode == "tfidf":
            return self._tfidf_search(query, k)
        return self._simple_search(query, k)
        # Наивный скоринг: по количеству общих токенов (без стемминга)
        if not query:
            return []
        q_tokens = set(query.lower().split())
        scored: List[Dict[str, Any]] = []
        for doc in self._iter_docs():
            text = f"{doc.get('title','')}\n{doc.get('text','')}".lower()
            d_tokens = set(text.split())
            inter = q_tokens.intersection(d_tokens)
            score = len(inter)
            if score > 0:
                snippet = doc.get("text", "")[:200]
                scored.append({
                    "id": doc.get("id"),
                    "title": doc.get("title"),
                    "score": score,
                    "snippet": snippet,
                })
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:k]


class RAGService:
    def __init__(self, store: VectorStore | None = None, mode: str | None = None):
        self.backend = settings.RAG_BACKEND
        # Fallback если pgvector выбран, но нет PostgreSQL / неподходящий DATABASE_URL
        if self.backend == 'pgvector':
            db_url = os.getenv('DATABASE_URL', '')
            if not db_url.startswith('postgresql'):
                self.backend = 'files'
        use_mode = mode or settings.RAG_SEARCH_MODE
        self.store = store or VectorStore(mode=use_mode)

    def _make_doc_id(self, title: str, text: str) -> str:
        return hashlib.sha1(f"{title}\n{text}".encode("utf-8")).hexdigest()[:16]

    async def ingest(self, title: str, text: str, lang: str | None = None, tags: List[str] | None = None, session: Optional[AsyncSession] = None) -> Dict[str, Any]:
        # File backend (legacy)
        if self.backend != 'pgvector':
            return self.store.add_document(title=title, text=text, lang=lang, tags=tags)
        # pgvector backend requires embeddings mode for semantic value; still store raw even if simple
        doc_id = self._make_doc_id(title, text)
        tag_str = ",".join(tags or [])
        embedding: List[float] = []
        if self.store.mode == 'embeddings':
            embedding = self.store._embed(f"{title} {text}") or []
        if not session:
            raise RuntimeError("AsyncSession required for pgvector backend")
        # Upsert (simple): try select then insert if missing
        existing = await session.execute(select(models.RAGEmbedding).where(models.RAGEmbedding.doc_id == doc_id))
        row = existing.scalars().first()
        if not row:
            row = models.RAGEmbedding(doc_id=doc_id, title=title, text=text, tags=tag_str)
            if hasattr(row, 'embedding') and isinstance(embedding, list) and embedding:
                row.embedding = embedding  # type: ignore
            session.add(row)
            await session.commit()
        return {"id": doc_id, "title": title, "tags": tags or []}

    async def search(self, query: str, k: int = 3, session: Optional[AsyncSession] = None) -> List[Dict[str, Any]]:
        if self.backend != 'pgvector':
            return self.store.search(query, k=k)
        if not session:
            raise RuntimeError("AsyncSession required for pgvector backend search")
        # If embeddings mode and embeddings available, perform DB fetch then compute cosine similarity locally.
        use_embeddings = (self.store.mode == 'embeddings' and self.store._embeddings_enabled)
        q_vec: List[float] = []
        if use_embeddings:
            q_vec = self.store._embed(query) or []
        rows = await session.execute(select(models.RAGEmbedding))
        items = rows.scalars().all()
        scored: List[Dict[str, Any]] = []
        if use_embeddings and q_vec:
            q_norm = math.sqrt(sum(v*v for v in q_vec)) + 1e-9
            for r in items:
                d_vec = []
                if hasattr(r, 'embedding') and isinstance(r.embedding, list) and r.embedding:
                    d_vec = r.embedding
                if not d_vec:
                    continue
                num = 0.0
                for i in range(min(len(q_vec), len(d_vec))):
                    num += q_vec[i] * d_vec[i]
                d_norm = math.sqrt(sum(v*v for v in d_vec)) + 1e-9
                score = num / (q_norm * d_norm)
                if score > 0:
                    scored.append({"id": r.doc_id, "title": r.title, "score": round(score,4), "snippet": (r.text or '')[:200]})
            scored.sort(key=lambda x: x['score'], reverse=True)
            return scored[:k]
        # Fallback simple token overlap (DB rows)
        q_tokens = set(query.lower().split())
        for r in items:
            text = f"{r.title or ''} {r.text or ''}".lower()
            d_tokens = set(text.split())
            inter = q_tokens.intersection(d_tokens)
            score = len(inter)
            if score > 0:
                scored.append({"id": r.doc_id, "title": r.title, "score": score, "snippet": (r.text or '')[:200]})
        scored.sort(key=lambda x: x['score'], reverse=True)
        return scored[:k]

    async def get_context(self, query: str, session: Optional[AsyncSession] = None) -> str:
        if self.backend == 'pgvector':
            docs = await self.search(query, k=3, session=session)
        else:
            docs = self.store.search(query, k=3)
        if isinstance(docs, list) and docs and isinstance(docs[0], dict):
            return "\n".join(f"{d['title']}: {d['snippet']}" for d in docs)
        # Fallback for старой формы (если провайдер менялся)
        return "\n".join(docs) if isinstance(docs, list) else ""

    async def ingest_batch(self, items: List[Dict[str, Any]], session: Optional[AsyncSession] = None) -> Dict[str, Any]:
        ok = 0; fail = 0; ids: List[str] = []
        for it in items:
            try:
                doc = await self.ingest(title=it.get("title", ""), text=it.get("text", ""), lang=it.get("lang"), tags=it.get("tags"), session=session)
                ids.append(doc.get("id", "")); ok += 1
            except Exception:
                fail += 1
        return {"ok": ok, "fail": fail, "ids": ids}


rag_service = RAGService()
