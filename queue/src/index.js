/**
 * BullMQ worker + enqueue HTTP API for the FastAPI backend.
 *
 * FastAPI POST /enqueue/complaint-ai → job added to Redis queue → worker calls internal process route.
 * Uses REDIS_URL (default 6380) — dedicated civic Redis, not other projects on 6379.
 */
import dotenv from "dotenv";
import express from "express";

dotenv.config();
import { Queue, Worker } from "bullmq";
import IORedis from "ioredis";

const REDIS_URL = process.env.REDIS_URL || "redis://127.0.0.1:6380";
const QUEUE_NAME = process.env.COMPLAINT_AI_QUEUE_NAME || "complaint-ai";
const PORT = Number(process.env.QUEUE_HTTP_PORT || 3030);
const BACKEND_URL = (process.env.BACKEND_URL || "http://127.0.0.1:8002").replace(/\/$/, "");
const INTERNAL_API_KEY = process.env.INTERNAL_API_KEY || "dev-internal-key";

const connection = new IORedis(REDIS_URL, { maxRetriesPerRequest: null });

const queue = new Queue(QUEUE_NAME, { connection });

const PROCESS_AI_TIMEOUT_MS = Number(process.env.PROCESS_AI_TIMEOUT_MS || 600000);

async function processComplaintJob(job) {
  const complaintId = job.data?.complaint_id;
  if (!complaintId) {
    throw new Error("Job missing complaint_id");
  }

  const res = await fetch(`${BACKEND_URL}/api/v1/internal/complaints/${complaintId}/process-ai`, {
    method: "POST",
    headers: {
      "X-Internal-Key": INTERNAL_API_KEY,
      "Content-Type": "application/json",
    },
    signal: AbortSignal.timeout(PROCESS_AI_TIMEOUT_MS),
  });

  const body = await res.text();
  if (!res.ok) {
    throw new Error(`Backend process-ai failed (${res.status}): ${body}`);
  }

  return body ? JSON.parse(body) : { ok: true };
}

const worker = new Worker(QUEUE_NAME, processComplaintJob, {
  connection,
  concurrency: Number(process.env.QUEUE_CONCURRENCY || 2),
  lockDuration: PROCESS_AI_TIMEOUT_MS + 30000,
  stalledInterval: 60000,
  maxStalledCount: 2,
});

worker.on("completed", (job) => {
  console.log(`[bullmq] completed ${job.id} complaint=${job.data?.complaint_id}`);
});

worker.on("failed", (job, err) => {
  console.error(`[bullmq] failed ${job?.id}:`, err?.message || err);
});

const app = express();
app.use(express.json());

app.get("/health", (_req, res) => {
  res.json({ status: "ok", queue: QUEUE_NAME });
});

/** Called by FastAPI when a citizen submits a complaint (status stays `submitted` until worker runs). */
app.post("/enqueue/complaint-ai", async (req, res) => {
  const complaintId = req.body?.complaint_id;
  if (!complaintId || typeof complaintId !== "string") {
    return res.status(400).json({ detail: "complaint_id required" });
  }

  const jobId = `complaint-${complaintId}`;
  const existing = await queue.getJob(jobId);
  if (existing) {
    const state = await existing.getState();
    if (state === "waiting" || state === "delayed" || state === "active") {
      return res.status(202).json({
        job_id: existing.id,
        complaint_id: complaintId,
        state,
        note: "already_queued",
      });
    }
    await existing.remove();
  }

  const job = await queue.add(
    "process",
    { complaint_id: complaintId },
    {
      jobId,
      removeOnComplete: 200,
      removeOnFail: 500,
      attempts: 5,
      backoff: { type: "exponential", delay: 3000 },
    }
  );

  res.status(202).json({ job_id: job.id, complaint_id: complaintId, state: "queued" });
});

const server = app.listen(PORT, () => {
  console.log(
    `Queue service listening on http://127.0.0.1:${PORT} (BullMQ: ${QUEUE_NAME}, Redis: ${REDIS_URL})`
  );
});

server.on("error", (err) => {
  if (err.code === "EADDRINUSE") {
    console.error(
      `Port ${PORT} is already in use — another queue instance is running. Use that one or stop it first.`
    );
    process.exit(1);
  }
  throw err;
});
