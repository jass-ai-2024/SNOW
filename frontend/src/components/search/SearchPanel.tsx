// src/components/search/SearchPanel.tsx
import React, { useState } from 'react';
import {
  VStack,
  Input,
  Box,
  Text,
  Button,
  Spinner,
  Highlight
} from '@chakra-ui/react';
import { useSearch } from '../../hooks/useSearch';

export const SearchPanel: React.FC = () => {
  const [query, setQuery] = useState('');
  const { search, results, isLoading } = useSearch();

  const handleSearch = async () => {
    if (query.trim()) {
      await search(query);
    }
  };

  return (
    <VStack gap={4} align="stretch">
      <Box>
        <Input
          placeholder="Search in documents..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={(e) => {
            if (e.key === 'Enter') {
              handleSearch();
            }
          }}
        />
        <Button
          mt={2}
          colorScheme="blue"
          disabled={isLoading}
          onClick={handleSearch}
        >
          {isLoading ? <Spinner size="sm" mr={2} /> : null}
          {isLoading ? 'Searching...' : 'Search'}
        </Button>
      </Box>

      {results?.documents.map(doc => (
        <Box
          key={doc.id}
          p={4}
          borderRadius="md"
          bg="gray.50"
          boxShadow="sm"
          _hover={{ boxShadow: "md" }}
        >
          <Text fontWeight="bold" mb={2}>Document ID: {doc.id}</Text>
          <Text>
            <Highlight
              query={query}
              styles={{ bg: 'yellow.200', px: '2', py: '1', rounded: 'full' }}
            >
              {doc.subcontent}
            </Highlight>
          </Text>
        </Box>
      ))}
    </VStack>
  );
};