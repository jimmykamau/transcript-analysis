from datetime import UTC, datetime

from bson import ObjectId

from app.transcripts.models import TranscriptAnalysis, TranscriptDocument
from app.transcripts.schemas import TranscriptSummary

# Fields returned for list/search endpoints — excludes the full transcript text to keep responses light.
_SUMMARY_PROJECTION = {
    "_id": 1,
    "qa_score": 1,
    "sentiment": 1,
    "summary": 1,
    "created_at": 1,
    "topics": 1,
}


def _normalize(doc: dict) -> dict:
    # MongoDB uses "_id" (ObjectId); rename and stringify it to match our schema's "id" field.
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
    db, skip: int = 0, limit: int = 20, topic: str | None = None
) -> list[TranscriptSummary]:
    query = {"topics": topic} if topic is not None else {}
    cursor = (
        db["transcripts"]
        .find(query, _SUMMARY_PROJECTION)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    return [TranscriptSummary(**_normalize(doc)) async for doc in cursor]


async def list_topics(db) -> list[str]:
    results = await db["transcripts"].distinct("topics")
    return [t for t in results if t is not None]


async def search_by_topics(
    db, topics: list[str], skip: int = 0, limit: int = 20
) -> list[TranscriptSummary]:
    cursor = (
        db["transcripts"]
        .find({"topics": {"$in": topics}}, _SUMMARY_PROJECTION)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    return [TranscriptSummary(**_normalize(doc)) async for doc in cursor]
