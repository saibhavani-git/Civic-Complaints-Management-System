/** Hide queue/AI implementation details in timeline notes (matches backend sanitization). */

const INTERNAL_MARKERS = [
  "bullmq",
  "gemini",
  "openai",
  "ai routing",
  "ai pipeline",
  "ai queue",
  "ai processing failed",
  "returned to queue",
  "routing_source",
  "redis",
];

export function sanitizeTimelineNote(note: string | null | undefined): string | null {
  if (!note?.trim()) return null;
  const text = note.trim();
  const lower = text.toLowerCase();

  if (lower.includes("bullmq") || lower.includes("picked up from")) {
    return "Review started";
  }
  if (lower.includes("waiting in ai queue") || lower.startsWith("complaint submitted — waiting")) {
    return "Complaint received";
  }
  if (lower.includes("ai processing failed") || lower.includes("returned to queue")) {
    return "Review paused — we will try again shortly";
  }
  if (INTERNAL_MARKERS.some((m) => lower.includes(m))) {
    return null;
  }

  if (lower.startsWith("assigned to department:")) {
    const dept = text.split(":", 2)[1]?.trim();
    return dept ? `Sent to ${dept}` : "Sent to the municipal team";
  }
  if (lower.startsWith("worker assigned:")) {
    const name = text.split(":", 2)[1]?.trim();
    return name ? `Assigned to ${name}` : "Worker assigned";
  }

  return text;
}
