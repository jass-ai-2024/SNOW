import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { documentsApi } from '../api/documents';

export const useDocuments = (parentId?: number | string, selectedId?: number) => {
  const queryClient = useQueryClient();

  const { data: documents, isLoading } = useQuery({
    queryKey: ['documents', parentId],
    queryFn: () => documentsApi.getAll(parentId)
  });

  const uploadMutation = useMutation({
    mutationFn: ({ file, parentId }: { file: File; parentId?: number }) =>
      documentsApi.upload(file, parentId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    }
  });

  const downloadMutation = useMutation({
    mutationFn: documentsApi.download
  });

  const { data: content, isLoading: isContentLoading } = useQuery({
    queryKey: ['document-content', selectedId],
    queryFn: () => selectedId ? documentsApi.getContent(selectedId) : null,
    enabled: !!selectedId
  });

  const { data: graphData } = useQuery({
    queryKey: ['documents-graph'],
    queryFn: documentsApi.getGraph
  });

  return {
    documents: documents || [],
    isLoading,
    uploadDocument: uploadMutation.mutate,
    downloadDocument: downloadMutation.mutate,
    content,
    isContentLoading,
    graphData
  };
};