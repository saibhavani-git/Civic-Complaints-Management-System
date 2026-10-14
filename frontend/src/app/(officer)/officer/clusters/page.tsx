import { redirect } from "next/navigation";

/** Cluster planning is a department / system concern — not officer day-to-day. */
export default function OfficerClustersRedirect() {
  redirect("/officer/complaints");
}
