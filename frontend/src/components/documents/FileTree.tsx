import React, { useState } from 'react';
import {
  Box,
  HStack,
  Text,
  VStack,
  useDisclosure,
  Popover,
  IconButton,
  Button,
} from '@chakra-ui/react';
import {Folder, FileText, ChevronRight, ChevronDown, Loader2, Trash2, AlertCircle} from 'lucide-react';
import { Droppable, Draggable } from 'react-beautiful-dnd';
import { Document } from '../../types/documents'
import { useDropzone } from 'react-dropzone';
import {useDocuments} from "../../hooks/useDocuments";
import {FileContextMenu} from "./FileContextMenu";
import {documentsApi} from "../../api/documents";
import {useQueryClient} from "@tanstack/react-query";

interface FileTreeItemProps {
  document: Document;
  onSelect: (id: number) => void;
  selectedId: number | undefined;
  index: number;
}

const FileTreeItem: React.FC<FileTreeItemProps> = ({ document, onSelect, selectedId, index }) => {
  const [isHovered, setIsHovered] = useState(false);
  const { open, onOpen, onClose } = useDisclosure();
  const cancelRef = React.useRef(null);
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
      onClose();
    } catch (error: any) {
      console.error('Failed to delete:', error);
      // Если папка не пуста
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
                    <IconButton
                      aria-label="Delete document"
                      size="xs"
                      variant="ghost"
                      colorScheme="red"
                      onClick={(e) => {
                        e.stopPropagation();
                        onOpen();
                      }}
                      position="absolute"
                      right={2}
                      opacity={0.7}
                      _hover={{ opacity: 1 }}
                    >
                      <Trash2 size={16} />
                    </IconButton>
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
  const { documents, isLoading } = useDocuments();

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