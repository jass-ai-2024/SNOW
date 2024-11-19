import React, { useState } from 'react';
import * as ContextMenu from '@radix-ui/react-context-menu';
import { Button, Input, VStack, Box } from '@chakra-ui/react';
import { FolderPlus } from 'lucide-react';
import { documentsApi } from '../../api/documents';
import { useQueryClient } from '@tanstack/react-query';

interface Props {
  parentId: number;
}

export const FileContextMenu: React.FC<{ children: React.ReactNode } & Props> = ({ children, parentId }) => {
  const [isCreating, setIsCreating] = useState(false);
  const [folderName, setFolderName] = useState('');
  const queryClient = useQueryClient();

  const handleCreateFolder = async () => {
    if (!folderName.trim()) return;

    try {
      await documentsApi.createFolder(folderName, parentId);
      await queryClient.invalidateQueries({ queryKey: ['documents'] });
      setFolderName('');
      setIsCreating(false);
    } catch (error) {
      console.error('Failed to create folder:', error);
    }
  };

  return (
    <ContextMenu.Root>
      <ContextMenu.Trigger>{children}</ContextMenu.Trigger>
      <ContextMenu.Portal>
        <ContextMenu.Content
          className="bg-white rounded-md shadow-lg p-1 min-w-[160px]"
        >
          {isCreating ? (
            <VStack p={2} gap={2}>
              <Input
                size="sm"
                value={folderName}
                onChange={(e) => setFolderName(e.target.value)}
                placeholder="Folder name"
                autoFocus
                onKeyPress={(e) => {
                  if (e.key === 'Enter') {
                    handleCreateFolder();
                  }
                }}
              />
              <Button
                size="sm"
                colorScheme="blue"
                w="full"
                onClick={handleCreateFolder}
              >
                Create
              </Button>
            </VStack>
          ) : (
            <ContextMenu.Item
              className="flex items-center px-2 py-1 text-sm outline-none cursor-default
                         hover:bg-blue-50 rounded"
              onClick={() => setIsCreating(true)}
            >
              <FolderPlus className="mr-2" size={16} />
              New Folder
            </ContextMenu.Item>
          )}
        </ContextMenu.Content>
      </ContextMenu.Portal>
    </ContextMenu.Root>
  );
};