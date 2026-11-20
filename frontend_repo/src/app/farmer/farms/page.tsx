"use client";
import { FormEvent, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, MapPin, Plus, Ruler, Sprout, Tractor, Trash2 } from "lucide-react";
import { Badge, Button, EmptyState, PageHeader, Skeleton } from "@/components/ui";
import { addCropCycle, addFarm, deleteFarm, listCrops, listFarms, listGrowthStages, listVarieties, updateCropCycle } from "@/lib/api";
import { fmtDate, toBn } from "@/lib/utils";
import { useApp, useL } from "@/store/app";
import type { Farm, FarmCrop } from "@/types";

const SOIL = [["loam", "দোআঁশ", "Loam"], ["clay", "এঁটেল", "Clay"], ["sandy", "বেলে", "Sandy"], ["sandy_loam", "বেলে-দোআঁশ", "Sandy loam"]] as const;
const WATER = [["tubewell", "নলকূপ", "Tube well"], ["canal", "খাল / নদী", "Canal / river"], ["pond", "পুকুর", "Pond"], ["rainfed", "বৃষ্টির পানি", "Rain-fed"]] as const;
const today = () => new Date().toISOString().slice(0, 10);

function CropCycleRow({ farm, cy }: { farm: Farm; cy: FarmCrop }) {
  const L = useL();
  const lang = useApp((s) => s.lang);
  const qc = useQueryClient();
  const [harvest, setHarvest] = useState(false);
  const [kg, setKg] = useState("");
  const { data: stages } = useQuery({ queryKey: ["stages", cy.crop.id], queryFn: () => listGrowthStages(cy.crop.id), staleTime: 3_600_000 });
  const done = cy.status === "harvested" || cy.status === "failed";
  const refresh = () => qc.invalidateQueries({ queryKey: ["farms"] });
  const move = useMutation({ mutationFn: (id: string) => { const st = stages?.find((x) => x.id === id); return updateCropCycle(farm.id, cy.cycle_id!, { stage_id: id, stage: st?.name_bn }); }, onSuccess: refresh });
  const finish = useMutation({ mutationFn: (status: "harvested" | "failed") => updateCropCycle(farm.id, cy.cycle_id!, { status, yield_kg: kg ? Number(kg) : undefined, actual_harvest: today() }), onSuccess: () => { setHarvest(false); refresh(); } });

  return (
    <div className="rounded-xl bg-canvas p-3.5">
      <div className="flex items-center gap-3">
        <span className="text-3xl">{cy.crop.emoji}</span>
        <div className="min-w-0 flex-1 leading-tight">
          <p className="font-display font-bold">{L(cy.crop.name_bn, cy.crop.name_en)}{cy.variety ? ` · ${cy.variety}` : ""}</p>
          <p className="text-[13.5px] text-ink-mute">
            {L("রোপণ ", "Planted ")}{cy.planted_at ? fmtDate(cy.planted_at, lang) : "—"}
            {cy.expected_harvest ? ` · ${L("তোলা ", "Harvest ")}${fmtDate(cy.expected_harvest, lang)}` : ""}
          </p>
        </div>
        {done ? <Badge tone={cy.status === "harvested" ? "brand" : "clay"}>{cy.status === "harvested" ? L("ফসল তোলা হয়েছে", "Harvested") : L("ব্যর্থ", "Failed")}</Badge> : cy.stage ? <Badge tone="brand">{cy.stage}</Badge> : null}
      </div>
      {done && cy.yield_kg != null && <p className="mt-2 text-ink-soft">{L("ফলন: ", "Yield: ")}<strong>{lang === "bn" ? toBn(cy.yield_kg) : cy.yield_kg}</strong> {L("কেজি", "kg")}</p>}
      {!done && cy.cycle_id && (
        <div className="mt-3 flex flex-wrap items-center gap-2">
          {stages && stages.length > 0 && (
            <select aria-label={L("পর্যায় বদলান", "Change stage")} className="field !min-h-[44px] !w-auto" value={cy.stage_id ?? ""} onChange={(e) => e.target.value && move.mutate(e.target.value)}>
              <option value="">{L("পর্যায় বদলান", "Change stage")}</option>
              {stages.map((s) => <option key={s.id} value={s.id}>{L(s.name_bn, s.name_en)}</option>)}
            </select>
          )}
          {!harvest ? <Button size="sm" variant="secondary" onClick={() => setHarvest(true)}><CheckCircle2 size={16} />{L("ফসল তোলা হয়েছে", "Mark harvested")}</Button> : (
            <>
              <input aria-label={L("ফলন (কেজি)", "Yield (kg)")} type="number" min={0} className="field !min-h-[44px] !w-32" placeholder={L("ফলন (কেজি)", "Yield (kg)")} value={kg} onChange={(e) => setKg(e.target.value)} />
              <Button size="sm" loading={finish.isPending} onClick={() => finish.mutate("harvested")}>{L("সংরক্ষণ", "Save")}</Button>
              <Button size="sm" variant="ghost" onClick={() => finish.mutate("failed")}>{L("ফসল নষ্ট", "Crop failed")}</Button>
              <Button size="sm" variant="ghost" onClick={() => setHarvest(false)}>{L("বাতিল", "Cancel")}</Button>
            </>
          )}
        </div>
      )}
    </div>
  );
}

