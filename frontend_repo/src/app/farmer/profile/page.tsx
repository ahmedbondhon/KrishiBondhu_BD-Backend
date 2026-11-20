"use client";
import { FormEvent, useEffect, useRef, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Camera, CheckCircle2, Trash2, User as UserIcon } from "lucide-react";
import { EMPTY_GEO, GeoCascade, GeoValue } from "@/components/auth";
import { Button, PageHeader, Skeleton } from "@/components/ui";
import { deleteAvatar, getFarmerProfile, updateContactPrefs, updateFarmerProfile, uploadAvatar } from "@/lib/api";
import { toBn } from "@/lib/utils";
import { useApp, useL } from "@/store/app";

const COMM = [["sms", "এসএমএস", "SMS"], ["call", "ফোন কল", "Phone call"], ["in_app", "অ্যাপে", "In-app"]] as const;
const msg = (e: unknown, lang: string) => (e as { message_bn?: string; message?: string })?.[lang === "bn" ? "message_bn" : "message"] ?? "";

export default function ProfilePage() {
  const L = useL();
  const lang = useApp((s) => s.lang);
  const setLang = useApp((s) => s.setLang);
  const user = useApp((s) => s.user);
  const setUser = useApp((s) => s.setUser);
  const qc = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const { data, isLoading, isError } = useQuery({ queryKey: ["profile"], queryFn: getFarmerProfile });
  const [name, setName] = useState("");
  const [geo, setGeo] = useState<GeoValue>(EMPTY_GEO);
  const [pl, setPl] = useState<"bn" | "en">("bn");
  const [comm, setComm] = useState("sms");
  const [saved, setSaved] = useState(false);
  const [avatarErr, setAvatarErr] = useState("");

  useEffect(() => {
    if (!data) return;
    setName(data.full_name); setGeo(data.geo); setPl(data.preferred_language); setComm(data.preferred_communication ?? "sms");
  }, [data]);

  const save = useMutation({
    mutationFn: async () => {
      const p = await updateFarmerProfile({ full_name: name, preferred_language: pl, ...geo });
      await updateContactPrefs({ preferred_communication: comm, preferred_language: pl });
      return p;
    },
    onSuccess: (p) => {
      if (user) setUser({ ...user, name: p.full_name });
      setLang(pl);
      setSaved(true); setTimeout(() => setSaved(false), 3000);
      qc.invalidateQueries({ queryKey: ["profile"] });
    },
  });
  const upload = useMutation({
    mutationFn: (f: File) => uploadAvatar(f),
    onSuccess: (url) => { if (user) setUser({ ...user, avatar_url: url }); qc.invalidateQueries({ queryKey: ["profile"] }); },
    onError: (e) => setAvatarErr(msg(e, lang)),
  });
  const remove = useMutation({
    mutationFn: deleteAvatar,
    onSuccess: () => { if (user) setUser({ ...user, avatar_url: null }); qc.invalidateQueries({ queryKey: ["profile"] }); },
    onError: (e) => setAvatarErr(msg(e, lang)),
  });

  function pick(f?: File | null) {
    setAvatarErr("");
    if (!f) return;
    if (!["image/jpeg", "image/png", "image/webp"].includes(f.type)) return setAvatarErr(L("শুধু JPG, PNG বা WebP ছবি দেওয়া যাবে।", "Only JPG, PNG or WebP images are allowed."));
    if (f.size > 3 * 1024 * 1024) return setAvatarErr(L("ছবিটি ৩ MB-এর বেশি। ছোট ছবি দিন।", "Image is over 3 MB. Choose a smaller one."));
    upload.mutate(f);
  }
  const submit = (e: FormEvent) => { e.preventDefault(); save.mutate(); };
  const avatar = data?.avatar_url ?? user?.avatar_url;

  return (
    <div>
      <PageHeader title={L("আমার প্রোফাইল", "My profile")} sub={L("আপনার তথ্য ঠিক থাকলে পরামর্শ আপনার এলাকার সাথে মিলবে।", "Accurate details help us match advice to your area.")} />
      {isLoading ? <Skeleton className="!h-64 !rounded-card" /> : isError || !data ? <p role="alert" className="rounded-ctl bg-clay-50 px-4 py-3 text-clay-700">{L("প্রোফাইল আনা যায়নি। একটু পরে আবার চেষ্টা করুন।", "Could not load your profile. Try again shortly.")}</p> : (
        <div className="space-y-5">
          <section className="card flex flex-wrap items-center gap-5 p-5">
            <div className="relative h-24 w-24 shrink-0 overflow-hidden rounded-full bg-brand-50 ring-2 ring-brand-100">
              {avatar ? /* eslint-disable-next-line @next/next/no-img-element */ <img src={avatar} alt={L("প্রোফাইল ছবি", "Profile photo")} className="h-full w-full object-cover" /> : <span className="grid h-full w-full place-items-center text-brand-600"><UserIcon size={40} /></span>}
            </div>
            <div className="min-w-0 flex-1 space-y-2">
              <p className="font-display text-xl font-bold">{data.full_name}</p>
              <p className="text-ink-soft">{data.phone_number}</p>
              <div className="flex flex-wrap gap-2">
                <Button size="sm" variant="secondary" loading={upload.isPending} onClick={() => fileRef.current?.click()}><Camera size={16} />{avatar ? L("ছবি বদলান", "Change photo") : L("ছবি দিন", "Add photo")}</Button>
                {avatar && <Button size="sm" variant="ghost" loading={remove.isPending} onClick={() => remove.mutate()}><Trash2 size={16} />{L("ছবি মুছুন", "Remove")}</Button>}
              </div>
              {avatarErr && <p role="alert" className="text-[14px] text-clay-700">{avatarErr}</p>}
              <input ref={fileRef} type="file" accept="image/jpeg,image/png,image/webp" hidden onChange={(e) => { pick(e.target.files?.[0]); e.target.value = ""; }} />
            </div>
            {data.stats.length > 0 && (
              <div className="flex gap-3">
                {data.stats.map((s) => <div key={s.label_en} className="rounded-xl bg-canvas px-4 py-3 text-center"><p className="font-display text-2xl font-bold text-brand-700">{lang === "bn" ? toBn(s.value) : s.value}</p><p className="text-[13.5px] text-ink-mute">{L(s.label_bn, s.label_en)}</p></div>)}
              </div>
            )}
          </section>

          <form onSubmit={submit} className="card space-y-5 p-5">
            <div><label className="label" htmlFor="pn">{L("আপনার নাম", "Your name")}</label><input id="pn" className="field" value={name} onChange={(e) => setName(e.target.value)} required minLength={2} /></div>
            <div>
              <span className="label">{L("ঠিকানা", "Location")}</span>
              {(data.names.division || data.names.district) && <p className="mb-2 text-[14px] text-ink-mute">{L("বর্তমান: ", "Current: ")}{[data.names.union, data.names.upazila, data.names.district, data.names.division].filter(Boolean).join(", ")}</p>}
              <GeoCascade value={geo} onChange={setGeo} />
            </div>
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <span className="label">{L("ভাষা", "Language")}</span>
                <div className="grid grid-cols-2 gap-2">{([["bn", "বাংলা"], ["en", "English"]] as const).map(([v, t]) => <button key={v} type="button" aria-pressed={pl === v} onClick={() => setPl(v)} className={`min-h-[48px] rounded-ctl border-2 font-semibold ${pl === v ? "border-brand-600 bg-brand-50 text-brand-700" : "border-line-strong bg-white"}`}>{t}</button>)}</div>
              </div>
              <div>
                <span className="label">{L("যোগাযোগের মাধ্যম", "Preferred contact")}</span>
                <div className="grid grid-cols-3 gap-2">{COMM.map(([v, b, e]) => <button key={v} type="button" aria-pressed={comm === v} onClick={() => setComm(v)} className={`min-h-[48px] rounded-ctl border-2 font-semibold ${comm === v ? "border-brand-600 bg-brand-50 text-brand-700" : "border-line-strong bg-white"}`}>{L(b, e)}</button>)}</div>
              </div>
            </div>
            {save.isError && <p role="alert" className="rounded-ctl bg-clay-50 px-4 py-3 text-clay-700">{msg(save.error, lang) || L("সংরক্ষণ করা যায়নি।", "Could not save.")}</p>}
            {saved && <p role="status" className="flex items-center gap-2 rounded-ctl bg-brand-50 px-4 py-3 text-brand-800"><CheckCircle2 size={18} />{L("প্রোফাইল সংরক্ষিত হয়েছে।", "Profile saved.")}</p>}
            <Button type="submit" size="lg" loading={save.isPending}>{L("সংরক্ষণ করুন", "Save changes")}</Button>
          </form>
        </div>
      )}
    </div>
  );
}
