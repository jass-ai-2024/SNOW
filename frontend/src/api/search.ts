import axios from 'axios';
import { API_URL } from '../config/api';
import { SearchResult } from '../types/documents';

export const searchApi = {
  search: async (query: string) => {
    const response = await axios.get<SearchResult>(
      `${API_URL}/search/?query=${query}`,
    );
    return response.data;
  }
};