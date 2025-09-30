/**
 * Application Sidebar component with corporate branding
 * Based on folio-parse-stream design patterns with Sanabil corporate styling
 */

import { FileText, Upload, BarChart3, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Page } from '../App';

interface AppSidebarProps {
  currentPage: Page;
  onPageChange: (page: Page) => void;
  isOpen: boolean;
  onToggle: () => void;
  collapsed?: boolean;
}

export function AppSidebar({ currentPage, onPageChange, isOpen, onToggle, collapsed = false }: AppSidebarProps) {
  const navItems = [
    {
      id: 'schemas' as Page,
      label: 'Schema Management',
      icon: FileText,
      description: 'Define and manage extraction schemas',
    },
    {
      id: 'upload' as Page,
      label: 'Upload Documents',
      icon: Upload,
      description: 'Upload and process documents',
    },
    {
      id: 'results' as Page,
      label: 'Extraction Results',
      icon: BarChart3,
      description: 'View and export extraction results',
    },
  ];

  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-40 bg-black bg-opacity-50 lg:hidden"
          onClick={onToggle}
        />
      )}

      {/* Sidebar */}
      <div
        className={`fixed inset-y-0 left-0 z-50 ${collapsed ? 'w-16' : 'w-64'} bg-card border-r border-border shadow-strong transform transition-all duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        } lg:transform-none`}
      >
        {/* Mobile Close Button */}
        <div className="lg:hidden flex justify-end p-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggle}
            className="text-muted-foreground hover:text-foreground"
          >
            <X className="h-5 w-5" />
          </Button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-4 py-4 space-y-1">
          {navItems.map((item) => {
            const isActive = currentPage === item.id;
            const Icon = item.icon;

            return (
              <Button
                key={item.id}
                onClick={() => {
                  onPageChange(item.id);
                  if (window.innerWidth < 1024) {
                    onToggle(); // Close sidebar on mobile after selection
                  }
                }}
                variant={isActive ? "default" : "ghost"}
                className={`w-full ${collapsed ? 'justify-center px-2' : 'justify-start px-3'} text-left h-9 text-sm ${
                  isActive
                    ? 'bg-gradient-primary text-primary-foreground shadow-soft'
                    : 'text-muted-foreground hover:text-foreground hover:bg-accent/20'
                }`}
                title={item.description}
              >
                <Icon className={`h-4 w-4 ${collapsed ? '' : 'mr-3'}`} />
                {!collapsed && <span className="font-medium">{item.label}</span>}
              </Button>
            );
          })}
        </nav>

        {/* Footer - Only show when not collapsed */}
        {!collapsed && (
          <div className="p-3 border-t border-border">
            <div className="text-center">
              <p className="text-xs text-muted-foreground leading-tight">
                Powered by Databricks<br/>
                © 2024 Sanabil Investments
              </p>
            </div>
          </div>
        )}
      </div>
    </>
  );
}