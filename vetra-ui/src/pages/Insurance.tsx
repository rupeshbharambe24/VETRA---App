import { Link } from "react-router-dom";
import { ArrowLeft, ShieldCheck, ExternalLink } from "lucide-react";

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

export default function Insurance() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="p-4 border-b bg-white flex items-center gap-4">
        <Link to="/">
          <Button>
            <ArrowLeft className="w-5 h-5" />
          </Button>
        </Link>
        <h1 className="text-xl font-bold">Livestock Insurance</h1>
      </header>

      <div className="max-w-4xl mx-auto p-6 space-y-6">
        <p className="text-gray-700">
          Livestock insurance helps protect farmers from the financial impact of
          animal loss. Explore government-supported insurance schemes.
        </p>

        <div className="space-y-4">
          <div className="p-4 bg-white border rounded-lg shadow-sm">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <ShieldCheck className="w-6 h-6 text-blue-600" />
              National Livestock Insurance Scheme
            </h2>

            <p className="text-gray-700 mt-2">
              Provides insurance coverage for cattle, buffalo, sheep, goats, and
              more under government subsidy.
            </p>

            <Button
              className="mt-4"
              onClick={() => window.open("https://dahd.nic.in", "_blank")}
            >
              <ExternalLink className="w-4 h-4" />
              Visit Official Website
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
