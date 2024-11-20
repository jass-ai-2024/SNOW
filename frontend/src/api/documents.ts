import axios from 'axios';
import { API_URL } from '../config/api';
import { Document } from '../types/documents';

export const documentsApi = {
  getAll: async (parentId?: number | string) => {
    const url = parentId
      ? `${API_URL}/documents/${parentId}`
      : `${API_URL}/documents/`;
    const response = await axios.get<Document[]>(url);
    return response.data;
  },

  upload: async (file: File, parentId?: number) => {
    const formData = new FormData();
    formData.append('file', file);
    if (parentId) {
      formData.append('parent_id', parentId.toString());
    }

    const response = await axios.post(
      `${API_URL}/documents/`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    );
    return response.data;
  },

  updateDocument: async (documentId: number, newValue: string) => {
      const response = await fetch(
        `${API_URL}/arch/update/`, {
            method: "POST",
            body: JSON.stringify({id: documentId, content: newValue}),
            headers: {
                'Content-Type': 'application/json'  // Add this header
            },
          }
      );

      return await response.json();
  },

  download: async (documentId: number) => {
    const response = await axios.get(
      `${API_URL}/documents/download/${documentId}`,
      { responseType: 'blob' }
    );
    return response.data;
  },

  moveDocument: async (documentId: number, newParentId: number | null) => {
    const response = await axios.post(
      `${API_URL}/documents/${documentId}/move/${newParentId || 'root'}`
    );
    return response.data;
  },

  getContent: async (documentId: number) => {
    const response = await axios.get(`${API_URL}/documents/content/${documentId}`);
    return response.data.content;
  },

  createFolder: async (name: string, parentId?: number) => {
    const response = await axios.post(`${API_URL}/documents/create_folder/`, {
      name,
      parent_id: parentId || null // явно указываем null если parentId не определен
    });
    return response.data;
  },

  deleteDocument: async (documentId: number) => {
    const response = await axios.delete(`${API_URL}/documents/${documentId}`);
    return response.data;
  },

  getGraph: async () => {
    const response = await axios.get(`${API_URL}/graph/`);
    return response.data;
  }
};
