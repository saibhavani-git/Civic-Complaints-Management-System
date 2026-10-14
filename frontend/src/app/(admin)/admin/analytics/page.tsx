import { redirect } from "next/navigation";

/** Analytics merged into admin Overview — avoid duplicate menu. */
export default function AdminAnalyticsRedirect() {
  redirect("/admin/dashboard");
}
