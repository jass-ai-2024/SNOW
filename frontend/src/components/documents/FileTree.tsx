import React, { useState } from 'react';
import {
  Box,
  HStack,
  Text,
  VStack
} from '@chakra-ui/react';
import {Folder, FileText, ChevronRight, ChevronDown, Loader2, Trash2, AlertCircle} from 'lucide-react';
import { Droppable, Draggable } from 'react-beautiful-dnd';
import { Document } from '../../types/documents'
import { useDropzone } from 'react-dropzone';
import {useDocuments} from "../../hooks/useDocuments";
import {FileContextMenu} from "./FileContextMenu";
import {documentsApi} from "../../api/documents";
import {useQueryClient} from "@tanstack/react-query";
import {DeleteConfirmDialog} from "./DeleteConfirmDialog";

interface FileTreeItemProps {
  document: Document;
  onSelect: (id: number) => void;
  selectedId: number | undefined;
  index: number;
}

const FileTreeItem: React.FC<FileTreeItemProps> = ({ document, onSelect, selectedId, index }) => {
  const [isHovered, setIsHovered] = useState(false);
  const queryClient = useQueryClient();
  const [isOpen, setIsOpen] = React.useState(false);
  const { documents, isLoading, uploadDocument } = useDocuments(isOpen ? document.id : undefined);
  const isFolder = document.doc_metadata.type === 'folder';

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: async (files) => {
      if (isFolder) {
        for (const file of files) {
          await uploadDocument({ file, parentId: document.id });
        }
      }
    },
    noClick: true,
  });

  const handleDelete = async () => {
    try {
      await documentsApi.deleteDocument(document.id);
      await queryClient.invalidateQueries({ queryKey: ['documents'] });
    } catch (error: any) {
      if (error.response?.status === 400) {
        alert('Cannot delete folder with documents inside');
      }
    }
  };

  return (
      <>
    <Draggable draggableId={document.id.toString()} index={index}>
      {(provided) => (
          <FileContextMenu parentId={document.id}>
            <Box
              ref={provided.innerRef}
              {...provided.draggableProps}
              {...provided.dragHandleProps}
              onMouseEnter={() => setIsHovered(true)}
              onMouseLeave={() => setIsHovered(false)}
              position="relative"
            >
              <Box
                {...(isFolder ? getRootProps() : {})}
                bg={isDragActive ? 'blue.50' : 'transparent'}
              >
                {isFolder && <input {...getInputProps()} />}
                <HStack
                  p={2}
                  gap={2}
                  cursor="pointer"
                  borderRadius="md"
                  bg={selectedId === document.id ? 'blue.50' : 'transparent'}
                  _hover={{ bg: 'gray.50' }}
                  onClick={() => {
                    console.log(document.id)
                    onSelect(document.id);
                    if (isFolder) setIsOpen(!isOpen);
                  }}
                >
                  {isFolder && (
                    isOpen ? (
                      <ChevronDown size={18} className="text-gray-500" />
                    ) : (
                      <ChevronRight size={18} className="text-gray-500" />
                    )
                  )}
                  {isFolder ? (
                    <Folder size={18} className="text-blue-500" />
                  ) : (
                    <FileText size={18} className="text-gray-500" />
                  )}
                  <Text>{document.content}</Text>

                  {isHovered && (
                    <button
                      className="absolute right-2 p-1 rounded hover:bg-gray-200 transition-colors"
                      onClick={handleDelete}
                    >
                      <Trash2 size={16} className="text-red-500" style={{cursor: "pointer", opacity: 0.8}} />
                    </button>
                  )}

        </HStack>

                {isFolder && isOpen && (
                  <Droppable droppableId={document.id.toString()}>
                    {(provided) => (
                      <Box
                        pl={4}
                        ref={provided.innerRef}
                        {...provided.droppableProps}
                      >
                        {isLoading ? (
                          <Loader2 className="animate-spin" />
                        ) : (
                          documents?.map((doc, index) => (
                            <FileTreeItem
                              key={doc.id}
                              document={doc}
                              onSelect={onSelect}
                              selectedId={selectedId}
                              index={index}
                            />
                          ))
                        )}
                        {provided.placeholder}
                      </Box>
                    )}
                  </Droppable>
                )}
              </Box>
            </Box>
        </FileContextMenu>
      )}
    </Draggable>
    </>
  );
};

interface FileTreeProps {
  onSelect: (id: number) => void;
  selectedId: number | undefined;
}


export const FileTree: React.FC<FileTreeProps> = ({ onSelect, selectedId }) => {
  const { documents: allDocuments, isLoading } = useDocuments('root');
  const documents = allDocuments.filter((doc: Document) => doc.parent_id === null)
  if (isLoading) return <Loader2 className="animate-spin" />;

  return (
    <Droppable droppableId="root">
      {(provided) => (
        <VStack
          align="stretch"
          gap={0}
          ref={provided.innerRef}
          {...provided.droppableProps}
        >
          {documents?.map((doc, index) => (
            <FileTreeItem
              key={doc.id}
              document={doc}
              onSelect={onSelect}
              selectedId={selectedId}
              index={index}
            />
          ))}
          {provided.placeholder}
        </VStack>
      )}
    </Droppable>
  );
};