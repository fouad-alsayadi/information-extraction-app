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
import { JobDetailsPage } from './pages/JobDetailsPage';
import { SchemaDetailsPage } from './pages/SchemaDetailsPage';

export type Page =
  | 'dashboard'
  | 'schemas'
  | 'upload'
  | 'results'
  | 'logs'
  | 'job-details'
  | 'schema-details'
  | { type: 'upload'; selectedSchemaId?: number };

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
const getCurrentPageFromUrl = (): { page: Page; jobId?: number; schemaId?: number } => {
  const path = window.location.pathname;
  if (path.includes('/upload')) return { page: 'upload' };
  if (path.includes('/results')) return { page: 'results' };
  if (path.includes('/logs')) return { page: 'logs' };
  if (path.includes('/dashboard')) return { page: 'dashboard' };

  // Check for schema details pattern: /schemas/:id
  const schemaMatch = path.match(/^\/schemas\/(\d+)$/);
  if (schemaMatch) {
    return { page: 'schema-details', schemaId: parseInt(schemaMatch[1]) };
  }

  if (path.includes('/schemas')) return { page: 'schemas' };

  // Check for job details pattern: /jobs/:id
  const jobMatch = path.match(/^\/jobs\/(\d+)$/);
  if (jobMatch) {
    return { page: 'job-details', jobId: parseInt(jobMatch[1]) };
  }

  // Default to dashboard for root path
  return { page: 'dashboard' };
};

// Helper function to update URL
const updateUrl = (page: Page, jobId?: number, schemaId?: number) => {
  let path: string;
  if (page === 'job-details' && jobId) {
    path = `/jobs/${jobId}`;
  } else if (page === 'schema-details' && schemaId) {
    path = `/schemas/${schemaId}`;
  } else {
    path = `/${page}`;
  }
  window.history.pushState(null, '', path);
};

function App() {
  const urlState = getCurrentPageFromUrl();
  const [currentPage, setCurrentPage] = useState<Page>(urlState.page);
  const [currentJobId, setCurrentJobId] = useState<number | undefined>(urlState.jobId);
  const [currentSchemaId, setCurrentSchemaId] = useState<number | undefined>(urlState.schemaId);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // Handle browser back/forward navigation
  useEffect(() => {
    const handlePopState = () => {
      const urlState = getCurrentPageFromUrl();
      setCurrentPage(urlState.page);
      setCurrentJobId(urlState.jobId);
      setCurrentSchemaId(urlState.schemaId);
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  // Update page and URL
  const handlePageChange = (page: Page, jobId?: number, schemaId?: number) => {
    setCurrentPage(page);
    setCurrentJobId(jobId);
    setCurrentSchemaId(schemaId);
    updateUrl(page, jobId, schemaId);
  };

  const renderPage = () => {
    // Handle both string and object Page types
    const pageType = typeof currentPage === 'string' ? currentPage : currentPage.type;

    switch (pageType) {
      case 'dashboard':
        return <DashboardPage onPageChange={handlePageChange} />;
      case 'schemas':
        return <SchemasPage onPageChange={handlePageChange} />;
      case 'upload':
        const selectedSchemaId = typeof currentPage === 'object' ? currentPage.selectedSchemaId : undefined;
        return <UploadPage selectedSchemaId={selectedSchemaId} />;
      case 'results':
        return <ResultsPage onPageChange={handlePageChange} />;
      case 'logs':
        return <ActivityLogsPage />;
      case 'job-details':
        return currentJobId ? (
          <JobDetailsPage jobId={currentJobId} onPageChange={handlePageChange} />
        ) : (
          <DashboardPage onPageChange={handlePageChange} />
        );
      case 'schema-details':
        return currentSchemaId ? (
          <SchemaDetailsPage schemaId={currentSchemaId} onPageChange={handlePageChange} />
        ) : (
          <SchemasPage />
        );
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
