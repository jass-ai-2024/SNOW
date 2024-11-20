from pydantic import BaseModel
from typing import Optional, Dict, Any


class DocumentBase(BaseModel):
    content: str
    doc_metadata: Optional[Dict[str, Any]] = None
    parent_id: Optional[int] = None


class DocumentCreate(DocumentBase):
    pass


class ArchData(BaseModel):
    id: int
    content: str


class DocumentResponse(DocumentBase):
    id: int
    download_url: Optional[str] = None

    class Config:
        from_attributes = True


class FolderCreate(BaseModel):
    name: str
    parent_id: Optional[int] = None


class FolderResponse(BaseModel):
    id: int


class PlaceResponse(BaseModel):
    folder_parent_id: int
    folder_name: str
