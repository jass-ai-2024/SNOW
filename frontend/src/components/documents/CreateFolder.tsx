import React, { useState } from 'react';
import {
  Input,
  HStack,
  VStack,
  IconButton
} from '@chakra-ui/react';
import { Plus, FolderPlus } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { documentsApi } from '../../api/documents';

interface CreateFolderProps {
  parentId?: number;
}

export const CreateFolder: React.FC<CreateFolderProps> = ({ parentId }) => {
  const [isCreating, setIsCreating] = useState(false);
  const [folderName, setFolderName] = useState('');
  const queryClient = useQueryClient();

  const handleCreate = async () => {
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

  if (!isCreating) {
    return (
      <IconButton
        aria-label="Create folder"
        size="sm"
        variant="ghost"
        onClick={() => setIsCreating(true)}
      >
          <FolderPlus size={18} />
      </IconButton>
    );
  }

  return (
    <HStack gap={2}>
      <Input
        size="sm"
        placeholder="Folder name"
        value={folderName}
        onChange={(e) => setFolderName(e.target.value)}
        onKeyPress={(e) => {
          if (e.key === 'Enter') {
            handleCreate();
          }
        }}
      />
      <IconButton
        aria-label="Create"
        size="sm"
        onClick={handleCreate}
      >
          <Plus size={18} />
      </IconButton>
    </HStack>
  );
};
