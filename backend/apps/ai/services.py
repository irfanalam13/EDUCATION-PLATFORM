from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from typing import Iterable

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import AIDocument, AIChatMessage, AIChatSession, AIKnowledgeChunk


FALLBACK_EMBEDDING_MODEL = "local-hash-v1"
FALLBACK_EMBEDDING_DIM = 192


@dataclass
class RetrievedChunk:
    chunk: AIKnowledgeChunk
    score: float


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def chunk_text(text: str, *, size: int = 1200, overlap: int = 180) -> list[str]:
    clean = normalize_text(text)
    if not clean:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(clean):
        end = min(len(clean), start + size)
        if end < len(clean):
            boundary = max(clean.rfind(". ", start, end), clean.rfind("\n", start, end))
            if boundary > start + size // 2:
                end = boundary + 1
        chunk = clean[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(clean):
            break
        start = max(0, end - overlap)
    return chunks


def fallback_embedding(text: str, *, dim: int = FALLBACK_EMBEDDING_DIM) -> list[float]:
    vector = [0.0] * dim
    words = re.findall(r"[A-Za-z0-9_]+", (text or "").lower())
    for word in words:
        digest = hashlib.blake2b(word.encode("utf-8"), digest_size=8).digest()
        bucket = int.from_bytes(digest[:4], "big") % dim
        sign = -1.0 if digest[4] % 2 else 1.0
        vector[bucket] += sign

    norm = math.sqrt(sum(v * v for v in vector)) or 1.0
    return [round(v / norm, 6) for v in vector]


def embed_text(text: str) -> tuple[list[float], str]:
    """Embed text for retrieval.

    Anthropic does not provide an embeddings endpoint, so retrieval uses a
    pluggable provider (``AI_EMBEDDING_PROVIDER``): Voyage (Anthropic's
    recommended partner), OpenAI, or a local hash-based fallback that needs no
    key. Any provider failure degrades gracefully to the local fallback so the
    assistant keeps working.
    """
    provider = getattr(settings, "AI_EMBEDDING_PROVIDER", "local").lower()

    if provider == "voyage":
        api_key = getattr(settings, "VOYAGE_API_KEY", "")
        model = getattr(settings, "VOYAGE_EMBEDDING_MODEL", "voyage-3.5")
        if api_key:
            try:
                import voyageai

                client = voyageai.Client(api_key=api_key)
                result = client.embed([text[:8000]], model=model, input_type="document")
                return list(result.embeddings[0]), model
            except Exception:
                pass

    elif provider == "openai":
        api_key = getattr(settings, "OPENAI_API_KEY", "")
        model = getattr(settings, "AI_EMBEDDING_MODEL", "text-embedding-3-small")
        if api_key:
            try:
                from openai import OpenAI

                client = OpenAI(api_key=api_key)
                response = client.embeddings.create(model=model, input=text[:8000])
                return list(response.data[0].embedding), model
            except Exception:
                pass

    return fallback_embedding(text), FALLBACK_EMBEDDING_MODEL


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right:
        return 0.0
    length = min(len(left), len(right))
    dot = sum(float(left[i]) * float(right[i]) for i in range(length))
    left_norm = math.sqrt(sum(float(left[i]) ** 2 for i in range(length))) or 1.0
    right_norm = math.sqrt(sum(float(right[i]) ** 2 for i in range(length))) or 1.0
    return dot / (left_norm * right_norm)


def extract_pdf_text(document: AIDocument) -> tuple[str, int]:
    try:
        import fitz
    except ImportError as exc:
        raise RuntimeError("PyMuPDF is not installed. Install pymupdf to process PDFs.") from exc

    pages: list[str] = []
    with document.file.open("rb") as file_obj:
        pdf = fitz.open(stream=file_obj.read(), filetype="pdf")
        for page in pdf:
            pages.append(page.get_text("text"))
        page_count = pdf.page_count
        pdf.close()

    return "\n\n".join(pages), page_count


@transaction.atomic
def process_document(document: AIDocument) -> AIDocument:
    document.status = AIDocument.Status.PROCESSING
    document.error = ""
    document.save(update_fields=["status", "error", "updated_at"])

    try:
        text, page_count = extract_pdf_text(document)
        chunks = chunk_text(text)
        if not chunks:
            raise RuntimeError("No readable text was found in this PDF.")

        document.chunks.all().delete()
        for index, chunk in enumerate(chunks):
            embedding, model = embed_text(chunk)
            AIKnowledgeChunk.objects.create(
                user=document.user,
                document=document,
                source_type=AIKnowledgeChunk.SourceType.PDF,
                source_id=str(document.id),
                title=document.title,
                text=chunk,
                embedding=embedding,
                embedding_model=model,
                token_count=max(1, len(chunk.split())),
                order=index,
            )

        document.extracted_text = text[:250_000]
        document.pages = page_count
        document.status = AIDocument.Status.READY
        document.processed_at = timezone.now()
        document.save(update_fields=["extracted_text", "pages", "status", "processed_at", "updated_at"])
    except Exception as exc:
        document.status = AIDocument.Status.FAILED
        document.error = str(exc)
        document.save(update_fields=["status", "error", "updated_at"])

    return document


def ensure_course_chunks_for_user(user) -> None:
    from apps.content.models import Note, Topic

    topics = Topic.objects.select_related("chapter").all()[:200]
    for topic in topics:
        source_id = str(topic.id)
        title = f"Topic: {topic.title}"
        text = normalize_text(f"{topic.title}. Chapter: {getattr(topic.chapter, 'title', '')}.")
        if not text:
            continue
        if AIKnowledgeChunk.objects.filter(source_type=AIKnowledgeChunk.SourceType.COURSE_TOPIC, source_id=source_id).exists():
            continue
        embedding, model = embed_text(text)
        AIKnowledgeChunk.objects.create(
            source_type=AIKnowledgeChunk.SourceType.COURSE_TOPIC,
            source_id=source_id,
            title=title,
            text=text,
            embedding=embedding,
            embedding_model=model,
            token_count=max(1, len(text.split())),
        )

    notes = Note.objects.filter(created_by=user)[:200]
    for note in notes:
        source_id = str(note.id)
        if AIKnowledgeChunk.objects.filter(
            user=user,
            source_type=AIKnowledgeChunk.SourceType.COURSE_NOTE,
            source_id=source_id,
        ).exists():
            continue
        text = normalize_text(f"{note.title}. {note.content_richtext}")
        if not text:
            continue
        embedding, model = embed_text(text)
        AIKnowledgeChunk.objects.create(
            user=user,
            source_type=AIKnowledgeChunk.SourceType.COURSE_NOTE,
            source_id=source_id,
            title=f"Note: {note.title}",
            text=text,
            embedding=embedding,
            embedding_model=model,
            token_count=max(1, len(text.split())),
        )


def retrieve_context(*, user, query: str, limit: int | None = None) -> list[RetrievedChunk]:
    ensure_course_chunks_for_user(user)
    query_embedding, _model = embed_text(query)
    limit = limit or int(getattr(settings, "AI_RAG_TOP_K", 5))
    candidates = AIKnowledgeChunk.objects.filter(user__isnull=True) | AIKnowledgeChunk.objects.filter(user=user)

    ranked = [
        RetrievedChunk(chunk=chunk, score=cosine_similarity(query_embedding, chunk.embedding))
        for chunk in candidates.select_related("document")[:1500]
    ]
    ranked.sort(key=lambda item: item.score, reverse=True)
    return [item for item in ranked[:limit] if item.score > 0.05]


def build_citations(chunks: Iterable[RetrievedChunk]) -> list[dict]:
    citations = []
    for item in chunks:
        chunk = item.chunk
        citations.append(
            {
                "chunk_id": chunk.id,
                "title": chunk.title,
                "source_type": chunk.source_type,
                "source_id": chunk.source_id,
                "score": round(item.score, 4),
                "page_start": chunk.page_start,
                "page_end": chunk.page_end,
                "preview": chunk.text[:280],
            }
        )
    return citations


AI_SYSTEM_PROMPT = (
    "You are EduPlatform's learning assistant for students in Nepal. "
    "Explain clearly and encouragingly at a level appropriate for the student's question. "
    "When retrieved context is provided, ground your answer in it and cite the bracketed "
    "source numbers (e.g. [1], [2]) you used. If the context is insufficient or absent, say "
    "briefly what is missing, then give a concise, correct general explanation from your own "
    "knowledge. Prefer short paragraphs and worked examples over long walls of text."
)


def generate_answer(*, question: str, context_chunks: list[RetrievedChunk]) -> tuple[str, str]:
    context = "\n\n".join(
        f"[{index + 1}] {item.chunk.title}\n{item.chunk.text}" for index, item in enumerate(context_chunks)
    )
    api_key = getattr(settings, "ANTHROPIC_API_KEY", "")
    model = getattr(settings, "AI_CHAT_MODEL", "claude-opus-4-8")
    max_tokens = int(getattr(settings, "AI_CHAT_MAX_TOKENS", 2000))

    if api_key:
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=api_key)
            user_content = (
                f"Retrieved context:\n{context or 'No retrieved context available.'}\n\n"
                f"Question: {question}"
            )
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=AI_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_content}],
            )
            answer = "".join(
                block.text for block in response.content if getattr(block, "type", None) == "text"
            ).strip()
            if answer:
                return answer, "rag_claude" if context_chunks else "general_claude"
        except Exception:
            pass

    if context_chunks:
        bullets = "\n".join(f"- {item.chunk.text[:350]}" for item in context_chunks[:3])
        return (
            "I found relevant material in your uploaded/course content. Here is the best grounded answer I can provide locally:\n\n"
            f"{bullets}\n\n"
            f"In short: {question} relates to the points above. Review the cited source previews for the exact context.",
            "rag_local",
        )

    return (
        "I could not find matching uploaded PDF or course context yet. "
        "Upload a PDF or add notes for this topic, then ask again so I can answer from your learning material.",
        "fallback",
    )


@transaction.atomic
def answer_learning_question(*, user, message: str, session_id: int | None = None) -> dict:
    session = None
    if session_id:
        session = AIChatSession.objects.filter(id=session_id, user=user).first()
    if session is None:
        title = message[:80] or "New chat"
        session = AIChatSession.objects.create(user=user, title=title)

    AIChatMessage.objects.create(session=session, role=AIChatMessage.Role.USER, content=message)

    chunks = retrieve_context(user=user, query=message)
    citations = build_citations(chunks)
    answer, source = generate_answer(question=message, context_chunks=chunks)

    assistant_message = AIChatMessage.objects.create(
        session=session,
        role=AIChatMessage.Role.ASSISTANT,
        content=answer,
        citations=citations,
        metadata={"source": source},
    )
    session.updated_at = timezone.now()
    session.save(update_fields=["updated_at"])

    return {
        "session_id": session.id,
        "answer": answer,
        "source": source,
        "citations": citations,
        "message": assistant_message,
    }
