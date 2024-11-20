import React, {useState} from 'react';
import {Box, Text, Spinner, Button, VStack, HStack} from '@chakra-ui/react';
import DocViewer, { DocViewerRenderers } from "react-doc-viewer";
import { useDocuments } from '../../hooks/useDocuments';
import {API_URL} from "../../config/api";
import KnowledgeGraph from "./KnowledgeGraph";
import Editor from '@monaco-editor/react';
import {documentsApi} from "../../api/documents";

import { Document, Page } from 'react-pdf';

import 'pdfjs-dist/build/pdf.worker';


export const FileViewer: React.FC<{ documentId?: number }> = ({ documentId }) => {
  const { documents, isLoading, graphData } = useDocuments();
  const document = documents.find(d => d.id === documentId);
  const [editorContent, setEditorContent] = useState(document?.content || "");
  const [numPages, setNumPages] = useState<number>(10);
  const [pageNumber, setPageNumber] = useState(1);

	const onDocumentLoadSuccess = ({ numPages }) => {
		setNumPages(numPages);
	};

	const goToPrevPage = () =>
		setPageNumber(pageNumber - 1 <= 1 ? 1 : pageNumber - 1);

	const goToNextPage = () =>
		setPageNumber(
			pageNumber + 1 >= numPages ? numPages : pageNumber + 1,
		);

  const handleUpdate = async () => {
    try {
      // @ts-ignore
      await documentsApi.updateDocument(document.id, editorContent);
      alert(JSON.stringify({
        title: "Document updated successfully",
        status: "success",
        duration: 3000,
      }));
    } catch (error: any) {
      if (error.response?.status === 400) {
        alert(JSON.stringify({
          title: "Update failed",
          description: "Please try again",
          status: "error",
          duration: 3000,
        }));
      }
    }
  };

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
        <Text fontSize="lg" mb={4}>Folder: {document.content}</Text>
        {graphData && <KnowledgeGraph data={graphData} />}
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

  const fileType = document.doc_metadata?.mime_type || 'text/plain';

  return (
    <Box h="calc(100vh - 100px)" borderRadius="md" overflow="hidden">
      {fileType === "text/plain"
          ? <Box h="calc(100vh - 100px)" position="relative">
              <Box position="absolute" top={2} right={2} zIndex={10}>
                <Button colorScheme="blue" size="sm" onClick={handleUpdate}>
                  Update
                </Button>
              </Box>
              <Editor
                height="100%"
                defaultLanguage="plaintext"
                defaultValue={document.content}
                onChange={value => setEditorContent(value || '')}
                options={{
                  minimap: { enabled: false },
                  lineNumbers: 'on',
                  wordWrap: 'on',
                  theme: 'vs-light',
                  scrollBeyondLastLine: false,
                  automaticLayout: true,
                  readOnly: false
                }}
              />
            </Box>
          :
          fileType === "application/pdf"
              ? (<div>
                <nav>
                  <HStack gap={50}>
                    <Button onClick={goToPrevPage}>Prev</Button>
                    <Button onClick={goToNextPage}>Next</Button>
                  </HStack>

                  <p>
                    Page {pageNumber} of {numPages}
                  </p>
                </nav>
                <Document
                    file={downloadUri}
                    onLoadSuccess={onDocumentLoadSuccess}
                >
                  <Page pageNumber={pageNumber}/>
                </Document>
              </div>)
              :
              <DocViewer
                  documents={docs}
                  pluginRenderers={DocViewerRenderers}
                  style={{height: '100%'}}
              />
      }
    </Box>
  );
};