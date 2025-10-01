import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import { useState, useEffect } from "react";
import { DashboardService } from "@/fastapi_client";

interface Activity {
  id: string;
  user: string;
  action: string;
  schema: string;
  timestamp: string;
  type: string;
  job_id: number;
}

function getActivityBadge(type: string) {
  const variants = {
    success: "bg-green-100 text-green-700 border-green-200",
    process: "bg-blue-100 text-blue-700 border-blue-200",
    error: "bg-red-100 text-red-700 border-red-200",
    upload: "bg-purple-100 text-purple-700 border-purple-200",
    update: "bg-gray-100 text-gray-700 border-gray-200",
  } as const;

  return variants[type as keyof typeof variants] || variants.update;
}

function formatRelativeTime(timestamp: string): string {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / (1000 * 60));
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

export function RecentActivity() {
  const [activities, setActivities] = useState<Activity[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchActivities = async () => {
      try {
        setIsLoading(true);
        const response = await DashboardService.getRecentActivityApiDashboardRecentActivityGet();
        setActivities(response.activities || []);
      } catch (error) {
        console.error('Failed to fetch recent activities:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchActivities();
  }, []);

  if (isLoading) {
    return (
      <Card className="bg-card border-border shadow-soft">
        <CardHeader>
          <CardTitle className="text-lg font-semibold text-foreground">Recent Activity</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="flex items-center gap-4 p-3 rounded-lg">
              <Skeleton className="h-8 w-8 rounded-full" />
              <div className="flex-1 space-y-2">
                <div className="flex items-center gap-2">
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-4 w-12" />
                </div>
                <Skeleton className="h-3 w-32" />
                <Skeleton className="h-3 w-24" />
              </div>
              <Skeleton className="h-3 w-16" />
            </div>
          ))}
        </CardContent>
      </Card>
    );
  }

  if (activities.length === 0) {
    return (
      <Card className="bg-card border-border shadow-soft">
        <CardHeader>
          <CardTitle className="text-lg font-semibold text-foreground">Recent Activity</CardTitle>
        </CardHeader>
        <CardContent className="p-6 text-center">
          <p className="text-muted-foreground">No recent activity found</p>
          <p className="text-xs text-muted-foreground mt-1">Activity will appear here as documents are processed</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-card border-border shadow-soft">
      <CardHeader>
        <CardTitle className="text-lg font-semibold text-foreground">Recent Activity</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {activities.map((activity) => (
          <div key={activity.id} className="flex items-center gap-4 p-3 rounded-lg hover:bg-muted/50 transition-colors">
            <Avatar className="h-8 w-8">
              <AvatarFallback className="bg-primary/10 text-primary text-xs font-medium">
                {activity.user.split(' ').map(n => n[0]).join('')}
              </AvatarFallback>
            </Avatar>
            <div className="flex-1 space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-foreground">{activity.user}</span>
                <Badge className={`text-xs px-2 py-0.5 ${getActivityBadge(activity.type)}`}>
                  {activity.type}
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground">{activity.action}</p>
              <p className="text-xs text-accent font-medium">{activity.schema}</p>
            </div>
            <div className="text-xs text-muted-foreground">
              {formatRelativeTime(activity.timestamp)}
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  );
}