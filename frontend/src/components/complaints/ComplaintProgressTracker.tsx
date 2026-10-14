"use client";

import { cn } from "@/lib/utils";
import { TRACKING_STEPS, trackingStepIndex } from "@/lib/complaintStatus";
import { Check } from "lucide-react";

export function ComplaintProgressTracker({ status }: { status: string }) {
  const current = trackingStepIndex(status);
  const allDone = current >= TRACKING_STEPS.length;

  return (
    <ol className="flex flex-col gap-0 sm:flex-row sm:items-start sm:justify-between sm:gap-2">
      {TRACKING_STEPS.map((label, i) => {
        const complete = allDone || i < current;
        const active = !allDone && i === current;
        return (
          <li
            key={label}
            className={cn(
              "flex flex-1 items-start gap-2 sm:flex-col sm:items-center sm:text-center pb-4 sm:pb-0 last:pb-0",
              i < TRACKING_STEPS.length - 1 && "sm:border-r sm:border-border sm:pr-2"
            )}
          >
            <span
              className={cn(
                "flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-semibold border-2",
                complete && "border-emerald-500 bg-emerald-500 text-white",
                active && !complete && "border-primary bg-primary/10 text-primary",
                !complete && !active && "border-muted-foreground/30 text-muted-foreground"
              )}
            >
              {complete ? <Check className="h-4 w-4" /> : i + 1}
            </span>
            <span
              className={cn(
                "text-xs font-medium pt-1 sm:pt-2",
                active && "text-foreground",
                complete && "text-emerald-700",
                !complete && !active && "text-muted-foreground"
              )}
            >
              {label}
            </span>
          </li>
        );
      })}
    </ol>
  );
}
