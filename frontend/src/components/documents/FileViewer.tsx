import React from 'react';
import { Box, Text, Spinner } from '@chakra-ui/react';
import DocViewer, { DocViewerRenderers } from "react-doc-viewer";
import { useDocuments } from '../../hooks/useDocuments';
import {API_URL} from "../../config/api";

export const FileViewer: React.FC<{ documentId?: number }> = ({ documentId }) => {
  const { documents, isLoading } = useDocuments();
  const document = documents.find(d => d.id === documentId);

  if (isLoading) {
    return (
      <Box p={4} display="flex" justifyContent="center">
        <Spinner />
      </Box>
    );
  }

  if (!document) {
    return (
      <Box p={4}>
        <Text>Select a document to view</Text>
      </Box>
    );
  }

  if (document.doc_metadata.type === 'folder') {
    return (
      <Box p={4}>
        <Text fontSize="lg" fontWeight="bold">
          Folder: {document.content}
        </Text>
      </Box>
    );
  }

  if (!document.download_url) {
    return (
      <Box p={4}>
        <Text color="red.500">Download URL not available</Text>
      </Box>
    );
  }

  const downloadUri = `${API_URL}/documents/download/${document.id}`;
  console.log(downloadUri, document.content)
  const docs = [{
    uri: downloadUri,
    fileName: document.content,
    fileType: document.doc_metadata?.mime_type || 'text/plain'
  }];

  return (
    <Box h="calc(100vh - 100px)" borderRadius="md" overflow="hidden">
      <DocViewer
        documents={docs}
        pluginRenderers={DocViewerRenderers}
        style={{ height: '100%' }}
      />
    </Box>
  );
};