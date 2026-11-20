"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { ReactNode, useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { BookOpenCheck, Bell, Camera, ClipboardList, Home, Inbox, LayoutDashboard, LogOut, MoreHorizontal, Tractor, Users, type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { useApp, useL } from "@/store/app";
import { Avatar, LangToggle, Logo, OfflineBanner, Spinner } from "./ui";
import { listNotifications, logout as apiLogout, loadToken, me } from "@/lib/api";
import type { Role } from "@/types";

/** UI-only guard: redirects to /login when the stored session lacks an allowed role. The backend must still enforce RBAC. */
export function useRequireRole(roles: Role[]) {
  const user = useApp((s) => s.user);
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    loadToken();
    setMounted(true);
    if (process.env.NEXT_PUBLIC_USE_MOCK === "false" && loadToken()) me().catch(() => {});
  }, []);
  useEffect(() => {
    if (!mounted) return;
    // Read the store directly: during hydration the hook returns the server snapshot (no user yet).
    const u = useApp.getState().user;
    if (!u || !roles.includes(u.role)) router.replace("/login");
  }, [mounted, user]); // eslint-disable-line react-hooks/exhaustive-deps
  return mounted && user && roles.includes(user.role) ? user : null;
}

interface NavItem { href: string; icon: LucideIcon; bn: string; en: string; badge?: number }
type Kind = "farmer" | "expert" | "admin";

const NAV: Record<Kind, NavItem[]> = {
  farmer: [
    { href: "/farmer/dashboard", icon: Home, bn: "হোম", en: "Home" },
    { href: "/farmer/cases", icon: ClipboardList, bn: "পরীক্ষার ইতিহাস", en: "Check history" },
    { href: "/farmer/farms", icon: Tractor, bn: "আমার খামার", en: "My farm" },
    { href: "/farmer/notifications", icon: Bell, bn: "বিজ্ঞপ্তি", en: "Notifications" },
    { href: "/farmer/more", icon: MoreHorizontal, bn: "আরও", en: "More" },
  ],
  expert: [
    { href: "/expert/dashboard", icon: LayoutDashboard, bn: "ড্যাশবোর্ড", en: "Dashboard" },
    { href: "/expert/cases", icon: Inbox, bn: "কেস তালিকা", en: "Case queue" },
  ],
  admin: [
    { href: "/admin/dashboard", icon: LayoutDashboard, bn: "ড্যাশবোর্ড", en: "Dashboard" },
    { href: "/admin/knowledge-base", icon: BookOpenCheck, bn: "পরামর্শ ভান্ডার", en: "Advisory content" },
    { href: "/admin/users", icon: Users, bn: "ব্যবহারকারী", en: "Users" },
  ],
};
const PORTAL = { farmer: ["কৃষক পোর্টাল", "Farmer portal"], expert: ["বিশেষজ্ঞ পোর্টাল", "Expert portal"], admin: ["অ্যাডমিন পোর্টাল", "Admin portal"] } as const;
const ROLE_NAME: Record<Role, [string, string]> = { farmer: ["কৃষক", "Farmer"], agent: ["কৃষি সহায়ক", "Farm agent"], expert: ["বিশেষজ্ঞ", "Expert"], admin: ["অ্যাডমিন", "Admin"], administrator: ["অ্যাডমিন", "Admin"], technical_admin: ["টেক অ্যাডমিন", "Tech admin"], tech_admin: ["টেক অ্যাডমিন", "Tech admin"] };

