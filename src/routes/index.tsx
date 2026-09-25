import { createFileRoute } from "@tanstack/react-router";
import { AcsShell } from "@/components/acs/shell";

export const Route = createFileRoute("/")({ component: Home });

function Home() {
  return <AcsShell />;
}
