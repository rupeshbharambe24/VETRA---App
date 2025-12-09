// ---------- Types used in TraitExtraction ----------

export interface TraitResult {
  section: string;
  name: string;
  score: number;
  measurement_cm?: number | null;
  view?: string | null;
  details?: Record<string, any> | null;
}

export interface AnalyzeResponse {
  metadata: Record<string, string | null>;
  traits: TraitResult[];
  overlays?: {
    side?: string;
    back?: string;
    udder_bottom?: string;
  };
  html_report?: string;
}

export interface ProcessImageRequest {
  sideImageData: string;
  backImageData: string;
  udderBottomImageData: string;
  metadata?: Record<string, string | null>;
  backendUrl?: string;
  focalLengthMm?: number | null;
  objectDistanceM?: number | null;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  totalCount?: number;
  hasMore?: boolean;
}

// ---------- Types used in DataRecords ----------

export interface HistoricalRecord {
  id: string;
  date: string; // ISO string
  animalType: string;
  bodyLength: number;
  withersHeight: number;
  girth: number;
  confidence: number;
  notes?: string;
}

const DEFAULT_BACKEND_URL = "http://localhost:8000";

function dataUrlToFile(dataUrl: string, filename: string): File {
  const arr = dataUrl.split(",");
  const mimeMatch = arr[0]?.match(/:(.*?);/);
  const mime = mimeMatch ? mimeMatch[1] : "image/jpeg";
  const bstr = atob(arr[arr.length - 1]);
  let n = bstr.length;
  const u8arr = new Uint8Array(n);
  while (n--) {
    u8arr[n] = bstr.charCodeAt(n);
  }
  return new File([u8arr], filename, { type: mime });
}

export async function processImage(
  payload: ProcessImageRequest
): Promise<ApiResponse<AnalyzeResponse>> {
  const backend = payload.backendUrl || DEFAULT_BACKEND_URL;
  const form = new FormData();
  form.append("side_image", dataUrlToFile(payload.sideImageData, "side.jpg"));
  form.append("back_image", dataUrlToFile(payload.backImageData, "back.jpg"));
  form.append(
    "udder_bottom_image",
    dataUrlToFile(payload.udderBottomImageData, "udder_bottom.jpg")
  );
  if (payload.focalLengthMm !== undefined && payload.focalLengthMm !== null) {
    form.append("focal_length_mm", String(payload.focalLengthMm));
  }
  if (payload.objectDistanceM !== undefined && payload.objectDistanceM !== null) {
    form.append("object_distance_m", String(payload.objectDistanceM));
  }

  if (payload.metadata) {
    Object.entries(payload.metadata).forEach(([k, v]) => {
      if (v !== undefined && v !== null) form.append(k, v);
    });
  }

  const resp = await fetch(`${backend}/api/v1/analyze`, {
    method: "POST",
    body: form,
  });

  if (!resp.ok) {
    const msg = await resp.text();
    return { success: false, error: msg || resp.statusText };
  }

  const data = (await resp.json()) as AnalyzeResponse;
  return { success: true, data };
}

// History endpoint is still mocked for now
export async function getResults(
  limit: number = 50,
  offset: number = 0,
  search: string = ""
): Promise<ApiResponse<HistoricalRecord[]>> {
  const now = new Date();
  const records: HistoricalRecord[] = [];
  for (let i = 0; i < limit; i++) {
    const idx = offset + i;
    const d = new Date(now.getTime() - idx * 86400000);
    records.push({
      id: `rec-${idx}`,
      date: d.toISOString(),
      animalType: idx % 2 === 0 ? "cattle" : "buffalo",
      bodyLength: 135 + (idx % 10),
      withersHeight: 120 + (idx % 7),
      girth: 165 + (idx % 12),
      confidence: 80 + (idx % 15),
      notes: "Recorded locally",
    });
  }
  return { success: true, data: records, totalCount: 200, hasMore: offset + limit < 200 };
}
