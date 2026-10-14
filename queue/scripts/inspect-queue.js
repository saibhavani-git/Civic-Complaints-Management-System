/**
 * List BullMQ jobs for complaint AI routing (waiting, active, delayed, failed).
 *
 * Usage (from queue/):
 *   npm run inspect
 *   npm run inspect -- --failed
 */
import dotenv from "dotenv";
import path from "path";
import { fileURLToPath } from "url";
import { Queue } from "bullmq";
import IORedis from "ioredis";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
dotenv.config({ path: path.join(__dirname, "..", ".env") });

const REDIS_URL = process.env.REDIS_URL || "redis://127.0.0.1:6380";
const QUEUE_NAME = process.env.COMPLAINT_AI_QUEUE_NAME || "complaint-ai";

const onlyFailed = process.argv.includes("--failed");
const states = onlyFailed
  ? ["failed"]
  : ["active", "waiting", "delayed", "failed", "completed"];

function fmtJob(job) {
  const cid = job.data?.complaint_id ?? "?";
  const attempts = `${job.attemptsMade}/${job.opts?.attempts ?? "?"}`;
  return `  job=${job.id}  complaint_id=${cid}  attempts=${attempts}  ${job.timestamp ? `enqueued=${new Date(job.timestamp).toISOString()}` : ""}`;
}

const connection = new IORedis(REDIS_URL, { maxRetriesPerRequest: null });
const queue = new Queue(QUEUE_NAME, { connection });

try {
  const counts = await queue.getJobCounts(...states);
  console.log(`Queue: ${QUEUE_NAME}  Redis: ${REDIS_URL}\n`);
  console.log("Counts:", counts);
  console.log("");

  for (const state of states) {
    const jobs = await queue.getJobs([state], 0, 50, true);
    if (!jobs.length) continue;
    console.log(`--- ${state.toUpperCase()} (up to 50) ---`);
    for (const job of jobs) {
      console.log(fmtJob(job));
      if (state === "failed" && job.failedReason) {
        console.log(`       error: ${job.failedReason.slice(0, 200)}`);
      }
    }
    console.log("");
  }

  console.log(
    "Tip: complaint_id is MongoDB _id. Match in DB or API with status submitted / ai_processing."
  );
} finally {
  await queue.close();
  connection.disconnect();
}
