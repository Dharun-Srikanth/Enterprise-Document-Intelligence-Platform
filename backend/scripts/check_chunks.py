import asyncio
from app.db.database import async_session
from sqlalchemy import text

async def check():
    async with async_session() as db:
        r = await db.execute(text(
            "SELECT chunk_text FROM document_chunks dc "
            "JOIN documents d ON dc.document_id = d.id "
            "WHERE d.filename='meeting_notes_sprint8.txt' LIMIT 5"
        ))
        for i, row in enumerate(r.fetchall()):
            print(f"--- Chunk {i} ---")
            print(row[0][:400])
            print()

asyncio.run(check())
