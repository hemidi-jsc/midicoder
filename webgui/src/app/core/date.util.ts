/**
 * Format a UTC ISO datetime string to local timezone.
 *
 * All datetimes from the backend are UTC. This converts them to the
 * browser's local timezone and returns "YYYY-MM-DD HH:MM:SS".
 */
export function formatDateLocal(iso: string): string {
  if (!iso) return '';
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso; // unparseable — return as-is

  const pad = (n: number) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`;
}
