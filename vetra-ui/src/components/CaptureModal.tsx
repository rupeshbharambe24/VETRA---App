import { useRef } from "react";
import { Camera, Upload, X } from "lucide-react";

interface CaptureModalProps {
  isOpen: boolean;
  onClose: () => void;
  onImageSelect: (imageData: string) => void;
}

export default function CaptureModal({
  isOpen,
  onClose,
  onImageSelect,
}: CaptureModalProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const cameraInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null; // Modal stays unmounted unless open

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith("image/")) {
      alert("Please select a valid image file");
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      alert("Image must be smaller than 10MB");
      return;
    }

    const reader = new FileReader();
    reader.onload = (ev) => {
      const data = ev.target?.result as string;
      onImageSelect(data);
      onClose();
    };
    reader.readAsDataURL(file);
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50">
      {/* Modal */}
      <div className="bg-white w-full max-w-sm rounded-2xl shadow-xl p-6 relative">
        {/* Close button */}
        <button
          onClick={onClose}
          title="Close modal"
          className="absolute top-3 right-3 p-2 rounded-full hover:bg-gray-100 transition"
        >
          <X className="w-5 h-5 text-gray-600" />
        </button>

        {/* Header */}
        <h2 className="text-xl font-bold mb-2">Select Image</h2>
        <p className="text-gray-600 text-sm mb-4">
          Capture or upload a clear image of the livestock for accurate analysis.
        </p>

        <div className="text-center my-6">
          <Camera className="w-14 h-14 mx-auto text-blue-600 mb-3" />
        </div>

        {/* Buttons */}
        <div className="space-y-3">
          {/* Capture Photo */}
          <button
            onClick={() => cameraInputRef.current?.click()}
            className="w-full flex items-center gap-3 bg-blue-600 text-white py-3 px-4 rounded-xl hover:bg-blue-700 transition"
          >
            <Camera className="w-6 h-6" />
            <div className="text-left">
              <div className="font-semibold">Capture Photo</div>
              <div className="text-sm opacity-80">Use device camera</div>
            </div>
          </button>

          {/* Upload Image */}
          <button
            onClick={() => fileInputRef.current?.click()}
            className="w-full flex items-center gap-3 bg-gray-200 text-gray-800 py-3 px-4 rounded-xl hover:bg-gray-300 transition"
          >
            <Upload className="w-6 h-6" />
            <div className="text-left">
              <div className="font-semibold">Upload Image</div>
              <div className="text-sm opacity-80">Choose from gallery</div>
            </div>
          </button>
        </div>

        {/* Hidden inputs */}
        <input
          ref={cameraInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileSelect}
          className="hidden"
          title="Capture photo from camera"
        />

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileSelect}
          className="hidden"
          title="Upload image from gallery"
        />

        <p className="text-center text-xs text-gray-500 mt-4">
          Supported: JPG, PNG, WebP • Max: 10MB
        </p>
      </div>
    </div>
  );
}
