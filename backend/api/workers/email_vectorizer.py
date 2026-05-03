"""Email vectorizer helper — Sprint B5.

Splits a non-CV inbound email into 1–3 corpus_chunks rows ready for embedding.
Used when the classifier returns is_cv=False but the email still has useful
content to retain for future retrieval.
"""

from __future__ import annotations

_MAX_CHUNK_CHARS = 2000
_MAX_BODY_CHUNKS = 2  # keeps total chunks (subject + body) at most 3


def vectorize_email(subject: str, body: str, inbound_id: str) -> list[dict]:
    """Split a non-CV inbound email into 1–3 corpus_chunks rows.

    Args:
        subject: Email subject line.
        body: Email body text.
        inbound_id: UUID of the inbound_emails row.

    Returns:
        list of dicts ready for corpus_chunks upsert:
          {
            "corpus_name": "inbound_emails",
            "chunk_text": str,
            "metadata": {
              "inbound_id": inbound_id,
              "chunk_kind": "subject" | "body",
              "confidential": True,
            },
          }
        Returns [] if both subject and body are empty.
    """
    chunks: list[dict] = []

    # ── Subject chunk ───────────────────────────────────────────────────
    subject_clean = (subject or "").strip()
    if subject_clean:
        chunks.append({
            "corpus_name": "inbound_emails",
            "chunk_text": subject_clean,
            "metadata": {
                "inbound_id": inbound_id,
                "chunk_kind": "subject",
                "confidential": True,
            },
        })

    # ── Body chunks ─────────────────────────────────────────────────────
    body_clean = (body or "").strip()
    if not body_clean:
        return chunks

    # Split into paragraphs (double-newline separated)
    paragraphs = [p.strip() for p in body_clean.split("\n\n") if p.strip()]

    if not paragraphs:
        return chunks

    # Merge paragraphs into at most _MAX_BODY_CHUNKS groups, each <= 2000 chars
    groups: list[str] = []
    current = ""

    for para in paragraphs:
        # If adding this para would exceed max chars, start a new group
        if current and len(current) + 1 + len(para) > _MAX_CHUNK_CHARS:
            groups.append(current)
            current = para
        elif current:
            current += "\n\n" + para
        else:
            current = para

    if current:
        groups.append(current)

    # If we have more groups than _MAX_BODY_CHUNKS, merge the extras into the
    # last allowed group (simple concatenation with truncation).
    if len(groups) > _MAX_BODY_CHUNKS:
        extra = groups[_MAX_BODY_CHUNKS:]
        base = groups[:_MAX_BODY_CHUNKS]
        # Merge all extras into the final base group
        for e in extra:
            if len(base[-1]) + 2 + len(e) <= _MAX_CHUNK_CHARS:
                base[-1] += "\n\n" + e
            else:
                # Truncate the last base group if needed
                space_left = _MAX_CHUNK_CHARS - len(base[-1]) - 2
                if space_left > 0:
                    base[-1] += "\n\n" + e[:space_left]
                break
        groups = base

    for g in groups:
        chunks.append({
            "corpus_name": "inbound_emails",
            "chunk_text": g,
            "metadata": {
                "inbound_id": inbound_id,
                "chunk_kind": "body",
                "confidential": True,
            },
        })

    return chunks
