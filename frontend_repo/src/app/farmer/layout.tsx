import { AppShell } from "@/components/shells";
export default function Layout({ children }: { children: React.ReactNode }) {
  return <AppShell kind="farmer">{children}</AppShell>;
}
