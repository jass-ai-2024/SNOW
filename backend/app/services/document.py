import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple

from fastapi import UploadFile

from app.core.config import settings
from app.models.document import Document
from app.schemas.document import DocumentCreate, FolderCreate
from app.repositories.document import DocumentRepository


class DocumentService:
    def __init__(self, repository: DocumentRepository):
        self.repository = repository

    def _generate_safe_filename(self, original_filename: str) -> str:
        """Generate unique filename with timestamp and UUID"""
        unique_id = str(uuid.uuid4())[:8]
        safe_name = f"{unique_id}_{original_filename}"
        return safe_name

    async def save_file(self, file: UploadFile) -> Path:
        """Safely save uploaded file with unique name"""
        safe_filename = self._generate_safe_filename(file.filename)
        file_path = settings.UPLOAD_DIR / safe_filename

        try:
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            if file_path.exists():
                file_path.unlink()
            raise Exception(f"Failed to save file: {str(e)}")

        return file_path
    async def get_place(self, document: DocumentCreate) -> Dict[str, any]:
        """Determine the best place for a document based on content"""
        # Here you would implement your logic to analyze content and suggest placement
        # For now, returning mock data
        return {
            "folder_parent_id": 1,
            "folder_name": "suggested_folder"
        }

    async def create_folder(self, folder: FolderCreate) -> Dict[str, int]:
        doc = Document(
            content="",
            doc_metadata={"type": "folder", "name": folder.name},
            parent_id=folder.parent_id
        )
        created = await self.repository.create(doc)
        return {"id": created.id}
    
    async def create_document(self, file: UploadFile, parent_id: Optional[int] = None) -> Document:
        file_path = await self.save_file(file)

        doc = Document(
            content=file.filename,
            doc_metadata={"type": "file", "mime_type": file.content_type},
            parent_id=parent_id,
            download_url=str(file_path.name),
        )
        doc = await self.repository.create(doc)

        return doc

    async def get_documents(self, parent_id: Optional[int] = None) -> List[Document]:
        return await self.repository.get_by_parent(parent_id)

    async def get_file(self, document_id: int) -> Optional[Path]:
        """Get file path for document"""
        doc = await self.repository.get_by_id(document_id)
        return settings.UPLOAD_DIR / doc.download_url
