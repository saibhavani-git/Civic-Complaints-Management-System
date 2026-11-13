"use client";

import { useParams } from "next/navigation";
import { PersonCaseView } from "@/components/admin/people/PersonCaseView";

export default function PersonCasesPage() {
  const params = useParams();
  const userId = String(params.id || "");
  return <PersonCaseView userId={userId} />;
}
