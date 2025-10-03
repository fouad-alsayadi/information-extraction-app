/**
 * Application Header component with logo and branding
 * Based on folio-parse-stream design patterns with Sanabil corporate styling
 * Always visible across all screen sizes
 */

import { useState, useEffect } from 'react';
import { Menu, Bell, User, PanelLeftClose, PanelLeft } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Page } from '../App';
import { UserService } from '../fastapi_client/services/UserService';
import type { UserInfo } from '../fastapi_client/models/UserInfo';
import logoImage from '@/assets/images/sanabil-main-logo.png';

interface AppHeaderProps {
  onMenuClick: () => void;
  currentPage: Page;
  sidebarCollapsed?: boolean;
  onSidebarToggle?: () => void;
}

export function AppHeader({ onMenuClick, sidebarCollapsed, onSidebarToggle }: AppHeaderProps) {
  const [userInfo, setUserInfo] = useState<UserInfo | null>(null);

  // Fetch user information on component mount
  useEffect(() => {
    const fetchUserInfo = async () => {
      try {
        const user = await UserService.getCurrentUserApiUserMeGet();
        setUserInfo(user);
      } catch (error) {
        console.error('Failed to fetch user info:', error);
        // Fallback to default user info
        setUserInfo({
          email: 'unknown@databricks.com',
          displayName: 'Unknown User',
          active: true,
        });
      }
    };

    fetchUserInfo();
  }, []);
  return (
    <header className="h-20 bg-card/50 backdrop-blur-sm border-b border-border shadow-soft">
      <div className="flex items-center justify-between px-4 h-full">
        {/* Left Side - Menu + Logo + Title */}
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            size="sm"
            onClick={onMenuClick}
            className="text-muted-foreground hover:text-foreground lg:hidden"
          >
            <Menu className="h-5 w-5" />
          </Button>

          {/* Desktop Sidebar Toggle */}
          <Button
            variant="ghost"
            size="sm"
            onClick={onSidebarToggle}
            className="text-muted-foreground hover:text-foreground hidden lg:flex"
          >
            {sidebarCollapsed ? (
              <PanelLeft className="h-5 w-5" />
            ) : (
              <PanelLeftClose className="h-5 w-5" />
            )}
          </Button>

          <div className="flex items-center space-x-3">
            <img
              src={logoImage}
              alt="Sanabil Investments"
              className="w-64 h-auto"
            />
            <div>
              <h1 className="text-2xl font-bold text-corporate">
                Information Extraction
              </h1>
              <p className="text-sm text-muted-foreground hidden sm:block">
                AI-Powered Document Analysis
              </p>
            </div>
          </div>
        </div>

        {/* Right Side - User Controls */}
        <div className="flex items-center space-x-2">
          <Button
            variant="ghost"
            size="sm"
            className="text-muted-foreground hover:text-foreground relative"
          >
            <Bell className="h-5 w-5" />
            <span className="absolute -top-1 -right-1 h-3 w-3 bg-destructive rounded-full text-xs"></span>
          </Button>

          {/* User Profile */}
          <div className="flex items-center space-x-3 ml-4">
            <div className="hidden md:block text-right">
              <p className="text-sm font-medium text-foreground">
                {userInfo?.displayName || 'Loading...'}
              </p>
              <p className="text-xs text-muted-foreground">
                {userInfo?.active ? 'Active User' : 'Inactive'}
              </p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              className="text-muted-foreground hover:text-foreground p-1"
              title={userInfo?.email || 'User Profile'}
            >
              <div className="w-8 h-8 bg-gradient-primary rounded-full flex items-center justify-center">
                <User className="h-4 w-4 text-primary-foreground" />
              </div>
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
}