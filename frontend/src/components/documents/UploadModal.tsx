import React, { useState, useEffect } from 'react';
import Modal from 'react-modal';
import { 
  Button, 
  VStack,
  Text, 
  Box,
  HStack,
  Icon
} from '@chakra-ui/react';
import { Progress } from "@chakra-ui/progress"
import { useDropzone } from 'react-dropzone';
import { Upload, Check, AlertCircle } from 'lucide-react';
import { documentsApi } from '../../api/documents';
import { useQueryClient } from '@tanstack/react-query';
const modalStyles = {
  content: {
    top: '50%',
    left: '50%',
    right: 'auto',
    bottom: 'auto',
    marginRight: '-50%',
    transform: 'translate(-50%, -50%)',
    width: '500px',
    padding: '0',
    border: 'none',
    borderRadius: '12px',
    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)'
  },
  overlay: {
    backgroundColor: 'rgba(0, 0, 0, 0.5)'
  }
};

Modal.setAppElement('#root');

interface UploadModalProps {
  isOpen: boolean;
  onClose: () => void;
  parentId?: number;
}

export const UploadModal: React.FC<UploadModalProps> = ({ isOpen, onClose, parentId }) => {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isUploading, setIsUploading] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);
  const queryClient = useQueryClient();

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (acceptedFiles) => {
      setSelectedFiles(acceptedFiles);
    },
    accept: {
      'text/*': ['.txt', '.md', '.pdf']
    }
  });

  useEffect(() => {
    if (!isUploading) return;

    let startTime = Date.now();
    const duration = 15000; // 15 seconds

    const timer = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min((elapsed / duration) * 100, 100);

      if (progress === 100) {
        clearInterval(timer);
        setIsCompleted(true);
        setTimeout(() => {
          setIsUploading(false);
          setUploadProgress(0);
          setSelectedFiles([]);
          setIsCompleted(false);
          onClose();
        }, 1000);
      } else {
        setUploadProgress(progress);
      }
    }, 100);

    return () => clearInterval(timer);
  }, [isUploading]);

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;

    setIsUploading(true);

    try {
      await Promise.all(selectedFiles.map(file => documentsApi.upload(file, parentId)));
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      alert(JSON.stringify({
        title: "Upload successful",
        status: "success",
        duration: 3000,
      }));
    } catch (error) {
      alert(JSON.stringify({
        title: "Upload failed",
        status: "error",
        duration: 3000,
      }));
      setIsUploading(false);
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onRequestClose={onClose}
      style={modalStyles}
      contentLabel="Upload Files"
    >
      <Box p={6}>
        <VStack gap={6} align="stretch">
          {!isUploading ? (
            <>
              <Text fontSize="xl" fontWeight="bold">Upload Files</Text>
              <Box
                {...getRootProps()}
                p={10}
                border="2px"
                borderStyle="dashed"
                borderColor={isDragActive ? "blue.500" : "gray.200"}
                borderRadius="lg"
                bg={isDragActive ? "blue.50" : "transparent"}
                transition="all 0.2s"
                _hover={{ borderColor: "blue.500" }}
              >
                <input {...getInputProps()} />
                <VStack gap={2}>
                  <Upload size={40} className={isDragActive ? "text-blue-500" : "text-gray-400"} />
                  <Text color={isDragActive ? "blue.500" : "gray.500"}>
                    {isDragActive
                      ? "Drop files here..."
                      : "Drag & drop files here or click to select"}
                  </Text>
                </VStack>
              </Box>
              {selectedFiles.length > 0 && (
                <VStack align="stretch" gap={2}>
                  <Text fontWeight="medium">Selected files:</Text>
                  {selectedFiles.map((file, index) => (
                    <Text key={index} fontSize="sm" color="gray.600">
                      {file.name}
                    </Text>
                  ))}
                </VStack>
              )}
              <HStack justify="flex-end" gap={3}>
                <Button variant="ghost" onClick={onClose}>
                  Cancel
                </Button>
                <Button
                  colorScheme="blue"
                  onClick={handleUpload}
                  // isDisabled={selectedFiles.length === 0}
                >
                  Upload
                </Button>
              </HStack>
            </>
          ) : (
            <VStack gap={4}>
              <Text fontSize="lg" fontWeight="medium">
                {isCompleted ? "Upload Complete!" : "Uploading..."}
              </Text>
              {isCompleted ? (
                <Check size={40} className="text-green-500" />
              ) : (
                <Progress
                  value={uploadProgress}
                  size="sm"
                  width="100%"
                  colorScheme="blue"
                  hasStripe
                  isAnimated
                />
              )}
            </VStack>
          )}
        </VStack>
      </Box>
    </Modal>
  );
};

// src/components/buttons/AddFileButton.tsx
export const AddFileButton: React.FC = () => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <>
      <Button
        // leftIcon={<Upload size={20} />}
        colorScheme="blue"
        onClick={() => setIsModalOpen(true)}
      >
        Add a file
      </Button>
      <UploadModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </>
  );
};