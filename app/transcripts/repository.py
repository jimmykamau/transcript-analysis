from datetime import UTC, datetime

from bson import ObjectId

from app.transcripts.models import TranscriptDocument
from app.transcripts.schemas import TranscriptAnalysis, TranscriptSummary


def _normalize(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    return doc


async def save_transcript(
    db, transcript: str, analysis: TranscriptAnalysis
) -> TranscriptDocument:
    now = datetime.now(UTC)
    analysis_data = analysis.model_dump()
    doc = {**analysis_data, "transcript": transcript, "created_at": now}
    result = await db["transcripts"].insert_one(doc)
    return TranscriptDocument(
        id=str(result.inserted_id),
        transcript=transcript,
        created_at=now,
        **analysis_data,
    )


async def get_transcript_by_id(db, id: str) -> TranscriptDocument | None:
    doc = await db["transcripts"].find_one({"_id": ObjectId(id)})
    if doc is None:
        return None
    return TranscriptDocument(**_normalize(doc))


async def list_transcripts(
    db, skip: int = 0, limit: int = 20
) -> list[TranscriptSummary]:
    cursor = (
        db["transcripts"]
        .find({}, {"_id": 1, "qa_score": 1, "sentiment": 1, "created_at": 1})
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    return [TranscriptSummary(**_normalize(doc)) async for doc in cursor]
