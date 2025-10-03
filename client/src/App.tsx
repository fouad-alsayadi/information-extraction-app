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

export type Page = 'dashboard' | 'schemas' | 'upload' | 'results' | 'logs' | 'job-details';

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
const getCurrentPageFromUrl = (): { page: Page; jobId?: number } => {
  const path = window.location.pathname;
  if (path.includes('/upload')) return { page: 'upload' };
  if (path.includes('/results')) return { page: 'results' };
  if (path.includes('/schemas')) return { page: 'schemas' };
  if (path.includes('/logs')) return { page: 'logs' };
  if (path.includes('/dashboard')) return { page: 'dashboard' };

  // Check for job details pattern: /jobs/:id
  const jobMatch = path.match(/^\/jobs\/(\d+)$/);
  if (jobMatch) {
    return { page: 'job-details', jobId: parseInt(jobMatch[1]) };
  }

  // Default to dashboard for root path
  return { page: 'dashboard' };
};

// Helper function to update URL
const updateUrl = (page: Page, jobId?: number) => {
  const path = page === 'job-details' && jobId ? `/jobs/${jobId}` : `/${page}`;
  window.history.pushState(null, '', path);
};

function App() {
  const urlState = getCurrentPageFromUrl();
  const [currentPage, setCurrentPage] = useState<Page>(urlState.page);
  const [currentJobId, setCurrentJobId] = useState<number | undefined>(urlState.jobId);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // Handle browser back/forward navigation
  useEffect(() => {
    const handlePopState = () => {
      const urlState = getCurrentPageFromUrl();
      setCurrentPage(urlState.page);
      setCurrentJobId(urlState.jobId);
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  // Update page and URL
  const handlePageChange = (page: Page, jobId?: number) => {
    setCurrentPage(page);
    setCurrentJobId(jobId);
    updateUrl(page, jobId);
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
        return <ResultsPage onPageChange={handlePageChange} />;
      case 'logs':
        return <ActivityLogsPage />;
      case 'job-details':
        return currentJobId ? (
          <JobDetailsPage jobId={currentJobId} onPageChange={handlePageChange} />
        ) : (
          <DashboardPage onPageChange={handlePageChange} />
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
