/**
 * User Activity page showing business activities for auditing
 * Based on folio-parse-stream design with Sanabil corporate styling
 */

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { AlertCircle, Info, CheckCircle2, AlertTriangle, Search, Download, RefreshCw, Loader2 } from "lucide-react";
import { useState, useEffect } from "react";

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

// API function to fetch activities
async function fetchActivities(params?: {
  limit?: number;
  offset?: number;
  activity_type?: string;
  user?: string;
  search?: string;
}): Promise<ActivitiesResponse> {
  const searchParams = new URLSearchParams();

  if (params?.limit) searchParams.set('limit', params.limit.toString());
  if (params?.offset) searchParams.set('offset', params.offset.toString());
  if (params?.activity_type && params.activity_type !== 'all') searchParams.set('activity_type', params.activity_type);
  if (params?.user && params.user !== 'all') searchParams.set('user', params.user);
  if (params?.search) searchParams.set('search', params.search);

  const url = `/api/logs${searchParams.toString() ? '?' + searchParams.toString() : ''}`;
  const response = await fetch(url);

  if (!response.ok) {
    throw new Error('Failed to fetch logs');
  }

  return await response.json();
}

export function ActivityLogsPage() {
  const [activities, setActivities] = useState<ActivityEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterActivityType, setFilterActivityType] = useState("all");
  const [filterUser, setFilterUser] = useState("all");
  const [totalActivities, setTotalActivities] = useState(0);

  const loadActivities = async () => {
    try {
      setIsLoading(true);
      const response = await fetchActivities({
        limit: 200,
        activity_type: filterActivityType === 'all' ? undefined : filterActivityType,
        user: filterUser === 'all' ? undefined : filterUser,
        search: searchTerm || undefined
      });

      setActivities(response.logs);
      setTotalActivities(response.total);
    } catch (error) {
      console.error('Error fetching activities:', error);
      // Could add toast notification here
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadActivities();
  }, [filterActivityType, filterUser]);

  // Debounced search
  useEffect(() => {
    const timer = setTimeout(() => {
      loadActivities();
    }, 500);

    return () => clearTimeout(timer);
  }, [searchTerm]);

  const formatDate = (dateString: string) => {
    if (!dateString) return 'Unknown';
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const getActivityBadge = (activityType: string) => {
    const variants = {
      "Upload": "bg-blue-100 text-blue-800",
      "Export": "bg-green-100 text-green-800",
      "Job Creation": "bg-purple-100 text-purple-800",
      "Job Completion": "bg-emerald-100 text-emerald-800",
      "Job Failure": "bg-red-100 text-red-800",
      "Schema Creation": "bg-orange-100 text-orange-800",
    } as const;

    return variants[activityType as keyof typeof variants] || "bg-gray-100 text-gray-800";
  };

  const activityCounts = {
    total: activities.length,
    uploads: activities.filter(a => a.activity_type === "Upload").length,
    exports: activities.filter(a => a.activity_type === "Export").length,
    jobCreations: activities.filter(a => a.activity_type === "Job Creation").length,
    jobCompletions: activities.filter(a => a.activity_type === "Job Completion").length,
    schemaCreations: activities.filter(a => a.activity_type === "Schema Creation").length
  };

  const activityTypes = ['Upload', 'Export', 'Job Creation', 'Job Completion', 'Job Failure', 'Schema Creation'];

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">User Activity</h1>
            <p className="text-muted-foreground">
              Track user actions and system activities for auditing and compliance
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={loadActivities} disabled={isLoading}>
              <RefreshCw className={`mr-2 h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              Export Activity Report
            </Button>
          </div>
        </div>

        {/* Filters */}
        <Card className="bg-card border-border shadow-soft">
          <CardHeader>
            <CardTitle className="text-lg">Filters</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4 flex-wrap">
              <div className="flex-1 min-w-[200px]">
                <div className="relative">
                  <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search activities..."
                    className="pl-9"
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                  />
                </div>
              </div>
              <Select value={filterActivityType} onValueChange={setFilterActivityType}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="Filter by activity" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Activities</SelectItem>
                  {activityTypes.map((type) => (
                    <SelectItem key={type} value={type}>
                      {type}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              <Select value={filterUser} onValueChange={setFilterUser}>
                <SelectTrigger className="w-[200px]">
                  <SelectValue placeholder="Filter by user" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Users</SelectItem>
                  <SelectItem value="System">System</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Logs */}
        <Card className="bg-card border-border shadow-soft">
          <CardHeader>
            <CardTitle className="text-lg">Recent Logs</CardTitle>
            <CardDescription>
              {isLoading ? 'Loading...' : `${activities.length} activity${activities.length !== 1 ? 'ies' : 'y'} found (${totalActivities} total)`}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                <span className="ml-2 text-muted-foreground">Loading logs...</span>
              </div>
            ) : (
              <ScrollArea className="h-[600px] pr-4">
                <div className="space-y-3">
                  {activities.length === 0 ? (
                    <div className="text-center py-12">
                      <Info className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                      <h3 className="text-lg font-semibold text-foreground mb-2">No activities found</h3>
                      <p className="text-muted-foreground">
                        {searchTerm || filterActivityType !== 'all' || filterUser !== 'all'
                          ? 'Try adjusting your filters or search term'
                          : 'No business activity recorded yet'}
                      </p>
                    </div>
                  ) : (
                    activities.map((activity) => (
                      <div
                        key={activity.id}
                        className="flex gap-3 p-4 border border-border rounded-lg hover:bg-muted/30 transition-colors"
                      >
                        <div className="flex-1 space-y-2">
                          <div className="flex items-center gap-2 flex-wrap">
                            <Badge className={getActivityBadge(activity.activity_type)}>
                              {activity.activity_type}
                            </Badge>
                            <Badge variant="secondary" className="text-xs">
                              {activity.user}
                            </Badge>
                            <span className="text-sm text-muted-foreground">
                              {formatDate(activity.timestamp)}
                            </span>
                          </div>
                          <div>
                            <p className="font-medium text-foreground">{activity.message}</p>
                            {activity.details && (
                              <p className="text-sm text-muted-foreground mt-1">{activity.details}</p>
                            )}
                          </div>
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </ScrollArea>
            )}
          </CardContent>
        </Card>

        {/* Stats Cards */}
        <div className="grid gap-4 md:grid-cols-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Activities</CardTitle>
              <Info className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{activityCounts.total}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Uploads</CardTitle>
              <AlertCircle className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">{activityCounts.uploads}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Exports</CardTitle>
              <Download className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{activityCounts.exports}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Jobs Created</CardTitle>
              <AlertTriangle className="h-4 w-4 text-purple-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-purple-600">{activityCounts.jobCreations}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Jobs Completed</CardTitle>
              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-emerald-600">{activityCounts.jobCompletions}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Schemas Created</CardTitle>
              <Info className="h-4 w-4 text-orange-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-orange-600">{activityCounts.schemaCreations}</div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}