import { Link } from "react-router-dom";
import { ArrowLeft, AlertTriangle } from "lucide-react";

const Button = ({ children, variant = "outline" }: any) => (
  <button
    className={`px-4 py-2 rounded-lg border ${
      variant === "outline"
        ? "hover:bg-gray-100"
        : "bg-blue-600 text-white hover:bg-blue-700"
    }`}
  >
    {children}
  </button>
);

export default function NotFound() {
  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
      <div className="text-center space-y-4">
        <AlertTriangle className="w-16 h-16 text-yellow-500 mx-auto" />
        <h1 className="text-3xl font-bold">404 - Page Not Found</h1>
        <p className="text-gray-600">
          The page you’re looking for doesn’t exist or has been moved.
        </p>

        <Link to="/">
          <Button className="mt-4 flex items-center gap-2">
            <ArrowLeft className="w-5 h-5" />
            Go Back Home
          </Button>
        </Link>
      </div>
    </div>
  );
}
