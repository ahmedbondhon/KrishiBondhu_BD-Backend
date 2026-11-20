/** Client-side image helpers: compression and a quick blur / brightness check (FR-22, FR-23, NFR-15). */

export const MAX_BYTES = 5 * 1024 * 1024;
export const ALLOWED = ["image/jpeg", "image/png", "image/webp"];

export interface QualityResult {
  status: "acceptable" | "blurry" | "dark" | "bright";
  blur: number;
  brightness: number;
}

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((res, rej) => {
    const img = new Image();
    img.onload = () => res(img);
    img.onerror = rej;
    img.src = src;
  });
}

export async function compressImage(file: File, maxSide = 1280, quality = 0.82): Promise<{ blob: Blob; dataUrl: string }> {
  const url = URL.createObjectURL(file);
  try {
    const img = await loadImage(url);
    const scale = Math.min(1, maxSide / Math.max(img.width, img.height));
    const c = document.createElement("canvas");
    c.width = Math.round(img.width * scale);
    c.height = Math.round(img.height * scale);
    c.getContext("2d")!.drawImage(img, 0, 0, c.width, c.height);
    const blob: Blob = await new Promise((r) => c.toBlob((b) => r(b!), "image/jpeg", quality));
    const dataUrl = c.toDataURL("image/jpeg", 0.7);
    return { blob, dataUrl };
  } finally {
    URL.revokeObjectURL(url);
  }
}

/** Variance of a Laplacian over a small grayscale copy — low variance means blurry. */
export async function assessQuality(dataUrl: string): Promise<QualityResult> {
  const img = await loadImage(dataUrl);
  const w = 160;
  const h = Math.max(1, Math.round((img.height / img.width) * w));
  const c = document.createElement("canvas");
  c.width = w;
  c.height = h;
  const ctx = c.getContext("2d")!;
  ctx.drawImage(img, 0, 0, w, h);
  const { data } = ctx.getImageData(0, 0, w, h);
  const g = new Float32Array(w * h);
  let sum = 0;
  for (let i = 0; i < w * h; i++) {
    g[i] = 0.299 * data[i * 4] + 0.587 * data[i * 4 + 1] + 0.114 * data[i * 4 + 2];
    sum += g[i];
  }
  const brightness = sum / (w * h);
  let acc = 0, acc2 = 0, n = 0;
  for (let y = 1; y < h - 1; y++)
    for (let x = 1; x < w - 1; x++) {
      const i = y * w + x;
      const lap = 4 * g[i] - g[i - 1] - g[i + 1] - g[i - w] - g[i + w];
      acc += lap;
      acc2 += lap * lap;
      n++;
    }
  const blur = acc2 / n - (acc / n) ** 2;
  let status: QualityResult["status"] = "acceptable";
  if (brightness < 45) status = "dark";
  else if (brightness > 225) status = "bright";
  else if (blur < 28) status = "blurry";
  return { status, blur, brightness };
}
