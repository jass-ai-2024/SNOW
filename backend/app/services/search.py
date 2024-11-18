from typing import Dict, List
from app.repositories.document import DocumentRepository


class SearchService:
    def __init__(self, repository: DocumentRepository):
        self.repository = repository
    
    async def search_documents(self, query: str) -> Dict:
        # Here you would implement your semantic search logic
        # This is a basic implementation
        documents = await self.repository.search(query)
        
        return {
            "answer": f"Found {len(documents)} documents matching your query",
            "documents": [
                {
                    "id": doc.id,
                    "parent": doc.parent_id,
                    "subcontent": doc.content[:200]  # First 200 chars as preview
                }
                for doc in documents
            ]
        }


async def search(self, query: str):
    # Basic search implementation
    # In real application, you might want to use full-text search or vector similarity
    query = f"%{query}%"
    stmt = select(Document).where(Document.content.ilike(query))
    result = await self.session.execute(stmt)
    return result.scalars().all()
