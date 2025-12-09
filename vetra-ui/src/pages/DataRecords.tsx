import  { useState, useEffect, useCallback } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Calendar,
  RefreshCw,
  AlertCircle,
  Plus,
  TrendingUp,
  Search,
  Activity,
} from "lucide-react";
import { getResults, HistoricalRecord } from "@/lib/api";
import { z } from "zod";


const Button = ({
  children,
  onClick,
  disabled,
  variant = "default",
  className = "",
}: any) => {
  const base =
    "inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-medium transition";
  const styles: any = {
    default: "bg-blue-600 text-white hover:bg-blue-700",
    outline: "border border-gray-400 hover:bg-gray-100",
    ghost: "hover:bg-gray-100",
  };

  return (
    <button
      disabled={disabled}
      onClick={onClick}
      className={`${base} ${styles[variant]} ${
        disabled ? "opacity-50 cursor-not-allowed" : ""
      } ${className}`}
    >
      {children}
    </button>
  );
};

const Card = ({ children }: any) => (
  <div className="border rounded-xl bg-white shadow-sm">{children}</div>
);

const CardHeader = ({ children }: any) => (
  <div className="border-b px-5 py-3">{children}</div>
);

const CardTitle = ({ children }: any) => (
  <h2 className="text-lg font-semibold">{children}</h2>
);

const CardContent = ({ children }: any) => (
  <div className="p-5">{children}</div>
);

const Table = ({ children }: any) => (
  <table className="min-w-full text-sm border border-gray-300">{children}</table>
);
const Th = ({ children }: any) => (
  <th className="px-3 py-2 bg-gray-100 font-semibold text-left border-b">
    {children}
  </th>
);
const Td = ({ children }: any) => (
  <td className="px-3 py-2 border-b">{children}</td>
);

/* -------------------------------
             MAIN PAGE
--------------------------------*/

const searchSchema = z.object({
  search: z.string().max(100),
});

