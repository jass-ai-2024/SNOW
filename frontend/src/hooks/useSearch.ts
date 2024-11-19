import { useMutation } from '@tanstack/react-query';
import { searchApi } from '../api/search';

export const useSearch = () => {
  const mutation = useMutation({
    mutationFn: searchApi.search
  });

  return {
    search: mutation.mutate,
    results: mutation.data,
    isLoading: mutation.isPending
  };
};