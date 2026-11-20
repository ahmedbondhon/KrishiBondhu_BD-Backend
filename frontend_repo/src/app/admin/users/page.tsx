"use client";
import { useMemo, useState } from "react";
import { Search, ShieldCheck } from "lucide-react";
import { Avatar, Badge, Button, PageHeader, Segmented } from "@/components/ui";
import { DEMO_USERS } from "@/lib/api";
import { useL } from "@/store/app";

type Role = "all" | "farmer" | "agent" | "expert";

export default function Users() {
  const L = useL();
  const [q, setQ] = useState("");
  const [role, setRole] = useState<Role>("all");
  const [verified, setVerified] = useState<Record<string, boolean>>({});
  const count = (r: Role) => DEMO_USERS.filter((u) => r === "all" || u.role === r).length;
  const rows = useMemo(() => DEMO_USERS.filter((u) => (role === "all" || u.role === role) && (!q || (u.name + u.phone).includes(q))), [q, role]);
  const roleName = { farmer: L("কৃষক", "Farmer"), agent: L("কৃষি সহায়ক", "Agent"), expert: L("বিশেষজ্ঞ", "Expert") } as const;
  const stat = (u: (typeof DEMO_USERS)[number]) => { const s = verified[u.phone] ? "verified" : u.status; return ({ active: ["সক্রিয়", "Active", "brand"], verified: ["যাচাইকৃত", "Verified", "sky"], pending: ["যাচাই বাকি", "Pending", "sun"] } as const)[s as "active"]; };
  return (
    <div>
      <PageHeader title={L("ব্যবহারকারী", "Users")} sub={L("বিশেষজ্ঞের পরিচয় যাচাই এখান থেকে করা হয়।", "Verify expert identities from here.")} />
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Segmented value={role} onChange={setRole} label={L("ভূমিকা", "Role")} options={[{ value: "all", label: `${L("সব", "All")} ${count("all")}` }, { value: "farmer", label: `${L("কৃষক", "Farmers")} ${count("farmer")}` }, { value: "agent", label: `${L("সহায়ক", "Agents")} ${count("agent")}` }, { value: "expert", label: `${L("বিশেষজ্ঞ", "Experts")} ${count("expert")}` }]} />
        <div className="relative min-w-[200px] flex-1 sm:max-w-xs"><Search className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-mute" size={17} /><input className="field !min-h-[42px] pl-9" placeholder={L("নাম বা ফোন নম্বর", "Name or phone")} value={q} onChange={(e) => setQ(e.target.value)} aria-label={L("খুঁজুন", "Search")} /></div>
      </div>
      <div className="card overflow-x-auto scrollbar-thin">
        <table className="w-full min-w-[620px]">
          <thead className="border-b border-line bg-canvas"><tr>{[L("নাম", "Name"), L("ফোন", "Phone"), L("ভূমিকা", "Role"), L("অবস্থা", "Status"), ""].map((h, i) => <th key={i} className="th">{h}</th>)}</tr></thead>
          <tbody className="divide-y divide-line">{rows.map((u) => { const s = stat(u); const pending = u.status === "pending" && !verified[u.phone]; return (
            <tr key={u.phone} className="transition hover:bg-canvas">
              <td className="td"><span className="flex items-center gap-3"><Avatar name={u.name} size={34} /><span className="font-semibold">{u.name}</span></span></td>
              <td className="td tabular-nums text-ink-soft">{u.phone}</td><td className="td">{roleName[u.role]}</td>
              <td className="td"><Badge tone={s[2]}>{L(s[0], s[1])}</Badge></td>
              <td className="td text-right">{pending && <Button size="sm" variant="soft" onClick={() => setVerified({ ...verified, [u.phone]: true })}><ShieldCheck size={16} />{L("যাচাই করুন", "Verify")}</Button>}</td>
            </tr>); })}
            {rows.length === 0 && <tr><td colSpan={5} className="td py-10 text-center text-ink-mute">{L("কাউকে পাওয়া যায়নি।", "No users found.")}</td></tr>}</tbody>
        </table>
      </div>
    </div>
  );
}
