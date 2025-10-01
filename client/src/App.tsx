/**
 * Main Application component with corporate sidebar navigation
 * Based on folio-parse-stream design patterns with Sanabil corporate styling
 */

import { useState, useEffect } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AppSidebar } from './components/AppSidebar';
import { AppHeader } from './components/AppHeader';
import { SchemasPage } from './pages/SchemasPage';
import { UploadPage } from './pages/UploadPage';
import { ResultsPage } from './pages/ResultsPage';
import { DashboardPage } from './pages/DashboardPage';
import { ActivityLogsPage } from './pages/ActivityLogsPage';

export type Page = 'dashboard' | 'schemas' | 'upload' | 'results' | 'logs';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// Helper function to get current page from URL
const getCurrentPageFromUrl = (): Page => {
  const path = window.location.pathname;
  if (path.includes('/upload')) return 'upload';
  if (path.includes('/results')) return 'results';
  if (path.includes('/schemas')) return 'schemas';
  if (path.includes('/logs')) return 'logs';
  if (path.includes('/dashboard')) return 'dashboard';
  // Default to dashboard for root path
  return 'dashboard';
};

// Helper function to update URL
const updateUrl = (page: Page) => {
  const path = `/${page}`;
  window.history.pushState(null, '', path);
};

function App() {
  const [currentPage, setCurrentPage] = useState<Page>(getCurrentPageFromUrl());
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // Handle browser back/forward navigation
  useEffect(() => {
    const handlePopState = () => {
      setCurrentPage(getCurrentPageFromUrl());
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  // Update page and URL
  const handlePageChange = (page: Page) => {
    setCurrentPage(page);
    updateUrl(page);
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'dashboard':
        return <DashboardPage onPageChange={handlePageChange} />;
      case 'schemas':
        return <SchemasPage />;
      case 'upload':
        return <UploadPage />;
      case 'results':
        return <ResultsPage />;
      case 'logs':
        return <ActivityLogsPage />;
      default:
        return <DashboardPage onPageChange={handlePageChange} />;
    }
  };

  return (
    <QueryClientProvider client={queryClient}>
      <div className="min-h-screen flex w-full bg-gradient-subtle">
        {/* Sidebar */}
        <AppSidebar
          currentPage={currentPage}
          onPageChange={handlePageChange}
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
