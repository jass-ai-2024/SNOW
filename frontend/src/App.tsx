// src/App.tsx
import React from 'react';
import {ChakraProvider, defaultSystem} from '@chakra-ui/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AppLayout from './components/layout/AppLayout';

const queryClient = new QueryClient();

const App = () => (
  <ChakraProvider value={defaultSystem}>
    <QueryClientProvider client={queryClient}>
      <AppLayout />
    </QueryClientProvider>
  </ChakraProvider>
);

export default App;