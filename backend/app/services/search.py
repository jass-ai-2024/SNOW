from typing import Dict, List
from app.repositories.document import DocumentRepository
from app.services.rag import DocumentProcessor
from app.models.document import Document


class SearchService:
    def __init__(self, document_processor: DocumentProcessor):
        self.processor = document_processor

    async def search_documents(self, query: str) -> Dict:
        # Here you would implement your semantic search logic
        # This is a basic implementation
        res = self.processor.query(query)

        print(res["sources"][0])
        return {
            "answer": res["response"],
            "documents": [
                {
                    "id": doc["text"],
                    "subcontent": doc["metadata"]["summary"]
                }
                for doc in res["sources"]
            ]
        }
