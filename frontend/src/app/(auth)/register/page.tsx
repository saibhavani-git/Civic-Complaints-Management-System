import { redirect } from "next/navigation";

/** Legacy URL — sign-in is for new resident accounts. */
export default function RegisterRedirectPage() {
  redirect("/sign-in");
}
