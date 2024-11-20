import React, { useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FilePlus, X } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import { documentsApi } from '../../api/documents';

export const UploadArea: React.FC<{ parentId?: number }> = ({ parentId }) => {
  const [uploadStatus, setUploadStatus] = useState<{
    isUploading: boolean;
    files: { name: string; progress: number }[];
  }>({ isUploading: false, files: [] });
  const queryClient = useQueryClient();

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: async (files) => {
      setUploadStatus({ isUploading: true, files: files.map(f => ({ name: f.name, progress: 0 })) });

      try {
        await Promise.all(files.map(async (file, index) => {
          await documentsApi.upload(file, parentId);
          setUploadStatus(prev => ({
            ...prev,
            files: prev.files.map((f, i) => i === index ? { ...f, progress: 100 } : f)
          }));
        }));

        queryClient.invalidateQueries({ queryKey: ['documents'] });
        setTimeout(() => setUploadStatus({ isUploading: false, files: [] }), 1000);
      } catch (error) {
        setUploadStatus(prev => ({ ...prev, isUploading: false }));
      }
    },
    accept: {
      'text/*': ['.txt', '.md', '.pdf']
    }
  });

  return (
    <div className="p-4">
      <div
        {...getRootProps()}
        className={`
          relative overflow-hidden
          border-2 border-dashed rounded-lg p-6
          transition-all duration-300 ease-in-out
          ${isDragActive 
            ? 'border-blue-500 bg-blue-50 scale-102' 
            : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
          }
          ${uploadStatus.isUploading ? 'opacity-50 pointer-events-none' : ''}
        `}
      >
        <input {...getInputProps()} />

        <div className="flex flex-col items-center text-gray-500">
          {isDragActive ? (
            <>
              <FilePlus className="w-12 h-12 mb-3 text-blue-500 animate-pulse" />
              <p className="text-blue-500 font-medium">Release to upload files</p>
            </>
          ) : (
            <>
              <Upload className="w-12 h-12 mb-3" />
              <p className="font-medium mb-1">Drop files here or click to upload</p>
              <p className="text-sm text-gray-400">Supported formats: TXT, MD, JSON, CSV</p>
            </>
          )}
        </div>
      </div>

      {uploadStatus.isUploading && (
        <div className="mt-4 space-y-2">
          {uploadStatus.files.map((file, index) => (
            <div key={index} className="bg-gray-50 rounded-lg p-3">
              <div className="flex items-center justify-between mb-1">
                <span className="text-sm text-gray-600">{file.name}</span>
                <X className="w-4 h-4 text-gray-400 cursor-pointer hover:text-gray-600" />
              </div>
              <div className="h-1 bg-gray-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-blue-500 transition-all duration-300"
                  style={{ width: `${file.progress}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
