/**
 * Dashboard page showing overview statistics and recent activity
 * Based on folio-parse-stream design with Sanabil corporate styling
 */

import { DashboardStats } from '@/components/dashboard/DashboardStats';
import { RecentActivity } from '@/components/dashboard/RecentActivity';
import { ProcessingQueue } from '@/components/dashboard/ProcessingQueue';
import { Button } from '@/components/ui/button';
import { Upload, Plus, BarChart3 } from 'lucide-react';

interface DashboardPageProps {
  onPageChange: (page: 'schemas' | 'upload' | 'results' | 'dashboard') => void;
}

export function DashboardPage({ onPageChange }: DashboardPageProps) {
  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Welcome Section */}
        <div className="bg-gradient-primary rounded-xl p-8 text-center text-primary-foreground shadow-medium">
          <h1 className="text-3xl font-bold mb-2">Information Extraction Platform</h1>
          <p className="text-primary-foreground/90 text-lg mb-6">
            Streamline your document analysis with AI-powered information extraction
          </p>
          <div className="flex justify-center gap-4">
            <Button
              variant="secondary"
              className="bg-white/20 hover:bg-white/30 text-white border-white/30"
              onClick={() => onPageChange('upload')}
            >
              <Upload className="mr-2 h-4 w-4" />
              Upload Documents
            </Button>
            <Button
              variant="secondary"
              className="bg-white/20 hover:bg-white/30 text-white border-white/30"
              onClick={() => onPageChange('schemas')}
            >
              <Plus className="mr-2 h-4 w-4" />
              Create Schema
            </Button>
          </div>
        </div>

        {/* Statistics */}
        <DashboardStats />

        {/* Main Content Grid */}
        <div className="grid gap-6 lg:grid-cols-2">
          <ProcessingQueue onPageChange={onPageChange} />
          <RecentActivity />
        </div>

        {/* Quick Actions */}
        <div className="grid gap-4 md:grid-cols-3">
          <div className="bg-card border border-border rounded-lg p-6 text-center hover:shadow-soft transition-all duration-200">
            <Upload className="h-8 w-8 text-accent mx-auto mb-3" />
            <h3 className="font-semibold text-foreground mb-2">Bulk Upload</h3>
            <p className="text-sm text-muted-foreground mb-4">Upload multiple documents for processing</p>
            <Button variant="outline" size="sm" onClick={() => onPageChange('upload')}>Get Started</Button>
          </div>

          <div className="bg-card border border-border rounded-lg p-6 text-center hover:shadow-soft transition-all duration-200">
            <Plus className="h-8 w-8 text-accent mx-auto mb-3" />
            <h3 className="font-semibold text-foreground mb-2">Schema Builder</h3>
            <p className="text-sm text-muted-foreground mb-4">Define extraction templates</p>
            <Button variant="outline" size="sm" onClick={() => onPageChange('schemas')}>Create Schema</Button>
          </div>

          <div className="bg-card border border-border rounded-lg p-6 text-center hover:shadow-soft transition-all duration-200">
            <BarChart3 className="h-8 w-8 text-accent mx-auto mb-3" />
            <h3 className="font-semibold text-foreground mb-2">Analytics</h3>
            <p className="text-sm text-muted-foreground mb-4">View processing insights</p>
            <Button variant="outline" size="sm" onClick={() => onPageChange('results')}>View Reports</Button>
          </div>
        </div>
      </div>
    </div>
  );
}