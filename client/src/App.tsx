import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Navigation, Page } from './components/Navigation';
import { SchemasPage } from './pages/SchemasPage';
import { UploadPage } from './pages/UploadPage';
import { ResultsPage } from './pages/ResultsPage';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('schemas');

  const renderPage = () => {
    switch (currentPage) {
      case 'schemas':
        return <SchemasPage />;
      case 'upload':
        return <UploadPage />;
      case 'results':
        return <ResultsPage />;
      default:
        return <SchemasPage />;
    }
  };

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen bg-gray-50">
        <Navigation currentPage={currentPage} onPageChange={setCurrentPage} />
        <main>{renderPage()}</main>
      </div>
    </QueryClientProvider>
  );
}

export default App;
