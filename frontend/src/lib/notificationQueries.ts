import type { Notification } from "@/types";

function notificationDedupeKey(n: Notification): string {
  return `${n.complaint_id ?? "none"}::${n.title}::${n.type ?? ""}`;
}

export function markNotificationReadInCache(
  notifications: Notification[] | undefined,
  id: string
): Notification[] {
  if (!notifications) return [];
  const target = notifications.find((n) => n.id === id);
  if (!target) return notifications;
  const key = notificationDedupeKey(target);
  return notifications.map((n) =>
    notificationDedupeKey(n) === key ? { ...n, is_read: true } : n
  );
}

export function markAllNotificationsReadInCache(
  notifications: Notification[] | undefined
): Notification[] {
  if (!notifications) return [];
  return notifications.map((n) => ({ ...n, is_read: true }));
}

/** One row per complaint + title — keeps the newest notification. */
export function dedupeNotificationsForDisplay(items: Notification[]): Notification[] {
  const seen = new Set<string>();
  const out: Notification[] = [];
  for (const n of items) {
    const key = notificationDedupeKey(n);
    if (seen.has(key)) continue;
    seen.add(key);
    out.push(n);
  }
  return out;
}
