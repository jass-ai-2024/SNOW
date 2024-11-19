import React, { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Box, Text, VStack } from '@chakra-ui/react';
import { useDocuments } from '../../hooks/useDocuments';

export const FileUpload = ({ parentId }: { parentId: number | undefined }) => {
  const { uploadDocument } = useDocuments();

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    try {
      await Promise.all(
        acceptedFiles.map(file => uploadDocument({ file, parentId: parentId }))
      );
      // TODO: Should be toast
      console.log({
        title: 'Success',
        description: 'Files uploaded successfully',
        status: 'success',
      });
    } catch (err) {
      // TODO: Should be toast
      console.log({
        title: 'Error',
        description: 'Failed to upload files',
        status: 'error',
      });
    }
  }, [uploadDocument, parentId]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/*': ['.txt', '.md', '.json', '.csv']
    }
  });

  return (
    <Box
      {...getRootProps()}
      p={4}
      border="2px dashed"
      borderColor={isDragActive ? 'blue.500' : 'gray.200'}
      borderRadius="md"
      bg={isDragActive ? 'blue.50' : 'transparent'}
      cursor="pointer"
    >
      <input {...getInputProps()} />
      <VStack>
        <Text>
          {isDragActive ? 'Drop files here' : 'Drag files or click to upload'}
        </Text>
        <Text fontSize="sm" color="gray.500">
          Only text files allowed
        </Text>
      </VStack>
    </Box>
  );
};