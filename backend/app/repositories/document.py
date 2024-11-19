from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.models.document import Document


class DocumentRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, document: Document) -> Document:
        self.session.add(document)
        await self.session.commit()
        await self.session.refresh(document)
        return document
    
    async def get_by_parent(self, parent_id: Optional[int]) -> List[Document]:
        query = select(Document)

        if parent_id is not None:
            query = query.where(Document.parent_id == parent_id)

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_by_id(self, document_id: int) -> Optional[Document]:
        query = select(Document).where(Document.id == document_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update(self, document: Document) -> Document:
        await self.session.commit()
        await self.session.refresh(document)
        return document

    async def search(self, query: str) -> list[Document]:
        sql_query = select(Document).limit(3)
        result = await self.session.execute(sql_query)
        return result.scalars().all()

    async def delete(self, document_id: int) -> None:
        """Delete document by id"""
        query = delete(Document).where(Document.id == document_id)
        await self.session.execute(query)
        await self.session.commit()
