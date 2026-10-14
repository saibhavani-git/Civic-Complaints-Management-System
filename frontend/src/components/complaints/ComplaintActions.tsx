"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { complaintsApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader2 } from "lucide-react";
import type { Complaint, UserRole } from "@/types";

const TERMINAL = ["resolved", "closed", "rejected", "feedback_received"];

export function OfficerActions({ complaint, role }: { complaint: Complaint; role: UserRole }) {
  const queryClient = useQueryClient();
  const [note, setNote] = useState("");
  const [resolveNotes, setResolveNotes] = useState("");
  const [showResolve, setShowResolve] = useState(false);

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["complaint", complaint.id] });
    queryClient.invalidateQueries({ queryKey: ["complaints"] });
    queryClient.invalidateQueries({ queryKey: ["complaint"] });
  };

  const updateStatus = useMutation({
    mutationFn: (status: string) =>
      complaintsApi.updateStatus(complaint.id, { status, note: note || undefined }),
    onSuccess: () => {
      invalidate();
      setNote("");
    },
  });

  const resolve = useMutation({
    mutationFn: () => complaintsApi.resolve(complaint.id, resolveNotes),
    onSuccess: () => {
      invalidate();
      setShowResolve(false);
      setResolveNotes("");
    },
  });

  if (role === "citizen" || role === "dept_admin" || role === "admin" || TERMINAL.includes(complaint.status)) {
    return null;
  }

  const status = complaint.status;

  return (
    <section className="rounded-xl border bg-card p-5 shadow-sm space-y-4">
      <h2 className="text-sm font-semibold">Department actions</h2>

      {!showResolve ? (
        <>
          <div className="flex flex-wrap gap-2">
            {status === "assigned" && (
              <Button
                size="sm"
                variant="outline"
                disabled={updateStatus.isPending}
                onClick={() => updateStatus.mutate("work_started")}
              >
                Start field work
              </Button>
            )}
            {["assigned", "work_started", "in_progress"].includes(status) && (
              <Button size="sm" onClick={() => setShowResolve(true)}>
                Mark as finished
              </Button>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="note">Add a note (optional)</Label>
            <Input id="note" placeholder="Progress update..." value={note} onChange={(e) => setNote(e.target.value)} />
          </div>
        </>
      ) : (
        <div className="space-y-3">
          <div className="space-y-2">
            <Label htmlFor="resolve">Resolution notes</Label>
            <textarea
              id="resolve"
              className="flex min-h-[100px] w-full rounded-lg border border-input bg-background px-3 py-2 text-sm"
              placeholder="Describe how the issue was resolved..."
              value={resolveNotes}
              onChange={(e) => setResolveNotes(e.target.value)}
              required
              minLength={10}
            />
          </div>
          <div className="flex gap-2">
            <Button
              size="sm"
              disabled={resolve.isPending || resolveNotes.length < 10}
              onClick={() => resolve.mutate()}
            >
              {resolve.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : "Confirm resolution"}
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setShowResolve(false)}>
              Cancel
            </Button>
          </div>
        </div>
      )}
    </section>
  );
}

export function FeedbackForm({ complaintId }: { complaintId: string }) {
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const queryClient = useQueryClient();

  const submit = useMutation({
    mutationFn: () => complaintsApi.submitFeedback(complaintId, { rating, comment }),
    onSuccess: () => {
      setSubmitted(true);
      queryClient.invalidateQueries({ queryKey: ["complaint", complaintId] });
    },
  });

  if (submitted) {
    return (
      <section className="rounded-xl border border-emerald-200 bg-emerald-50/50 p-5">
        <p className="text-sm font-medium text-emerald-800">Thank you for your feedback!</p>
      </section>
    );
  }

  return (
    <section className="rounded-xl border bg-card p-5 shadow-sm space-y-4">
      <h2 className="text-sm font-semibold">Rate this resolution</h2>
      <div className="flex gap-1">
        {[1, 2, 3, 4, 5].map((n) => (
          <button
            key={n}
            type="button"
            onClick={() => setRating(n)}
            className={`h-10 w-10 rounded-lg text-lg transition-colors ${
              n <= rating ? "bg-amber-100 text-amber-600" : "bg-muted text-muted-foreground"
            }`}
          >
            ★
          </button>
        ))}
      </div>
      <textarea
        className="flex min-h-[80px] w-full rounded-lg border border-input bg-background px-3 py-2 text-sm"
        placeholder="Optional comment..."
        value={comment}
        onChange={(e) => setComment(e.target.value)}
      />
      <Button size="sm" disabled={submit.isPending} onClick={() => submit.mutate()}>
        {submit.isPending ? "Submitting..." : "Submit Feedback"}
      </Button>
    </section>
  );
}
