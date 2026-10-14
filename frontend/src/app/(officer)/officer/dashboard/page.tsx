import { redirect } from "next/navigation";

/** Officers only need the case queue — one screen. */
export default function OfficerDashboardRedirect() {
  redirect("/officer/complaints");
}
