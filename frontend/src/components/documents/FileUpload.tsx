import React, {useState} from "react";
import {Upload} from "lucide-react";
import {Button} from "@chakra-ui/react";
import {UploadModal} from "./UploadModal";

export const AddFileButton: React.FC<{ parentId?: number }> = ({ parentId }) => {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <>
      <Button
        colorScheme="blue"
        size="lg"
        onClick={() => setIsModalOpen(true)}
      >
        Add a file
      </Button>

      <UploadModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        parentId={parentId}
      />
    </>
  );
};