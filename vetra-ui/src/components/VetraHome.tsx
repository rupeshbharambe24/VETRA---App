import { Link } from "react-router-dom";
import {
  Camera,
  Database,
  FileText,
  Shield,
  Phone,
  Info,
  Users,
  ArrowRight,
  Sparkles,
  BarChart3,
  Download,
  CheckCircle,
  Zap,
  Clock,
  TrendingUp,
  Heart,
  Scale
} from "lucide-react";

import vetraLogo from "@/assets/vetra-logo.png";
import traitIcon from "@/assets/trait-icon.png";
import dataIcon from "@/assets/data-icon.png";

export default function VetraHome() {
  const coreFeatures = [
    {
      icon: <Scale className="w-6 h-6" />,
      title: "Body Measurements",
      description: "Precise body length, height, and girth measurements using AI",
    },
    {
      icon: <Heart className="w-6 h-6" />,
      title: "Health Scoring",
      description: "1-9 scale body condition scoring for health assessment",
    },
    {
      icon: <TrendingUp className="w-6 h-6" />,
      title: "Weight Estimation",
      description: "Accurate weight estimation based on body measurements",
    },
    {
      icon: <Download className="w-6 h-6" />,
      title: "PDF Reports",
      description: "Download detailed analysis reports for record keeping",
    },
  ];

  const benefits = [
    { icon: <Zap className="w-4 h-4" />, text: "Instant AI Analysis" },
    { icon: <CheckCircle className="w-4 h-4" />, text: "High Accuracy" },
    { icon: <Clock className="w-4 h-4" />, text: "Save Time" },
    { icon: <Database className="w-4 h-4" />, text: "Track History" },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-700 text-white">
      {/* ---------------- HERO SECTION ---------------- */}
      <header className="relative py-20 px-6 md:px-12 max-w-7xl mx-auto">
        <div className="grid md:grid-cols-2 gap-10 items-center">
          {/* Left Hero */}
          <div className="text-center md:text-left">
            <div className="flex items-center justify-center md:justify-start gap-4 mb-5">
              <img src={vetraLogo} className="w-14 h-14 rounded-full" alt='logo'/>
              <h1 className="text-4xl font-bold tracking-tight">VETRA</h1>
            </div>

            <p className="text-lg text-white/90 mb-4">
              AI-powered livestock analysis with precise body measurements,
              health scoring, and weight estimation.
            </p>

            {/* Benefits chips */}
            <div className="flex flex-wrap gap-2 justify-center md:justify-start mb-6">
              {benefits.map((item, i) => (
                <div key={i} className="flex gap-2 items-center bg-white/10 backdrop-blur px-3 py-1.5 rounded-full text-sm">
                  {item.icon}
                  {item.text}
                </div>
              ))}
            </div>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center md:justify-start">
              <Link
                to="/trait-extraction"
                className="bg-white text-slate-900 font-semibold px-8 py-3 rounded-xl shadow hover:bg-slate-200 transition text-center"
              >
                <div className="flex items-center justify-center gap-2">
                  <Sparkles className="w-5 h-5" />
                  Start Analysis
                  <ArrowRight className="w-5 h-5" />
                </div>
              </Link>

              <Link
                to="/data-records"
                className="border border-white/40 text-white px-8 py-3 rounded-xl hover:bg-white/10 transition text-center"
              >
                <div className="flex items-center justify-center gap-2">
                  <Database className="w-5 h-5" />
                  View Records
                </div>
              </Link>
            </div>
          </div>

          {/* Right Hero Cards */}
          <div className="hidden md:grid grid-cols-2 gap-4">
            {[
              { icon: Camera, title: "Image Capture", text: "Upload images for AI analysis" },
              { icon: BarChart3, title: "Trait Analysis", text: "Get precise body measurements" },
              { icon: Database, title: "Data Storage", text: "Save and track past results" },
              { icon: Download, title: "PDF Reports", text: "Export detailed reports" },
            ].map((item, i) => (
              <div
                key={i}
                className="bg-white/10 p-5 rounded-xl backdrop-blur border border-white/20"
              >
                <item.icon className="w-8 h-8 text-white mb-3" />
                <h3 className="font-semibold">{item.title}</h3>
                <p className="text-white/70 text-sm">{item.text}</p>
              </div>
            ))}
          </div>
        </div>
      </header>

      {/* ---------------- CORE FEATURES ---------------- */}
      <section className="py-14 px-6 max-w-7xl mx-auto">
        <div className="text-center mb-10">
          <h2 className="text-3xl font-bold">What VETRA Offers</h2>
          <p className="text-white/70 max-w-2xl mx-auto">
            Comprehensive AI tools for livestock health and measurement.
          </p>
        </div>

        <div className="grid grid-cols-2 md:grid-cols-4 gap-5">
          {coreFeatures.map((feature, i) => (
            <div
              key={i}
              className="bg-white/5 border border-white/20 p-6 rounded-xl text-center hover:bg-white/10 transition"
            >
              <div className="w-12 h-12 mx-auto mb-3 bg-white/10 rounded-xl flex items-center justify-center">
                {feature.icon}
              </div>
              <h3 className="text-lg font-semibold">{feature.title}</h3>
              <p className="text-sm text-white/70">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ---------------- FEATURE CARDS ---------------- */}
      <section className="bg-slate-800/40 py-12 px-6">
        <div className="max-w-4xl mx-auto grid md:grid-cols-2 gap-6">
          {/* Trait Extraction */}
          <Link
            to="/trait-extraction"
            className="group bg-white/5 border border-white/20 p-6 rounded-xl hover:bg-white/10 transition"
          >
            <div className="flex items-start gap-4">
              <div className="bg-white/20 p-3 rounded-xl">
                <img src={traitIcon} className="w-8 h-8" alt="alte" />
              </div>

              <div className="flex-1">
                <h3 className="text-xl font-semibold group-hover:text-blue-300">Trait Extraction</h3>
                <p className="text-white/70 text-sm">
                  Automated body measurements, BCS scoring & weight prediction.
                </p>
              </div>

              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition" />
            </div>
          </Link>

          {/* Data Records */}
          <Link
            to="/data-records"
            className="group bg-white/5 border border-white/20 p-6 rounded-xl hover:bg-white/10 transition"
          >
            <div className="flex items-start gap-4">
              <div className="bg-white/20 p-3 rounded-xl">
                <img src={dataIcon} className="w-8 h-8" alt="data icon" />
              </div>

              <div className="flex-1">
                <h3 className="text-xl font-semibold group-hover:text-green-300">Data Records</h3>
                <p className="text-white/70 text-sm">
                  View past data, track changes & download reports.
                </p>
              </div>

              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition" />
            </div>
          </Link>
        </div>
      </section>

      {/* ---------------- QUICK ACCESS ---------------- */}
      <section className="bg-slate-900/40 py-14 px-6">
        <div className="max-w-6xl mx-auto">
          <h3 className="text-2xl font-bold text-center mb-8">Quick Access</h3>

          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            {[
              { to: "/schemes", icon: FileText, label: "Schemes" },
              { to: "/insurance", icon: Shield, label: "Insurance" },
              { to: "/helpline", icon: Phone, label: "Helpline" },
              { to: "/about", icon: Info, label: "About Us" },
              { to: "/contact", icon: Users, label: "Contact" },
            ].map((item, i) => (
              <Link
                key={i}
                to={item.to}
                className="bg-white/5 border border-white/20 p-6 text-center rounded-xl hover:bg-white/10 transition"
              >
                <item.icon className="w-8 h-8 mx-auto mb-2" />
                <span className="font-semibold">{item.label}</span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* ---------------- FOOTER ---------------- */}
      <footer className="py-8 text-center bg-slate-900/50 border-t border-white/10">
        <div className="flex items-center justify-center gap-3 mb-2">
          <img src={vetraLogo} className="w-7 h-7 rounded-full" alt="icon"/>
          <span className="font-bold text-lg">VETRA</span>
        </div>
        <p className="text-white/60 text-sm">Powered by AI for livestock intelligence.</p>
      </footer>
    </div>
  );
}
