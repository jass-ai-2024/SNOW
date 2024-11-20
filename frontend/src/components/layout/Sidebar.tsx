import React, { useState } from 'react';
import {VStack, HStack, Button} from '@chakra-ui/react';
import { DragDropContext, Droppable } from 'react-beautiful-dnd';
import { FileTree } from '../documents/FileTree';
import { useQueryClient } from '@tanstack/react-query';
import {documentsApi} from "../../api/documents";
import {CreateFolder} from "../documents/CreateFolder";
import {UploadArea} from "../documents/AddFileButton";
import {UploadModal} from "../documents/UploadModal";
import {Upload} from "lucide-react";
import {AddFileButton} from "../documents/FileUpload";

export const Sidebar = ({selectedId, setSelectedId}: {selectedId: any, setSelectedId: any}) => {
  const queryClient = useQueryClient();
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

  const handleDragEnd = async (result: any) => {
    if (!result.destination) return;

    try {
      const newParentId = result.destination.droppableId === 'root'
        ? null
        : parseInt(result.destination.droppableId);

      await documentsApi.moveDocument(
        parseInt(result.draggableId),
        newParentId
      );

      await queryClient.invalidateQueries({
        queryKey: ['documents']
      });
    } catch (error) {
      console.error('Failed to move document:', error);
    }
  };

  return (
      <div className="flex flex-col h-full bg-white border-r">
    <DragDropContext onDragEnd={handleDragEnd}>
      <VStack gap={4} align="stretch">
        <HStack justify="space-between" align="center">
          <p>Documents</p>
          <CreateFolder/>
        </HStack>
        <div className="p-4 border-b">
          <AddFileButton/>
        </div>
        <FileTree onSelect={setSelectedId} selectedId={selectedId}/>
      </VStack>
    </DragDropContext>

        <UploadModal
            isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
      />
    </div>
  );
};