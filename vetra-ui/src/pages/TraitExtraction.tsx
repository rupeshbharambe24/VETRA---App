import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  AlertCircle,
  ArrowLeft,
  CheckCircle,
  Download,
  Image as ImageIcon,
  Loader2,
  RotateCcw,
  Camera,
  FileText,
} from "lucide-react";

import CaptureModal from "../components/CaptureModal";
import { processImage, AnalyzeResponse, TraitResult } from "@/lib/api";

type CaptureTarget = "side" | "back" | "udder";

const Card = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
  <div className={`rounded-xl border border-gray-300 bg-white shadow-sm ${className}`}>{children}</div>
);
const CardHeader = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
  <div className={`border-b px-5 py-3 ${className}`}>{children}</div>
);
const CardTitle = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
  <h2 className={`text-lg font-semibold ${className}`}>{children}</h2>
);
const CardContent = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
  <div className={`p-5 ${className}`}>{children}</div>
);

const Button = ({
  children,
  onClick,
  disabled,
  variant = "default",
  className = "",
}: {
  children: React.ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  variant?: "default" | "outline" | "danger";
  className?: string;
}) => {
  const base = "flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-medium transition";
  const variants: Record<string, string> = {
    default: "bg-blue-600 text-white hover:bg-blue-700",
    outline: "border border-gray-400 hover:bg-gray-100",
    danger: "bg-red-600 text-white hover:bg-red-700",
  };
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`${base} ${variants[variant]} ${className} ${disabled ? "opacity-50 cursor-not-allowed" : ""}`}
    >
      {children}
    </button>
  );
};

const Table = ({ children }: { children: React.ReactNode }) => (
  <table className="min-w-full border border-gray-300 text-sm">{children}</table>
);
const Th = ({ children }: { children: React.ReactNode }) => (
  <th className="border-b bg-gray-100 px-3 py-2 font-semibold text-left">{children}</th>
);
const Td = ({ children, className = "" }: { children: React.ReactNode; className?: string }) => (
  <td className={`border-b px-3 py-2 ${className}`}>{children}</td>
);

const TRAIT_ORDER = ["Strength", "Rump", "Feet and Leg", "Udder", "General"];

function groupTraits(traits: TraitResult[]): Record<string, TraitResult[]> {
  return traits.reduce<Record<string, TraitResult[]>>((acc, t) => {
    acc[t.section] = acc[t.section] || [];
    acc[t.section].push(t);
    return acc;
  }, {});
}

