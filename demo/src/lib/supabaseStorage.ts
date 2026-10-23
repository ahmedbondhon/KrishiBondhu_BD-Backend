// Supabase Cloud Storage helper for Krishibondhu BD
export const SUPABASE_URL = "https://damfsrzakxxccalogghh.supabase.co";
export const SUPABASE_KEY =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRhbWZzcnpha3h4Y2NhbG9nZ2hoIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc5MTk3OTE1MywiZXhwIjoyMTA3NTU1MTUzfQ.1t8QxaKh9GfFjdcz3vRvY-FbYK8Af9b-xDa8t8fSDi8";
export const BUCKET_NAME = "krishibondhu-uploads";

/**
 * Upload a File or Blob directly to a specific folder in Supabase Storage.
 * Folders:
 *  - "avatars" -> User avatar profile images
 *  - "crops"   -> Crop diagnosis / specimen photos
 */
export async function uploadToSupabaseStorage(
  folder: "avatars" | "crops",
  file: File | Blob,
  fileName?: string
): Promise<{ publicUrl: string; path: string }> {
  const ext = file.type === "image/png" ? "png" : file.type === "image/webp" ? "webp" : "jpg";
  const uniqueName = fileName || `${Date.now()}_${Math.random().toString(36).substring(2, 9)}.${ext}`;
  const path = `${folder}/${uniqueName}`;

  const uploadEndpoint = `${SUPABASE_URL}/storage/v1/object/${BUCKET_NAME}/${path}`;

  const response = await fetch(uploadEndpoint, {
    method: "POST",
    headers: {
      apikey: SUPABASE_KEY,
      Authorization: `Bearer ${SUPABASE_KEY}`,
      "Content-Type": file.type || "image/jpeg",
      "x-upsert": "true",
    },
    body: file,
  });

  if (!response.ok) {
    const errText = await response.text();
    throw new Error(`Failed to upload to Supabase Storage [${folder}]: ${errText}`);
  }

  const publicUrl = `${SUPABASE_URL}/storage/v1/object/public/${BUCKET_NAME}/${path}`;
  return { publicUrl, path };
}

/**
 * Convert base64 data URL to Blob
 */
export function dataURLtoBlob(dataurl: string): Blob {
  const arr = dataurl.split(",");
  const mime = arr[0].match(/:(.*?);/)?.[1] || "image/jpeg";
  const bstr = atob(arr[1]);
  let n = bstr.length;
  const u8arr = new Uint8Array(n);
  while (n--) {
    u8arr[n] = bstr.charCodeAt(n);
  }
  return new Blob([u8arr], { type: mime });
}
