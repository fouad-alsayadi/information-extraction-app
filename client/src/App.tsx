/**
 * Main Application component with corporate sidebar navigation
 * Based on folio-parse-stream design patterns with Sanabil corporate styling
 */

import { useState } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppSidebar } from './components/AppSidebar';
import { AppHeader } from './components/AppHeader';
import { SchemasPage } from './pages/SchemasPage';
import { UploadPage } from './pages/UploadPage';
import { ResultsPage } from './pages/ResultsPage';

export type Page = 'schemas' | 'upload' | 'results';

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
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

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
      <div className="min-h-screen flex w-full bg-gradient-subtle">
        {/* Sidebar */}
        <AppSidebar
          currentPage={currentPage}
          onPageChange={setCurrentPage}
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
          collapsed={sidebarCollapsed}
        />

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col">
          {/* Header - Always Visible */}
          <AppHeader
            onMenuClick={() => setSidebarOpen(true)}
            currentPage={currentPage}
            sidebarCollapsed={sidebarCollapsed}
            onSidebarToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
          />

          {/* Page Content */}
          <main className="flex-1">
            {renderPage()}
          </main>
        </div>
      </div>
    </QueryClientProvider>
  );
}

export default App;