export default function TraitExtraction() {
  const [sideImage, setSideImage] = useState<string | null>(null);
  const [backImage, setBackImage] = useState<string | null>(null);
  const [udderBottomImage, setUdderBottomImage] = useState<string | null>(null);
  const [captureTarget, setCaptureTarget] = useState<CaptureTarget | null>(null);
  const [showCaptureModal, setShowCaptureModal] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [results, setResults] = useState<AnalyzeResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [focalLengthMm, setFocalLengthMm] = useState<string>("");
  const [distanceM, setDistanceM] = useState<string>("");

  const handleImageSelect = (imageData: string) => {
    if (captureTarget === "back") setBackImage(imageData);
    else if (captureTarget === "udder") setUdderBottomImage(imageData);
    else setSideImage(imageData);
    setCaptureTarget(null);
    setShowCaptureModal(false);
    setError(null);
  };

  const onUpload = (e: React.ChangeEvent<HTMLInputElement>, target: CaptureTarget) => {
    const file = e.target.files?.[0];
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      setError("Please select a valid image file.");
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      if (target === "back") setBackImage(reader.result as string);
      else if (target === "udder") setUdderBottomImage(reader.result as string);
      else setSideImage(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  const validateImages = () => {
    if (!sideImage || !backImage || !udderBottomImage) {
      setError("Please provide side, back, and udder bottom images.");
      return false;
    }
    return true;
  };

  const processImageAnalysis = async () => {
    if (!validateImages()) return;
    setIsProcessing(true);
    setError(null);
    try {
      const resp = await processImage({
        sideImageData: sideImage!,
        backImageData: backImage!,
        udderBottomImageData: udderBottomImage!,
        focalLengthMm: focalLengthMm ? Number(focalLengthMm) : null,
        objectDistanceM: distanceM ? Number(distanceM) : null,
      });
      if (!resp.success || !resp.data) throw new Error(resp.error || "Processing failed.");
      setResults(resp.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Processing error");
    } finally {
      setIsProcessing(false);
    }
  };

  const resetProcess = () => {
    setSideImage(null);
    setBackImage(null);
    setUdderBottomImage(null);
    setResults(null);
    setError(null);
  };

  const groupedTraits = useMemo(() => (results ? groupTraits(results.traits || []) : {}), [results]);

  const TraitTable = ({ section, traits }: { section: string; traits: TraitResult[] }) => (
    <Card>
      <CardHeader>
        <CardTitle>{section}</CardTitle>
      </CardHeader>
      <CardContent>
        <Table>
          <thead>
            <tr>
              <Th>Trait</Th>
              <Th>Score (1-9)</Th>
              <Th>Measurement</Th>
              <Th>View</Th>
            </tr>
          </thead>
          <tbody>
            {traits.map((t) => (
              <tr key={`${section}-${t.name}`}>
                <Td>{t.name}</Td>
                <Td className="font-semibold">{t.score}</Td>
                <Td>{t.measurement_cm ? `${t.measurement_cm.toFixed(1)} cm` : "-"}</Td>
                <Td className="capitalize">{t.view || "-"}</Td>
              </tr>
            ))}
          </tbody>
        </Table>
      </CardContent>
    </Card>
  );

  const OverlayPanel = ({ title, img }: { title: string; img?: string }) => (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {img ? (
          <img src={img} className="w-full rounded-lg border" alt={title} />
        ) : (
          <div className="w-full h-56 border border-dashed rounded-lg flex items-center justify-center text-gray-500">
            No overlay
          </div>
        )}
      </CardContent>
    </Card>
  );

  const openHtmlReport = () => {
    if (!results?.html_report) return;
    const win = window.open();
    if (win) {
      win.document.write(results.html_report);
      win.document.close();
    }
  };

  const ImageCard = ({
    title,
    description,
    image,
    onUploadHandler,
    onCaptureHandler,
  }: {
    title: string;
    description: string;
    image: string | null;
    onUploadHandler: (e: any) => void;
    onCaptureHandler: () => void;
  }) => (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {image ? (
          <img src={image} alt={title} className="w-full rounded-lg border max-h-64 object-cover" />
        ) : (
          <div className="w-full h-64 border border-dashed rounded-lg flex flex-col items-center justify-center text-gray-500">
            <ImageIcon className="w-8 h-8 mb-2" aria-hidden="true" />
            <p className="text-sm text-center">{description}</p>
          </div>
        )}

        <div className="flex gap-3 flex-wrap">
          <Button variant="outline" onClick={onCaptureHandler}>
            <Camera className="w-4 h-4" /> Capture
          </Button>

          <label className="inline-flex items-center px-4 py-2 border rounded-lg cursor-pointer bg-gray-100 hover:bg-gray-200 text-sm">
            <input type="file" className="hidden" accept="image/*" onChange={onUploadHandler} />
            Upload Image
          </label>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="flex items-center gap-3 p-4 border-b bg-white shadow-sm">
        <Link to="/" className="inline-block">
          <Button variant="outline">
            <ArrowLeft className="w-5 h-5" />
          </Button>
        </Link>
        <h1 className="text-xl font-bold">Trait Extraction</h1>
      </header>

      <div className="p-4 md:p-8 max-w-6xl mx-auto space-y-6">
        {!results && (
          <div className="grid md:grid-cols-3 gap-6">
            <ImageCard
              title="Side View Image"
              description="Capture or upload a clear side-view image."
              image={sideImage}
              onUploadHandler={(e) => onUpload(e, "side")}
              onCaptureHandler={() => {
                setCaptureTarget("side");
                setShowCaptureModal(true);
              }}
            />
            <ImageCard
              title="Back View Image"
              description="Capture or upload a clear back-view image."
              image={backImage}
              onUploadHandler={(e) => onUpload(e, "back")}
              onCaptureHandler={() => {
                setCaptureTarget("back");
                setShowCaptureModal(true);
              }}
            />
            <ImageCard
              title="Udder Bottom View"
              description="Capture or upload a clear udder bottom image."
              image={udderBottomImage}
              onUploadHandler={(e) => onUpload(e, "udder")}
              onCaptureHandler={() => {
                setCaptureTarget("udder");
                setShowCaptureModal(true);
              }}
            />
          </div>
        )}

        {!results && (
          <div className="space-y-4">
            {error && (
              <div className="flex items-center gap-2 bg-red-100 border border-red-300 text-red-700 px-4 py-3 rounded-lg">
                <AlertCircle className="w-4 h-4" />
                {error}
              </div>
            )}

            <Card>
              <CardHeader>
                <CardTitle>Optional Camera Inputs (for scaling fallback)</CardTitle>
              </CardHeader>
              <CardContent className="grid md:grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-sm font-medium text-gray-700">Focal Length (mm)</label>
                  <input
                    type="number"
                    value={focalLengthMm}
                    onChange={(e) => setFocalLengthMm(e.target.value)}
                    placeholder="e.g., 4.0"
                    className="w-full rounded-lg border px-3 py-2"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-sm font-medium text-gray-700">Distance to Animal (m)</label>
                  <input
                    type="number"
                    value={distanceM}
                    onChange={(e) => setDistanceM(e.target.value)}
                    placeholder="e.g., 2.5"
                    className="w-full rounded-lg border px-3 py-2"
                  />
                </div>
              </CardContent>
            </Card>

            <div className="flex flex-col sm:flex-row gap-3">
              <Button onClick={processImageAnalysis} disabled={isProcessing} className="flex-1">
                {isProcessing ? (
                  <>
                    <Loader2 className="animate-spin w-5 h-5" /> Processing...
                  </>
                ) : (
                  "Process Images"
                )}
              </Button>

              <Button variant="outline" onClick={resetProcess}>
                <RotateCcw className="w-4 h-4" />
                Reset
              </Button>
            </div>
          </div>
        )}

        {results && (
          <div className="space-y-6">
            <Card>
              <CardHeader className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-6 h-6 text-green-600" />
                  <CardTitle>Analysis Complete</CardTitle>
                </div>

                <div className="flex gap-3">
                  <Button variant="outline" onClick={openHtmlReport}>
                    <FileText className="w-4 h-4" /> Open Report
                  </Button>
                  <Button variant="outline" onClick={resetProcess}>
                    <RotateCcw className="w-4 h-4" /> New Analysis
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="grid md:grid-cols-3 gap-4">
                  <OverlayPanel title="Side Overlay" img={results.overlays?.side} />
                  <OverlayPanel title="Back Overlay" img={results.overlays?.back} />
                  <OverlayPanel title="Udder Bottom Overlay" img={results.overlays?.udder_bottom} />
                </div>
              </CardContent>
            </Card>

            <div className="space-y-4">
              {TRAIT_ORDER.filter((sec) => groupedTraits[sec]?.length).map((sec) => (
                <TraitTable key={sec} section={sec} traits={groupedTraits[sec]} />
              ))}
            </div>

            {results.html_report && (
              <div className="flex gap-3">
                <Button onClick={openHtmlReport} className="flex-1">
                  <Download className="w-5 h-5" /> Download / Print Report
                </Button>
              </div>
            )}
          </div>
        )}
      </div>

      <CaptureModal
        isOpen={showCaptureModal}
        onClose={() => setShowCaptureModal(false)}
        onImageSelect={handleImageSelect}
      />
    </div>
  );
}