export default function DataRecords() {
  const [records, setRecords] = useState<HistoricalRecord[]>([]);
  const [searchTerm, setSearchTerm] = useState("");
  const [loading, setLoading] = useState(true);
  const [totalCount, setTotalCount] = useState(0);
  const [hasMore, setHasMore] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const navigate = useNavigate();

  /* ----------------------- FETCH FUNCTION ----------------------- */
  const fetchRecords = useCallback(
    async (search: string = "", offset: number = 0) => {
      try {
        setError(null);

        if (search) {
          const validated = searchSchema.parse({ search });
          search = validated.search;
        }

        const response = await getResults(50, offset, search);

        if (!response.success || !response.data) {
          throw new Error(response.error || "Failed to fetch records");
        }

        // sort by date
        const sorted = [...response.data].sort(
          (a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()
        );

        setRecords(sorted);
        setHasMore(response.hasMore || false);
        setTotalCount(response.totalCount || 0);
      } catch (e) {
        const msg =
          e instanceof Error ? e.message : "Unable to load records";
        setError(msg);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  /* ----------------------- INITIAL + INTERVAL REFRESH ---------------------- */
  useEffect(() => {
    fetchRecords();
    const interval = setInterval(
      () => fetchRecords(searchTerm, 0),
      30000
    );
    return () => clearInterval(interval);
  }, [fetchRecords, searchTerm]);

  /* ----------------------- SEARCH (DEBOUNCE) ---------------------- */
  useEffect(() => {
    const delay = setTimeout(() => {
      setLoading(true);
      fetchRecords(searchTerm);
    }, 500);
    return () => clearTimeout(delay);
  }, [searchTerm, fetchRecords]);

  /* ----------------------- HELPERS ---------------------- */

  const formatDate = (d: string) =>
    new Date(d).toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });

  const formatConfidence = (v?: number) =>
    v === undefined || v === null ? "-" : v.toFixed(2);

  const getScoreColor = (s: number) =>
    s <= 3
      ? "bg-red-100 text-red-600"
      : s <= 6
      ? "bg-yellow-100 text-yellow-700"
      : "bg-green-100 text-green-700";

  /* ----------------------- RENDER ---------------------- */

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="p-4 flex items-center justify-between border-b bg-white shadow-sm">
        <div className="flex items-center gap-3">
          <Link to="/">
            <Button variant="ghost">
              <ArrowLeft className="w-5 h-5" />
            </Button>
          </Link>

          <div>
            <h1 className="text-xl font-bold">Past Records</h1>
            <p className="text-gray-500 text-sm">
              {totalCount} total records
            </p>
          </div>
        </div>

        <Button onClick={() => navigate("/trait-extraction")}>
          <Plus className="w-4 h-4" /> New Analysis
        </Button>
      </header>

      <div className="p-4 md:p-8 max-w-6xl mx-auto space-y-6">
        {/* Search */}
        <Card>
          <CardContent className="flex flex-col sm:flex-row gap-4 items-center">
            <div className="relative w-full">
              <Search className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
              <input
                className="border rounded-lg w-full pl-10 px-3 py-2"
                placeholder="Search animal type or notes..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>

            <Button variant="outline" onClick={() => fetchRecords(searchTerm)}>
              <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
              Refresh
            </Button>
          </CardContent>
        </Card>

        {/* Loading */}
        {loading && (
          <Card>
            <CardContent className="text-center py-10">
              <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
              <p className="text-gray-500">Loading records…</p>
            </CardContent>
          </Card>
        )}

        {/* No Results */}
        {!loading && records.length === 0 && (
          <Card>
            <CardContent className="text-center py-12">
              <Activity className="w-16 h-16 mx-auto text-gray-300 mb-4" />
              <h2 className="text-lg font-semibold">No Records Found</h2>
              <p className="text-gray-500 mb-4">
                {searchTerm ? "Try a different search" : "Run your first analysis"}
              </p>
              <Button onClick={() => navigate("/trait-extraction")}>
                <Plus className="w-4 h-4" /> Start New Analysis
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Table View */}
        {!loading && records.length > 0 && (
          <>
            <Card className="hidden md:block">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-blue-600" />
                  Analysis History
                </CardTitle>
              </CardHeader>

              <CardContent>
                <Table>
                  <thead>
                    <tr>
                      <Th>Date</Th>
                      <Th>Animal</Th>
                      <Th className="text-center">Body Length</Th>
                      <Th className="text-center">Height</Th>
                      <Th className="text-center">Girth</Th>
                      <Th className="text-center">Confidence</Th>
                      <Th>Notes</Th>
                    </tr>
                  </thead>

                  <tbody>
                    {records.map((r) => (
                      <tr key={r.id} className="hover:bg-gray-100 transition">
                        <Td>
                          <div className="flex items-center gap-2">
                            <Calendar className="w-4 h-4 text-gray-400" />
                            {formatDate(r.date)}
                          </div>
                        </Td>

                        <Td className="capitalize">{r.animalType}</Td>

                        <Td className="text-center font-semibold text-blue-600">
                          {r.bodyLength} cm
                        </Td>

                        <Td className="text-center font-semibold text-indigo-600">
                          {r.withersHeight} cm
                        </Td>

                        <Td className="text-center font-semibold text-purple-600">
                          {r.girth} cm
                        </Td>

                        <Td className="text-center">
                          <span
                            className={`px-2 py-1 rounded-full text-xs font-medium ${getScoreColor(
                              r.confidence
                            )}`}
                          >
                            {formatConfidence(r.confidence)}%
                          </span>
                        </Td>

                        <Td className="text-gray-500 max-w-[200px] truncate">
                          {r.notes || "-"}
                        </Td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </CardContent>
            </Card>

            {/* Mobile Cards */}
            <div className="md:hidden space-y-4">
              {records.map((r) => (
                <Card key={r.id}>
                  <CardContent className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="bg-blue-100 text-blue-700 px-2 py-1 rounded text-xs capitalize">
                        {r.animalType}
                      </span>

                      <span className="text-xs text-gray-500 flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {formatDate(r.date)}
                      </span>
                    </div>

                    <div className="grid grid-cols-3 gap-2">
                      <div className="bg-blue-50 p-3 text-center rounded">
                        <div className="font-bold">{r.bodyLength}</div>
                        <div className="text-xs text-gray-500">Length</div>
                      </div>

                      <div className="bg-indigo-50 p-3 text-center rounded">
                        <div className="font-bold">{r.withersHeight}</div>
                        <div className="text-xs text-gray-500">Height</div>
                      </div>

                      <div className="bg-purple-50 p-3 text-center rounded">
                        <div className="font-bold">{r.girth}</div>
                        <div className="text-xs text-gray-500">Girth</div>
                      </div>
                    </div>

                    {r.notes && (
                      <p className="text-sm text-gray-500 truncate">{r.notes}</p>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>

            <p className="text-center text-gray-500 text-sm mt-6">
              Showing {records.length} of {totalCount} records
            </p>
          </>
        )}
      </div>
    </div>
  );
}
