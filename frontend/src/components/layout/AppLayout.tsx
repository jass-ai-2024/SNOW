import React, { useState } from 'react';
import {Grid, GridItem, Box} from '@chakra-ui/react';
import { Sidebar } from './Sidebar';
import { FileViewer } from '../documents/FileViewer';
import { SearchPanel } from '../search/SearchPanel';

type ViewMode = 'file' | 'search';

const AppLayout = () => {
  const [selectedId, setSelectedId] = useState<number | undefined>(undefined);
  const [viewMode, setViewMode] = useState<ViewMode>('file');

  return (
    <Grid templateColumns="350px 1fr" h="100vh">
      <GridItem p={4} borderRight="1px" borderColor="gray.200">
        <Sidebar selectedId={selectedId} setSelectedId={setSelectedId}/>
      </GridItem>
      <GridItem p={4}>
        <Box mb={4}>
          <Box as="button"
              px={4}
              py={2}
              mr={2}
              bg={viewMode === 'file' ? 'blue.500' : 'gray.100'}
              color={viewMode === 'file' ? 'white' : 'black'}
              borderRadius="md"
              onClick={() => setViewMode('file')}>
            File Viewer
          </Box>
          <Box as="button"
              px={4}
              py={2}
              bg={viewMode === 'search' ? 'blue.500' : 'gray.100'}
              color={viewMode === 'search' ? 'white' : 'black'}
              borderRadius="md"
              onClick={() => setViewMode('search')}>
            Search
          </Box>
        </Box>

        <Box mt={4}>
          {viewMode === 'file' ? (
            <FileViewer documentId={selectedId} />
          ) : (
            <SearchPanel />
          )}
        </Box>
      </GridItem>
    </Grid>
  );
};

export default AppLayout;