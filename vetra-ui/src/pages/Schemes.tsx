
import { Link } from "react-router-dom";
import { ExternalLink, FileText, IndianRupee, ArrowLeft } from "lucide-react";
import { useTranslation } from "react-i18next";

/* -------------------------------
    BASIC UI COMPONENTS (Manual)
--------------------------------*/

const Button = ({ children, onClick, variant = "default", className = "" }: any) => {
  const base =
    "flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-medium transition";

  const styles: any = {
    default: "bg-blue-600 text-white hover:bg-blue-700",
    outline: "border border-gray-400 hover:bg-gray-100",
    primary: "bg-blue-600 text-white hover:bg-blue-700",
    ghost: "hover:bg-gray-100",
  };

  return (
    <button onClick={onClick} className={`${base} ${styles[variant]} ${className}`}>
      {children}
    </button>
  );
};

const Card = ({ children, className = "" }: any) => (
  <div className={`border rounded-xl bg-white shadow-sm ${className}`}>{children}</div>
);

const CardHeader = ({ children }: any) => (
  <div className="border-b px-5 py-3">{children}</div>
);

const CardTitle = ({ children }: any) => (
  <h2 className="text-lg font-semibold">{children}</h2>
);

const CardContent = ({ children }: any) => <div className="p-5">{children}</div>;

/* -------------------------------
          PAGE COMPONENT
--------------------------------*/

export default function Schemes() {
  const { t } = useTranslation();

  const schemes = [
    {
      name: t("schemes.rashtriyaGokul.name"),
      description: t("schemes.rashtriyaGokul.description"),
      eligibility: t("schemes.rashtriyaGokul.eligibility"),
      benefits: t("schemes.rashtriyaGokul.benefits"),
      link: "https://dahd.nic.in/schemes/rashtriya-gokul-mission",
    },
    {
      name: t("schemes.dairyDevelopment.name"),
      description: t("schemes.dairyDevelopment.description"),
      eligibility: t("schemes.dairyDevelopment.eligibility"),
      benefits: t("schemes.dairyDevelopment.benefits"),
      link: "https://dahd.nic.in/schemes/programmes-implementation/national-programme-dairy-development",
    },
    {
      name: t("schemes.healthControl.name"),
      description: t("schemes.healthControl.description"),
      eligibility: t("schemes.healthControl.eligibility"),
      benefits: t("schemes.healthControl.benefits"),
      link: "https://dahd.nic.in/schemes/livestock-health-disease-control",
    },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="flex items-center gap-4 p-4 md:p-6 border-b bg-white shadow-sm">
        <Link to="/">
          <Button variant="ghost">
            <ArrowLeft className="w-5 h-5" />
          </Button>
        </Link>
        <h1 className="text-xl md:text-2xl font-bold">{t("schemes.title")}</h1>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto p-6 md:p-12">
        {/* Intro Card */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-blue-600">
              <FileText className="w-6 h-6" />
              {t("schemes.availableSchemes")}
            </CardTitle>
          </CardHeader>

          <CardContent>
            <p className="text-gray-600 text-lg">{t("schemes.description")}</p>
          </CardContent>
        </Card>

        {/* Schemes Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          {schemes.map((scheme, idx) => (
            <Card
              key={idx}
              className="hover:shadow-lg transition-shadow border-gray-200"
            >
              <CardHeader>
                <CardTitle className="text-blue-600">{scheme.name}</CardTitle>
              </CardHeader>

              <CardContent className="space-y-4">
                <p className="text-gray-700">{scheme.description}</p>

                <div className="space-y-2">
                  <p>
                    <span className="font-semibold">{t("schemes.eligibility")}:</span>{" "}
                    <span className="text-gray-600">{scheme.eligibility}</span>
                  </p>

                  <p>
                    <span className="font-semibold">{t("schemes.benefits")}:</span>{" "}
                    <span className="text-gray-600">{scheme.benefits}</span>
                  </p>
                </div>

                <Button
                  variant="outline"
                  className="w-full mt-3"
                  onClick={() => window.open(scheme.link, "_blank")}
                >
                  <ExternalLink className="w-4 h-4" />
                  {t("schemes.learnMore")}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Apply Section */}
        <Card className="bg-blue-50 border-blue-200">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-blue-700">
              <IndianRupee className="w-6 h-6" />
              {t("schemes.applyForSchemes")}
            </CardTitle>
          </CardHeader>

          <CardContent>
            <p className="text-gray-700 mb-6">{t("schemes.applyDescription")}</p>

            <Button
              variant="default"
              className="px-6 py-3"
              onClick={() => window.open("https://dahd.nic.in/", "_blank")}
            >
              <ExternalLink className="w-4 h-4" />
              {t("schemes.visitOfficialWebsite")}
            </Button>
          </CardContent>
        </Card>
      </main>
    </div>
  );
}
