import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Skeleton } from "@/components/ui/skeleton";
import { useState, useEffect } from "react";
import { LogsService } from "@/fastapi_client";

interface ActivityEntry {
  id: string;
  timestamp: string;
  activity_type: string;
  message: string;
  details: string;
  user: string;
}

interface ActivitiesResponse {
  logs: ActivityEntry[];
  total: number;
  limit: number;
  offset: number;
}

function getActivityBadge(activityType: string) {
  const variants = {
    "Upload": "bg-blue-100 text-blue-800",
    "Export": "bg-green-100 text-green-800",
    "Job Creation": "bg-purple-100 text-purple-800",
    "Job Completion": "bg-emerald-100 text-emerald-800",
    "Job Failure": "bg-red-100 text-red-800",
    "Schema Creation": "bg-orange-100 text-orange-800",
  } as const;

  return variants[activityType as keyof typeof variants] || "bg-gray-100 text-gray-800";
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
  const [activities, setActivities] = useState<ActivityEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadActivities = async () => {
      try {
        setIsLoading(true);
        const response = await LogsService.getLogsApiLogsGet(10) as ActivitiesResponse;
        setActivities(response.logs || []);
      } catch (error) {
        console.error('Failed to fetch recent activities:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadActivities();
  }, []);

  if (isLoading) {
    return (
      <Card className="bg-card border-border shadow-soft flex flex-col">
        <CardHeader>
          <CardTitle className="text-lg font-semibold text-foreground">Recent Activity</CardTitle>
        </CardHeader>
        <CardContent className="h-96 overflow-y-auto space-y-4">
          {Array.from({ length: 4 }).map((_, i) => (
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
      <Card className="bg-card border-border shadow-soft flex flex-col">
        <CardHeader>
          <CardTitle className="text-lg font-semibold text-foreground">Recent Activity</CardTitle>
        </CardHeader>
        <CardContent className="h-96 p-6 text-center flex items-center justify-center">
          <div>
            <p className="text-muted-foreground">No recent activity found</p>
            <p className="text-xs text-muted-foreground mt-1">Activity will appear here as documents are processed</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-card border-border shadow-soft flex flex-col">
      <CardHeader className="pb-6">
        <CardTitle className="text-xl font-semibold text-foreground">Recent Activity</CardTitle>
      </CardHeader>
      <CardContent className="h-96 overflow-y-auto space-y-2">
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
                <Badge className={`text-xs px-2 py-0.5 ${getActivityBadge(activity.activity_type)}`}>
                  {activity.activity_type}
                </Badge>
              </div>
              <p className="text-sm text-muted-foreground">{activity.message}</p>
              {activity.details && (
                <p className="text-xs text-accent font-medium">{activity.details}</p>
              )}
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