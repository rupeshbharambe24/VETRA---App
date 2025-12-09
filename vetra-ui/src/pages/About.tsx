import { Link } from "react-router-dom";
import { ArrowLeft, Info } from "lucide-react";

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

export default function About() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="p-4 border-b bg-white flex items-center gap-4">
        <Link to="/">
          <Button>
            <ArrowLeft className="w-5 h-5" />
          </Button>
        </Link>
        <h1 className="text-xl font-bold">About VETRA</h1>
      </header>

      {/* Content */}
      <div className="max-w-3xl mx-auto p-6 space-y-6">
        <h2 className="text-2xl font-semibold flex items-center gap-2">
          <Info className="w-6 h-6 text-blue-600" />
          Our Mission
        </h2>

        <p className="text-gray-700 leading-relaxed">
          VETRA is an AI-powered livestock analysis platform designed to provide
          accurate body measurements, health scoring, weight estimation, and
          detailed reports — helping farmers and veterinarians improve livestock
          management with precision.
        </p>

        <p className="text-gray-700 leading-relaxed">
          Our goal is to make animal health assessment fast, accessible, and
          reliable using computer vision and machine learning.
        </p>
      </div>
    </div>
  );
}