export default function Farms() {
  const L = useL();
  const lang = useApp((s) => s.lang);
  const qc = useQueryClient();
  const { data, isLoading, isError } = useQuery({ queryKey: ["farms"], queryFn: listFarms });
  const { data: crops } = useQuery({ queryKey: ["crops"], queryFn: listCrops, staleTime: 3_600_000 });
  const [open, setOpen] = useState(false);
  const [cropFor, setCropFor] = useState<string | null>(null);
  const [f, setF] = useState({ name: "", size_decimal: 30, soil_type: "loam", irrigation_source: "tubewell" });
  const [c, setC] = useState({ crop_id: "", stage_id: "", variety_id: "", planted_at: today(), expected_harvest: "" });
  const cropId = c.crop_id || crops?.[0]?.id || "";
  const { data: stages } = useQuery({ queryKey: ["stages", cropId], queryFn: () => listGrowthStages(cropId), enabled: !!cropId, staleTime: 3_600_000 });
  const { data: varieties } = useQuery({ queryKey: ["varieties", cropId], queryFn: () => listVarieties(cropId), enabled: !!cropId, staleTime: 3_600_000 });
  const stageId = c.stage_id || stages?.[0]?.id || "";

  const label = (v: string, list: readonly (readonly [string, string, string])[]) => { const m = list.find((x) => x[0] === v); return m ? L(m[1], m[2]) : v; };
  const refresh = () => qc.invalidateQueries({ queryKey: ["farms"] });
  const addF = useMutation({ mutationFn: () => addFarm(f), onSuccess: () => { refresh(); setOpen(false); setF({ name: "", size_decimal: 30, soil_type: "loam", irrigation_source: "tubewell" }); } });
  const delF = useMutation({ mutationFn: (id: string) => deleteFarm(id), onSuccess: refresh });
  const addC = useMutation({
    mutationFn: (farmId: string) => {
      const crop = crops!.find((x) => x.id === cropId)!;
      const st = stages?.find((x) => x.id === stageId);
      const v = varieties?.find((x) => x.id === c.variety_id);
      return addCropCycle(farmId, { crop, stage: st?.name_bn ?? "", stage_id: st?.id, planted_at: c.planted_at, variety: v?.name_bn, variety_id: v?.id, expected_harvest: c.expected_harvest || undefined });
    },
    onSuccess: () => { refresh(); setCropFor(null); },
  });
  const submitF = (e: FormEvent) => { e.preventDefault(); addF.mutate(); };
  const errMsg = (e: unknown) => (e as { message_bn?: string; message?: string })?.[lang === "bn" ? "message_bn" : "message"] ?? "";

  return (
    <div>
      <PageHeader title={L("আমার খামার", "My farm")} sub={L("ফসলের তথ্য দিলে পরামর্শ আপনার ক্ষেতের সাথে আরও মিলবে।", "Adding crop details makes advice fit your field better.")} actions={<Button onClick={() => setOpen(!open)}><Plus size={19} />{L("নতুন খামার", "Add farm")}</Button>} />

      {open && (
        <form onSubmit={submitF} className="card mb-5 space-y-4 p-5">
          <div><label className="label" htmlFor="fn">{L("খামারের নাম", "Farm name")}</label><input id="fn" className="field" value={f.name} onChange={(e) => setF({ ...f, name: e.target.value })} required /></div>
          <div className="grid gap-4 sm:grid-cols-3">
            <div><label className="label" htmlFor="fs">{L("আয়তন (শতাংশ)", "Size (decimals)")}</label><input id="fs" type="number" min={1} className="field" value={f.size_decimal} onChange={(e) => setF({ ...f, size_decimal: Number(e.target.value) })} /></div>
            <div><label className="label" htmlFor="fso">{L("মাটির ধরন", "Soil type")}</label><select id="fso" className="field" value={f.soil_type} onChange={(e) => setF({ ...f, soil_type: e.target.value })}>{SOIL.map((x) => <option key={x[0]} value={x[0]}>{L(x[1], x[2])}</option>)}</select></div>
            <div><label className="label" htmlFor="fw">{L("সেচের উৎস", "Irrigation")}</label><select id="fw" className="field" value={f.irrigation_source} onChange={(e) => setF({ ...f, irrigation_source: e.target.value })}>{WATER.map((x) => <option key={x[0]} value={x[0]}>{L(x[1], x[2])}</option>)}</select></div>
          </div>
          {addF.isError && <p role="alert" className="rounded-ctl bg-clay-50 px-4 py-3 text-clay-700">{errMsg(addF.error)}</p>}
          <div className="flex gap-2"><Button type="submit" loading={addF.isPending}>{L("খামার সংরক্ষণ করুন", "Save farm")}</Button><Button type="button" variant="ghost" onClick={() => setOpen(false)}>{L("বাতিল", "Cancel")}</Button></div>
        </form>
      )}

      {isLoading ? <Skeleton className="!h-48 !rounded-card" /> : isError ? <p role="alert" className="rounded-ctl bg-clay-50 px-4 py-3 text-clay-700">{L("খামারের তালিকা আনা যায়নি। একটু পরে আবার চেষ্টা করুন।", "Could not load your farms. Try again shortly.")}</p> : !data?.length ? <EmptyState icon={<Tractor size={28} />} title={L("এখনো কোনো খামার নেই", "No farm yet")} body={L("খামার যোগ করলে ফসলের পর্যায় অনুযায়ী পরামর্শ পাবেন।", "Add a farm to get advice matched to your crop stage.")} action={<Button onClick={() => setOpen(true)}><Plus size={19} />{L("খামার যোগ করুন", "Add a farm")}</Button>} /> : (
        <div className="grid gap-5 lg:grid-cols-2">
          {data.map((farm) => (
            <section key={farm.id} className="card overflow-hidden">
              <div className="rows-texture bg-canopy p-5 text-white">
                <div className="flex items-start justify-between gap-3">
                  <h2 className="text-2xl">{farm.name}</h2>
                  <button aria-label={L("খামার মুছুন", "Delete farm")} onClick={() => { if (window.confirm(L("এই খামারটি মুছে ফেলবেন?", "Delete this farm?"))) delF.mutate(farm.id); }} className="grid h-10 w-10 shrink-0 place-items-center rounded-lg text-brand-100 hover:bg-white/10"><Trash2 size={18} /></button>
                </div>
                <p className="mt-1 flex flex-wrap gap-x-5 gap-y-1 text-brand-100">
                  {(farm.soil_type || farm.irrigation_source) && <span className="inline-flex items-center gap-1.5"><MapPin size={16} />{[farm.soil_type && label(farm.soil_type, SOIL), farm.irrigation_source && label(farm.irrigation_source, WATER)].filter(Boolean).join(" · ") || farm.location}</span>}
                  <span className="inline-flex items-center gap-1.5"><Ruler size={16} />{lang === "bn" ? toBn(farm.size_decimal) : farm.size_decimal} {L("শতাংশ", "decimals")}</span>
                </p>
              </div>
              <div className="space-y-2.5 p-5">
                {farm.crops.length === 0 && <p className="text-ink-soft">{L("এখনো কোনো ফসল যোগ করা হয়নি।", "No crops added yet.")}</p>}
                {farm.crops.map((cy, i) => <CropCycleRow key={cy.cycle_id ?? i} farm={farm} cy={cy} />)}
                {cropFor === farm.id ? (
                  <div className="grid gap-3 rounded-xl border border-line-strong p-4 sm:grid-cols-2">
                    <select aria-label={L("ফসল", "Crop")} className="field" value={cropId} onChange={(e) => setC({ ...c, crop_id: e.target.value, stage_id: "", variety_id: "" })}>{(crops ?? []).map((x) => <option key={x.id} value={x.id}>{L(x.name_bn, x.name_en)}</option>)}</select>
                    <select aria-label={L("পর্যায়", "Stage")} className="field" value={stageId} onChange={(e) => setC({ ...c, stage_id: e.target.value })}>{(stages ?? []).map((x) => <option key={x.id} value={x.id}>{L(x.name_bn, x.name_en)}</option>)}</select>
                    {!!varieties?.length && <select aria-label={L("জাত", "Variety")} className="field sm:col-span-2" value={c.variety_id} onChange={(e) => setC({ ...c, variety_id: e.target.value })}><option value="">{L("জাত (ঐচ্ছিক)", "Variety (optional)")}</option>{varieties.map((x) => <option key={x.id} value={x.id}>{L(x.name_bn, x.name_en)}</option>)}</select>}
                    <div><label className="label" htmlFor="pd">{L("রোপণের তারিখ", "Planting date")}</label><input id="pd" type="date" className="field" value={c.planted_at} onChange={(e) => setC({ ...c, planted_at: e.target.value })} /></div>
                    <div><label className="label" htmlFor="hd">{L("প্রত্যাশিত ফসল তোলা", "Expected harvest")}</label><input id="hd" type="date" className="field" value={c.expected_harvest} onChange={(e) => setC({ ...c, expected_harvest: e.target.value })} /></div>
                    {addC.isError && <p role="alert" className="rounded-ctl bg-clay-50 px-4 py-3 text-clay-700 sm:col-span-2">{errMsg(addC.error)}</p>}
                    <Button className="sm:col-span-2" loading={addC.isPending} disabled={!crops?.length} onClick={() => addC.mutate(farm.id)}>{L("ফসল যোগ করুন", "Add crop")}</Button>
                  </div>
                ) : <Button variant="soft" onClick={() => setCropFor(farm.id)}><Sprout size={18} />{L("ফসল যোগ করুন", "Add a crop")}</Button>}
              </div>
            </section>
          ))}
        </div>
      )}
    </div>
  );
}
