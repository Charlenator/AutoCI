"""CV smart-chunking helper — Sprint B5.

Transforms a normalized CVExtractorAgent record into 5–8 corpus_chunks rows
with chunk_text ready for embedding.

Chunk kinds produced:
  - identity  (name + email + phone + location)
  - skills    (comma-separated)
  - summary   (only if record has a summary)
  - experience (one chunk per job)
  - education (all rows combined)
"""

from __future__ import annotations

_MAX_CHUNK_CHARS = 2000


def chunk_cv(record: dict, candidate_id: str) -> list[dict]:
    """Build 5–8 corpus_chunks rows from a CVExtractorAgent record.

    Args:
        record: The dict returned by CVExtractorAgent.extract().
        candidate_id: UUID of the candidates row to link chunks to.

    Returns:
        List of dicts ready for corpus_chunks upsert:
          {
            "corpus_name": "cvs",
            "chunk_text": str,
            "metadata": {
              "candidate_id": candidate_id,
              "chunk_kind": "identity"|"skills"|"summary"|"experience"|"education",
              "section_label": str,
              "role_target": str|None,
              "confidential": True,
            },
          }
    """
    chunks: list[dict] = []

    # ── Identity chunk ──────────────────────────────────────────────────
    parts: list[str] = []
    name = record.get("name") or ""
    email = record.get("email") or ""
    phone = record.get("phone") or ""

    if name:
        parts.append(f"Name: {name}")
    if email:
        parts.append(f"Email: {email}")
    if phone:
        parts.append(f"Phone: {phone}")

    # Try to extract a rough location from raw_text (between "Location: " and next newline)
    raw_text = record.get("raw_text") or ""
    for line in raw_text.split("\n"):
        stripped = line.strip()
        lower = stripped.lower()
        if lower.startswith("location") or lower.startswith("address") or lower.startswith("based in"):
            # Grab after the colon
            colon = stripped.find(":")
            if colon != -1 and colon < len(stripped) - 1:
                loc = stripped[colon + 1:].strip()
                if loc:
                    parts.append(f"Location: {loc}")
                    break
            else:
                parts.append(f"Location: {stripped}")
                break

    identity_text = "; ".join(parts)
    if identity_text:
        chunks.append(_make_chunk(
            chunk_kind="identity",
            section_label="Identity",
            chunk_text=identity_text,
            candidate_id=candidate_id,
        ))

    # ── Skills chunk ────────────────────────────────────────────────────
    skills = record.get("skills") or []
    if skills:
        skills_text = ", ".join(skills)
        chunks.append(_make_chunk(
            chunk_kind="skills",
            section_label="Skills",
            chunk_text=skills_text,
            candidate_id=candidate_id,
        ))

    # ── Summary chunk ───────────────────────────────────────────────────
    summary = (record.get("summary") or "").strip()
    if summary:
        chunks.append(_make_chunk(
            chunk_kind="summary",
            section_label="Profile",
            chunk_text=summary,
            candidate_id=candidate_id,
        ))

    # ── Experience chunks (one per job) ─────────────────────────────────
    experience = record.get("experience") or []
    for exp in experience:
        if not isinstance(exp, dict):
            continue
        role = (exp.get("role") or "").strip()
        company = (exp.get("company") or "").strip()
        start = (exp.get("start_date") or "").strip()
        end = (exp.get("end_date") or "").strip()
        desc = (exp.get("description") or "").strip()

        date_range = f"{start}–{end}" if start or end else ""
        parts_exp = []
        if role and company:
            parts_exp.append(f"{role} at {company}")
        elif role:
            parts_exp.append(role)
        elif company:
            parts_exp.append(f"Worked at {company}")
        if date_range:
            parts_exp.append(f"({date_range})")
        if desc:
            parts_exp.append(f": {desc}" if parts_exp else desc)

        exp_text = " ".join(parts_exp)
        if exp_text:
            section_label = f"Experience: {role}" if role else "Experience"
            chunks.append(_make_chunk(
                chunk_kind="experience",
                section_label=section_label,
                chunk_text=exp_text,
                candidate_id=candidate_id,
                role_target=role or None,
            ))

    # ── Education chunk (all rows combined) ─────────────────────────────
    education = record.get("education") or []
    if education:
        edu_lines: list[str] = []
        for edu in education:
            if not isinstance(edu, dict):
                continue
            school = (edu.get("school") or "").strip()
            degree = (edu.get("degree") or "").strip()
            year = (edu.get("year") or "").strip()
            parts_edu = [p for p in [school, degree, year] if p]
            if parts_edu:
                edu_lines.append(", ".join(parts_edu))
        if edu_lines:
            edu_text = "\n".join(edu_lines)
            chunks.append(_make_chunk(
                chunk_kind="education",
                section_label="Education",
                chunk_text=edu_text,
                candidate_id=candidate_id,
            ))

    # Cap each chunk at _MAX_CHUNK_CHARS
    for c in chunks:
        if len(c["chunk_text"]) > _MAX_CHUNK_CHARS:
            c["chunk_text"] = c["chunk_text"][:_MAX_CHUNK_CHARS]

    return chunks


def _make_chunk(
    *,
    chunk_kind: str,
    section_label: str,
    chunk_text: str,
    candidate_id: str,
    role_target: str | None = None,
) -> dict:
    return {
        "corpus_name": "cvs",
        "chunk_text": chunk_text,
        "metadata": {
            "candidate_id": candidate_id,
            "chunk_kind": chunk_kind,
            "section_label": section_label,
            "role_target": role_target,
            "confidential": True,
        },
    }
