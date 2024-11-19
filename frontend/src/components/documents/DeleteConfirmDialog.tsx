import * as AlertDialog from '@radix-ui/react-alert-dialog';
import { AlertCircle } from 'lucide-react';
import './DeleteConfirmDialog.css'; // Добавим стили
import React from "react";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  isFolder: boolean;
}

export const DeleteConfirmDialog: React.FC<Props> = ({
  isOpen,
  onClose,
  onConfirm,
  isFolder,
}) => {
  return (
      <AlertDialog.Root open={isOpen} onOpenChange={onClose}>
    <AlertDialog.Portal>
      <AlertDialog.Overlay className="fixed inset-0 bg-black/50" />
      <AlertDialog.Content className="fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 bg-white rounded-lg p-6 w-[400px] shadow-xl">
        <AlertDialog.Title className="text-xl font-semibold mb-4">
          Delete {isFolder ? 'Folder' : 'Document'}
        </AlertDialog.Title>

        <AlertDialog.Description className="flex items-center gap-2 mb-6 text-gray-600">
          <AlertCircle className="text-red-500" size={20} />
          <span>
            Are you sure you want to delete this {isFolder ? 'folder' : 'document'}?
            {isFolder && " Make sure it's empty."}
          </span>
        </AlertDialog.Description>

        <div className="flex justify-end gap-3">
          <AlertDialog.Cancel asChild>
            <button className="px-4 py-2 rounded bg-gray-100 hover:bg-gray-200 transition-colors">
              Cancel
            </button>
          </AlertDialog.Cancel>
          <AlertDialog.Action asChild>
            <button
              className="px-4 py-2 rounded bg-red-500 text-white hover:bg-red-600 transition-colors"
              onClick={onConfirm}
            >
              Delete
            </button>
          </AlertDialog.Action>
        </div>
      </AlertDialog.Content>
    </AlertDialog.Portal>
  </AlertDialog.Root>
  )
}