export function AppShell({ kind, children }: { kind: Kind; children: ReactNode }) {
  const roles: Role[] = kind === "farmer" ? ["farmer", "agent"] : kind === "expert" ? ["expert"] : ["admin", "administrator", "technical_admin", "tech_admin"];
  const user = useRequireRole(roles);
  const pathname = usePathname();
  const router = useRouter();
  const L = useL();
  const setUser = useApp((s) => s.setUser);
  const { data: notes } = useQuery({ queryKey: ["notifications"], queryFn: listNotifications, enabled: !!user && kind === "farmer" });
  const unread = notes?.filter((n) => !n.read).length ?? 0;
  if (!user) return <Spinner />;

  const items = NAV[kind].map((i) => (i.href.endsWith("notifications") ? { ...i, badge: unread } : i));
  const active = (href: string) => pathname === href || pathname.startsWith(href + "/");
  const logout = async () => { await apiLogout(); setUser(null); router.push("/"); };
  const bottom = kind === "farmer" ? items.filter((i) => !i.href.endsWith("notifications")) : items;

  return (
    <div className="min-h-screen lg:grid lg:grid-cols-[264px_1fr]">
      {/* Sidebar (desktop) */}
      <aside className="rows-texture hidden bg-canopy text-white lg:sticky lg:top-0 lg:flex lg:h-screen lg:flex-col">
        <div className="px-5 pb-4 pt-6"><Link href={`/${kind}/dashboard`}><Logo light /></Link></div>
        {kind === "farmer" && (
          <div className="px-4 pb-3">
            <Link href="/farmer/diagnose" className="flex min-h-[48px] items-center justify-center gap-2 rounded-ctl bg-lime-400 font-semibold text-canopy shadow-[0_8px_20px_-8px_rgba(196,233,75,.6)] transition hover:bg-lime-300"><Camera size={20} />{L("নতুন পরীক্ষা", "New check")}</Link>
          </div>
        )}
        <nav className="flex-1 space-y-0.5 overflow-y-auto px-3 py-2" aria-label={L("প্রধান মেনু", "Main menu")}>
          <p className="px-3 pb-1.5 text-[13px] font-semibold text-brand-300/80">{L(PORTAL[kind][0], PORTAL[kind][1])}</p>
          {items.map((i) => {
            const I = i.icon;
            return (
              <Link key={i.href} href={i.href} aria-current={active(i.href) ? "page" : undefined} className={cn("group flex min-h-[44px] items-center gap-3 rounded-ctl px-3 font-semibold transition", active(i.href) ? "bg-white/12 text-white ring-1 ring-inset ring-white/10" : "text-brand-100/80 hover:bg-white/8 hover:text-white")}>
                <I size={20} className={active(i.href) ? "text-lime-400" : ""} />
                <span className="flex-1">{L(i.bn, i.en)}</span>
                {!!i.badge && <span className="grid h-5 min-w-5 place-items-center rounded-full bg-lime-400 px-1.5 text-[12px] font-bold text-canopy">{i.badge}</span>}
              </Link>
            );
          })}
        </nav>
        <div className="space-y-3 border-t border-white/10 p-4">
          <LangToggle dark />
          <div className="flex items-center gap-3 rounded-ctl bg-white/8 p-2.5">
            <Avatar name={user.name} dark />
            <div className="min-w-0 flex-1 leading-tight"><p className="truncate font-semibold">{user.name}</p><p className="text-[13px] text-brand-200">{L(ROLE_NAME[user.role][0], ROLE_NAME[user.role][1])}</p></div>
            <button onClick={logout} className="grid h-9 w-9 place-items-center rounded-lg text-brand-100 hover:bg-white/10" aria-label={L("লগআউট", "Log out")}><LogOut size={18} /></button>
          </div>
        </div>
      </aside>

      <div className="min-w-0 pb-24 lg:pb-0">
        <OfflineBanner />
        {/* Top bar (mobile + tablet) */}
        <header className="sticky top-0 z-30 flex items-center justify-between border-b border-line bg-white/85 px-4 py-2.5 backdrop-blur lg:hidden">
          <Link href={`/${kind}/dashboard`}><Logo size={32} /></Link>
          <div className="flex items-center gap-2">
            <LangToggle />
            {kind === "farmer" && (
              <Link href="/farmer/notifications" className="relative grid h-10 w-10 place-items-center rounded-full bg-white ring-1 ring-inset ring-line-strong" aria-label={L("বিজ্ঞপ্তি", "Notifications")}>
                <Bell size={20} />{unread > 0 && <span className="absolute -right-0.5 -top-0.5 grid h-5 min-w-5 place-items-center rounded-full bg-clay-500 px-1 text-[12px] font-bold text-white">{unread}</span>}
              </Link>
            )}
            <button onClick={logout} className="grid h-10 w-10 place-items-center rounded-full bg-white ring-1 ring-inset ring-line-strong" aria-label={L("লগআউট", "Log out")}><LogOut size={18} /></button>
          </div>
        </header>
        <main id="main" className="mx-auto w-full max-w-[1180px] animate-rise px-4 py-6 md:px-8 md:py-9">{children}</main>
      </div>

      {/* Bottom tabs (mobile) */}
      <nav className="fixed inset-x-0 bottom-0 z-40 border-t border-line bg-white lg:hidden" aria-label={L("প্রধান মেনু", "Main menu")}>
        <ul className={cn("mx-auto grid max-w-lg items-end px-2 pb-[max(env(safe-area-inset-bottom),6px)] pt-1.5", kind === "farmer" ? "grid-cols-5" : bottom.length === 2 ? "grid-cols-2" : "grid-cols-3")}>
          {kind === "farmer" ? (
            <>
              {[bottom[0], bottom[1]].map((i) => <Tab key={i.href} item={i} on={active(i.href)} />)}
              <li className="text-center"><Link href="/farmer/diagnose" aria-label={L("নতুন পরীক্ষা", "New check")} className="-mt-6 mx-auto grid h-14 w-14 place-items-center rounded-full bg-brand-600 text-white shadow-cta ring-4 ring-white"><Camera size={26} /></Link><span className="text-[12.5px] font-semibold text-ink-soft">{L("পরীক্ষা", "Check")}</span></li>
              {[bottom[2], bottom[3]].map((i) => <Tab key={i.href} item={i} on={active(i.href)} />)}
            </>
          ) : bottom.map((i) => <Tab key={i.href} item={i} on={active(i.href)} />)}
        </ul>
      </nav>
    </div>
  );
}

function Tab({ item, on }: { item: NavItem; on: boolean }) {
  const L = useL();
  const I = item.icon;
  return (
    <li className="text-center">
      <Link href={item.href} aria-current={on ? "page" : undefined} className={cn("flex flex-col items-center gap-0.5 py-1 text-[12.5px] font-semibold", on ? "text-brand-700" : "text-ink-mute")}>
        <span className={cn("grid h-8 w-14 place-items-center rounded-full transition", on && "bg-brand-100")}><I size={21} strokeWidth={on ? 2.5 : 2} /></span>
        {L(item.bn.replace("পরীক্ষার ", ""), item.en.replace("Check ", ""))}
      </Link>
    </li>
  );
}
