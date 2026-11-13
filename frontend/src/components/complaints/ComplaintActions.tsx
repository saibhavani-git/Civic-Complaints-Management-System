"use client";

import { useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { complaintsApi } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Loader2, Upload } from "lucide-react";
import type { Complaint, UserRole } from "@/types";

const TERMINAL = ["resolved", "closed", "rejected", "feedback_received"];
const FIELD_ACTIVE = ["assigned", "work_started", "in_progress"];

export function OfficerActions({ complaint, role }: { complaint: Complaint; role: UserRole }) {
  const queryClient = useQueryClient();
  const [note, setNote] = useState("");
  const fileRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<FileList | null>(null);

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

  const uploadPhotos = useMutation({
    mutationFn: () => {
      if (!files?.length) throw new Error("Select at least one photo");
      const fd = new FormData();
      Array.from(files).forEach((f) => fd.append("images", f));
      if (note.trim()) fd.append("note", note.trim());
      return complaintsApi.uploadFieldPhotos(complaint.id, fd);
    },
    onSuccess: () => {
      invalidate();
      setFiles(null);
      setNote("");
      if (fileRef.current) fileRef.current.value = "";
    },
  });

  const uploadError =
    uploadPhotos.error &&
    (uploadPhotos.error as { response?: { data?: { detail?: string } } }).response?.data?.detail;

  if (role !== "officer" || TERMINAL.includes(complaint.status)) {
    return null;
  }

  const status = complaint.status;

  return (
    <section className="rounded-xl border bg-card p-5 shadow-sm space-y-4">
      <h2 className="text-sm font-semibold">Field work</h2>
      <p className="text-sm text-muted-foreground">
        Upload photos after fixing the issue. Your department admin will review them and mark the complaint finished.
      </p>

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
      </div>

      {FIELD_ACTIVE.includes(status) && (
        <div className="space-y-3 border-t pt-4">
          <div className="space-y-2">
            <Label htmlFor="field-photos">Completion photos</Label>
            <Input
              id="field-photos"
              ref={fileRef}
              type="file"
              accept="image/*"
              multiple
              onChange={(e) => setFiles(e.target.files)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="officer-note">Note (optional)</Label>
            <Input
              id="officer-note"
              placeholder="What was done on site..."
              value={note}
              onChange={(e) => setNote(e.target.value)}
            />
          </div>
          <Button
            size="sm"
            disabled={uploadPhotos.isPending || !files?.length}
            onClick={() => uploadPhotos.mutate()}
            className="gap-2"
          >
            {uploadPhotos.isPending ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Upload className="h-4 w-4" />
            )}
            Submit photos for review
          </Button>
          {uploadError && (
            <p className="text-sm text-destructive">{String(uploadError)}</p>
          )}
          {uploadPhotos.isError && !uploadError && (
            <p className="text-sm text-destructive">Upload failed. Restart the API on port 8002 and try again.</p>
          )}
        </div>
      )}
    </section>
  );
}

export function DeptAdminResolveActions({
  complaint,
  role,
  canManage,
}: {
  complaint: Complaint;
  role: UserRole;
  canManage: boolean;
}) {
  const queryClient = useQueryClient();
  const [resolveNotes, setResolveNotes] = useState("");
  const [showResolve, setShowResolve] = useState(false);

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["complaint", complaint.id] });
    queryClient.invalidateQueries({ queryKey: ["complaints"] });
  };

  const resolve = useMutation({
    mutationFn: () => complaintsApi.resolve(complaint.id, resolveNotes),
    onSuccess: () => {
      invalidate();
      setShowResolve(false);
      setResolveNotes("");
    },
  });

  if (!canManage || (role !== "dept_admin" && role !== "admin") || TERMINAL.includes(complaint.status)) {
    return null;
  }

  const hasFieldPhotos = (complaint.field_completion_images?.length ?? 0) > 0;
  if (!hasFieldPhotos) {
    return (
      <section className="rounded-xl border border-dashed bg-muted/30 p-5 text-sm text-muted-foreground">
        Waiting for the assigned officer to upload completion photos before you can mark this complaint finished.
      </section>
    );
  }

  if (!showResolve) {
    return (
      <section className="rounded-xl border bg-card p-5 shadow-sm space-y-3">
        <h2 className="text-sm font-semibold">Close complaint</h2>
        <p className="text-sm text-muted-foreground">
          Review the officer&apos;s completion photos above, then mark the case finished for the citizen.
        </p>
        <Button size="sm" onClick={() => setShowResolve(true)}>
          Mark as finished
        </Button>
      </section>
    );
  }

  return (
    <section className="rounded-xl border bg-card p-5 shadow-sm space-y-3">
      <h2 className="text-sm font-semibold">Confirm resolution</h2>
      <div className="space-y-2">
        <Label htmlFor="resolve">Resolution notes (visible in timeline)</Label>
        <textarea
          id="resolve"
          className="flex min-h-[100px] w-full rounded-lg border border-input bg-background px-3 py-2 text-sm"
          placeholder="Confirm work completed based on field photos..."
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
          {resolve.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : "Confirm finished"}
        </Button>
        <Button size="sm" variant="ghost" onClick={() => setShowResolve(false)}>
          Cancel
        </Button>
      </div>
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
