import { redirect } from "next/navigation";

/** AI research dataset removed from product UI — use admin complaints instead. */
export default function ClassificationDatasetPage() {
  redirect("/admin/dashboard");
}
