import { Routes, Route } from "react-router-dom";

import VetraHome from "./components/VetraHome";
import TraitExtraction from "./pages/TraitExtraction";
import DataRecords from "./pages/DataRecords";
import Schemes from "./pages/Schemes";
import Insurance from "./pages/Insurance";
import Helpline from "./pages/Helpline";
import About from "./pages/About";
import Contact from "./pages/Contact";
import NotFound from "./pages/NotFound";


export default function App() {
  return (
    <Routes>
      <Route path="/" element={<VetraHome />} />
      <Route path="/trait-extraction" element={<TraitExtraction />} />
      <Route path="/data-records" element={<DataRecords />} />
      <Route path="/schemes" element={<Schemes />} />
      <Route path="/insurance" element={<Insurance />} />
      <Route path="/helpline" element={<Helpline />} />
      <Route path="/about" element={<About />} />
      <Route path="/contact" element={<Contact />} />
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

