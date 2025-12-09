import { Link } from "react-router-dom";
import { ArrowLeft, Mail, Phone, MapPin } from "lucide-react";

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

export default function Contact() {
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="p-4 border-b bg-white flex items-center gap-4">
        <Link to="/">
          <Button>
            <ArrowLeft className="w-5 h-5" />
          </Button>
        </Link>
        <h1 className="text-xl font-bold">Contact Us</h1>
      </header>

      <div className="max-w-3xl mx-auto p-6 space-y-6">
        <p className="text-gray-700">We would love to help you!</p>

        <div className="space-y-4">
          <p className="flex items-center gap-3 text-gray-700">
            <Phone className="w-5 h-5 text-blue-600" />
            +91 98765 43210
          </p>
          <p className="flex items-center gap-3 text-gray-700">
            <Mail className="w-5 h-5 text-blue-600" />
            support@vetra.ai
          </p>
          <p className="flex items-center gap-3 text-gray-700">
            <MapPin className="w-5 h-5 text-blue-600" />
            Pune, Maharashtra, India
          </p>
        </div>
      </div>
    </div>
  );
}
