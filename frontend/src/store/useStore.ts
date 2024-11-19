import create from 'zustand';
import { Document } from '../types/documents';

interface AppState {
  selectedDocument: Document | null;
  documents: Document[];
  setSelectedDocument: (doc: Document | null) => void;
  setDocuments: (docs: Document[]) => void;
}

// @ts-ignore
export const useStore = create<AppState>((set: any) => ({
  selectedDocument: null,
  documents: [],
  setSelectedDocument: (doc: any) => set({ selectedDocument: doc }),
  setDocuments: (docs: any) => set({ documents: docs }),
}));
