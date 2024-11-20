import json

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from typing import List, Optional, Union

import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import FileResponse

from app.schemas.document import (
    DocumentCreate, 
    DocumentResponse, 
    FolderCreate, 
    FolderResponse, 
    PlaceResponse,
    ArchData,
)
from app.services.document import DocumentService
from app.services.rag import DocumentProcessor
from app.services.search import SearchService
from app.core.database import get_session
from app.repositories.document import DocumentRepository

router = APIRouter()


async def get_document_service(session: AsyncSession = Depends(get_session)) -> DocumentService:
    return DocumentService(DocumentRepository(session), DocumentProcessor())


async def get_search_service(session: AsyncSession = Depends(get_session)) -> SearchService:
    return SearchService(DocumentRepository(session))


@router.post("/documents/get_place/", response_model=PlaceResponse)
async def get_document_place(
    document: DocumentCreate,
    service: DocumentService = Depends(get_document_service)
):
    return await service.get_place(document)


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    service: DocumentService = Depends(get_document_service)
):
    await service.delete_document(document_id)
    return {"status": "success"}

@router.post("/documents/create_folder/", response_model=FolderResponse)
async def create_folder(
    folder: FolderCreate,
    service: DocumentService = Depends(get_document_service)
):
    return await service.create_folder(folder)


@router.post("/documents/", response_model=DocumentResponse)
async def create_document(
    file: UploadFile,
    parent_id: Optional[int] = None,
    metadata: Optional[str] = None,
    service: DocumentService = Depends(get_document_service)
):
    return await service.create_document(file, parent_id, metadata)


@router.get("/documents/", response_model=List[DocumentResponse])
async def get_documents(
    service: DocumentService = Depends(get_document_service)
):
    return await service.get_documents()


@router.get("/documents/{parent_id}", response_model=List[DocumentResponse])
async def get_documents(
    parent_id: Union[int, str] = 'root',
    service: DocumentService = Depends(get_document_service)
):
    parent_id = None if parent_id == 'root' else int(parent_id)
    return await service.get_documents(parent_id)


@router.get("/search/")
async def search_documents(
    query: str,
    service: SearchService = Depends(get_search_service)
):
    return await service.search_documents(query)


@router.post("/documents/{document_id}/move/{new_parent_id}")
async def move_document(
   document_id: int,
   new_parent_id: Union[int, str],
   service: DocumentService = Depends(get_document_service)
):
    new_parent_id = None if new_parent_id == 'root' else int(new_parent_id)
    return await service.move_document(document_id, new_parent_id)


@router.get("/documents/download/{document_id}")
async def download_document(
    document_id: int,
    service: DocumentService = Depends(get_document_service)
):
    file_path = await service.get_file(document_id)
    print(document_id, file_path)
    if not file_path or not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        filename=file_path.name,
        media_type="application/octet-stream"
    )


@router.get("/graph/")
async def get_graph(service: DocumentService = Depends(get_document_service)):
    with open("storage/document_state.json", "r") as f:
        raw_documents = json.loads(f.read())

        return raw_documents


@router.post("/arch/update/")
async def arch_update(
    arch_data: ArchData,
    service: DocumentService = Depends(get_document_service)
):
    document = await service.get_document_by_id(arch_data.id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    document.content = arch_data.content
    await service.repository.update(document)

    if "callback_url" not in document.doc_metadata and "document_id" not in document.doc_metadata:
        raise HTTPException(status_code=404, detail="Document for arch not found")

    async with aiohttp.ClientSession() as session:
        await session.post(
            document.doc_metadata["callback_url"],
            json={
                "content": arch_data.content,
                "id": document.doc_metadata["document_id"]
            }
        )

    return {"status": "success"}
