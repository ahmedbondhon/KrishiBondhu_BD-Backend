"use client";
import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell, CheckCheck, ChevronRight } from "lucide-react";
import { Button, EmptyState, PageHeader, Skeleton } from "@/components/ui";
import { listNotifications, markAllRead } from "@/lib/api";
import { cn, timeAgo } from "@/lib/utils";
import { useApp, useL } from "@/store/app";

export default function Notifications() {
  const L = useL();
  const lang = useApp((s) => s.lang);
  const qc = useQueryClient();
  const { data, isLoading } = useQuery({ queryKey: ["notifications"], queryFn: listNotifications });
  const readAll = useMutation({ mutationFn: markAllRead, onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }) });
  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader title={L("বিজ্ঞপ্তি", "Notifications")} actions={data?.some((n) => !n.read) ? <Button variant="secondary" size="sm" onClick={() => readAll.mutate()}><CheckCheck size={17} />{L("সব পড়া হয়েছে", "Mark all read")}</Button> : undefined} />
      {isLoading ? <div className="space-y-3">{[0, 1].map((i) => <Skeleton key={i} className="!h-20 !rounded-card" />)}</div> : !data?.length ? <EmptyState icon={<Bell size={28} />} title={L("কোনো বিজ্ঞপ্তি নেই", "No notifications")} body={L("বিশেষজ্ঞের উত্তর এলে এখানে জানানো হবে।", "Expert replies will show up here.")} /> : (
        <ul className="space-y-3">{data.map((n) => {
          const inner = (<><span className={cn("mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full", n.read ? "bg-transparent" : "bg-sky-500")} aria-label={n.read ? undefined : L("নতুন", "New")} /><span className="min-w-0 flex-1"><span className="block font-display font-bold">{n.title_bn}</span><span className="block text-ink-soft">{n.body_bn}</span><span className="mt-1 block text-[13px] text-ink-mute">{timeAgo(n.created_at, lang)}</span></span>{n.case_id && <ChevronRight className="mt-1 shrink-0 text-ink-mute" />}</>);
          const cls = cn("card flex items-start gap-3 p-4", !n.read && "ring-1 ring-sky-100");
          return <li key={n.id}>{n.case_id ? <Link href={`/farmer/cases/${n.case_id}`} className={cn(cls, "transition hover:shadow-pop")}>{inner}</Link> : <div className={cls}>{inner}</div>}</li>;
        })}</ul>
      )}
    </div>
  );
}
