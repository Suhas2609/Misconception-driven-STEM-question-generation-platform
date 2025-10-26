from app.database import chroma
from app.services import retrieval_service

COL = "factual_content"

print("Resetting collection...", COL)
chroma.reset_collection(COL)

chunks = [
    {
        "id": "chunk1",
        "text": "Newton's First Law states that an object remains at rest or in uniform motion unless acted upon by a net external force.",
        "metadata": {"source": "physics"},
    },
    {
        "id": "chunk2",
        "text": "Newton's Second Law relates force, mass, and acceleration with F = ma.",
        "metadata": {"source": "physics"},
    },
    {
        "id": "chunk3",
        "text": "Newton's Third Law asserts that every action has an equal and opposite reaction.",
        "metadata": {"source": "physics"},
    },
]

print("Adding chunks...")
retrieval_service.add_to_chroma(chunks, collection_name=COL)

query = "Newton's Laws"
print(f"Querying: {query}")
res = retrieval_service.retrieve_from_chroma(query, collection_name=COL, limit=3)

print("RESULT IDS:", res.get("ids"))
print("RESULT DOCS:", res.get("documents"))
