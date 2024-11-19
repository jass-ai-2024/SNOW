export interface Document {
  id: number;
  content: string;
  parent_id: number | undefined;
  doc_metadata: {
    type: 'file' | 'folder';
    mime_type?: string;
    original_filename?: string;
  };
  download_url?: string;
}

export interface FileUploadResponse {
  id: number;
  download_url: string;
}

export interface SearchResult {
  answer: string;
  documents: {
    id: number;
    parent: number | null;
    subcontent: string;
  }[];
}

// API request types
export interface UploadDocumentRequest {
  file: File;
  parent_id?: number;
}

export interface SearchRequest {
  query: string;
}