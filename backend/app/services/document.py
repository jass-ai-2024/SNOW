import os
import shutil
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple

from fastapi import UploadFile, HTTPException

from app.core.config import settings
from app.models.document import Document
from app.schemas.document import DocumentCreate, FolderCreate
from app.repositories.document import DocumentRepository
from app.services.rag import DocumentProcessor


class DocumentService:
    def __init__(self, repository: DocumentRepository, processor: DocumentProcessor):
        self.repository = repository
        self.processor = processor

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
            content=folder.name,
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

        self.processor.add_document("data/" + doc.download_url)

        return doc

    async def get_documents(self, parent_id: Optional[int] = None) -> List[Document]:
        return await self.repository.get_by_parent(parent_id)

    async def get_file(self, document_id: int) -> Optional[Path]:
        """Get file path for document"""
        doc = await self.repository.get_by_id(document_id)
        return settings.UPLOAD_DIR / doc.download_url

    async def move_document(self, document_id: int, new_parent_id: int) -> Document:
        """Move document to new parent folder"""
        doc = await self.repository.get_by_id(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        if new_parent_id:
            new_parent = await self.repository.get_by_id(new_parent_id)
            if not new_parent or new_parent.doc_metadata.get("type") != "folder":
                raise HTTPException(status_code=400, detail="Invalid destination folder")

        doc.parent_id = new_parent_id
        return await self.repository.update(doc)

    async def delete_document(self, document_id: int) -> None:
        doc = await self.repository.get_by_id(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        if doc.doc_metadata.get("type") == "folder":
            # Проверяем, есть ли документы в папке
            children = await self.repository.get_by_parent(doc.id)
            if children:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot delete folder with documents"
                )

        # Если это файл, удаляем физический файл
        if doc.doc_metadata.get("type") == "file" and doc.download_url:
            try:
                file_path = settings.UPLOAD_DIR / doc.download_url
                file_path.unlink(missing_ok=True)
            except Exception as e:
                print(f"Error deleting file: {e}")

        await self.repository.delete(doc.id)
