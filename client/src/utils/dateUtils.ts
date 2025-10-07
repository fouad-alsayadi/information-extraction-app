/**
 * Shared date/time utilities with proper timezone handling
 */

/**
 * Creates a proper Date object from a timestamp, handling timezone correctly
 * The database stores timestamps in the server's local timezone (UTC+3)
 * but without timezone information, so we need to parse them correctly
 */
export function parseTimestamp(timestamp: string): Date {
  if (!timestamp) return new Date();

  // If already has timezone info (Z, +, or -), use as-is
  if (timestamp.includes('Z') || timestamp.includes('+') || timestamp.includes('-')) {
    return new Date(timestamp);
  }

  // Database timestamps are stored in server timezone (UTC+3) without timezone info
  // We need to parse them as if they were already in UTC+3
  // The correct approach is to treat the timestamp as UTC and then adjust for display

  // Treat the timestamp as UTC by appending 'Z'
  const utcTimestamp = timestamp + 'Z';
  return new Date(utcTimestamp);
}

/**
 * Formats a timestamp as a relative time (e.g., "5m ago", "2h ago")
 */
export function formatRelativeTime(timestamp: string): string {
  if (!timestamp) return 'Unknown';

  const date = parseTimestamp(timestamp);
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
