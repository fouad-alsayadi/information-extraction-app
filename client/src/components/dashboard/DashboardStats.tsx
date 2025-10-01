import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { FileText, Database, Activity, TrendingUp } from "lucide-react";
import { useState, useEffect } from "react";
import { DashboardService } from "@/fastapi_client";

interface DashboardStatsData {
  total_jobs: number;
  pending_jobs: number;
  processing_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  total_schemas: number;
  active_schemas: number;
  total_documents: number;
  total_file_size: number;
  total_results: number;
  success_rate: number;
  last_updated: string;
}

export function DashboardStats() {
  const [stats, setStats] = useState<DashboardStatsData | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setIsLoading(true);
        const data = await DashboardService.getDashboardStatsApiDashboardStatsGet();
        setStats(data as DashboardStatsData);
      } catch (error) {
        console.error('Failed to fetch dashboard stats:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (isLoading) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i} className="bg-card border-border shadow-soft">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <Skeleton className="h-4 w-24" />
              <Skeleton className="h-4 w-4" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16 mb-2" />
              <Skeleton className="h-3 w-20" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card className="bg-card border-border shadow-soft">
          <CardContent className="p-6 text-center">
            <p className="text-muted-foreground">Failed to load dashboard stats</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const dashboardCards = [
    {
      title: "Total Documents",
      value: stats.total_documents.toLocaleString(),
      change: `${formatFileSize(stats.total_file_size)} processed`,
      icon: FileText,
      trend: stats.total_documents > 0 ? "up" : "neutral",
    },
    {
      title: "Active Schemas",
      value: stats.active_schemas.toString(),
      change: `${stats.total_schemas} total schemas`,
      icon: Database,
      trend: stats.active_schemas > 0 ? "up" : "neutral",
    },
    {
      title: "Processing Jobs",
      value: (stats.pending_jobs + stats.processing_jobs).toString(),
      change: `${stats.processing_jobs} running now`,
      icon: Activity,
      trend: stats.processing_jobs > 0 ? "up" : "neutral",
    },
    {
      title: "Success Rate",
      value: `${stats.success_rate}%`,
      change: `${stats.completed_jobs} completed`,
      icon: TrendingUp,
      trend: stats.completed_jobs > 0 ? "up" : "neutral", // Completed jobs should always be positive
    },
  ];

  return (
    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
      {dashboardCards.map((stat) => (
        <Card key={stat.title} className="bg-card border-border shadow-soft hover:shadow-medium transition-all duration-300">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {stat.title}
            </CardTitle>
            <stat.icon className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-foreground">{stat.value}</div>
            <p className={`text-xs ${
              stat.trend === 'up' ? 'text-success' :
              stat.trend === 'down' ? 'text-destructive' :
              'text-muted-foreground'
            }`}>
              {stat.change}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}