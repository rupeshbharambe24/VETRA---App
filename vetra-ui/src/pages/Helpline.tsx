import { Link } from "react-router-dom";
import { ArrowLeft, PhoneCall, Shield } from "lucide-react";

const Button = ({ children, onClick, variant = "outline" }: any) => (
  <button
    onClick={onClick}
    className={`px-4 py-2 rounded-lg border ${
      variant === "outline"
        ? "hover:bg-gray-100"
        : "bg-blue-600 text-white hover:bg-blue-700"
    }`}
  >
    {children}
  </button>
);

export default function Helpline() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="p-4 border-b bg-white flex items-center gap-4">
        <Link to="/">
          <Button>
            <ArrowLeft className="w-5 h-5" />
          </Button>
        </Link>
        <h1 className="text-xl font-bold">Livestock Helpline</h1>
      </header>

      <div className="max-w-3xl mx-auto p-6 space-y-6">
        <p className="text-gray-700">
          Contact these official helpline numbers for livestock support.
        </p>

        <div className="space-y-4">
          <p className="flex items-center gap-3 text-gray-700">
            <PhoneCall className="w-5 h-5 text-green-600" />
            1800-180-1551 (National Animal Helpline)
          </p>

          <p className="flex items-center gap-3 text-gray-700">
            <Shield className="w-5 h-5 text-purple-600" />
            1962 (Animal Disease Control Helpdesk)
          </p>
        </div>
      </div>
    </div>
  );
}
