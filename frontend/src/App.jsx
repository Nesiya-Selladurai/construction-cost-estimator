import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar.jsx";
import Home from "./pages/Home.jsx";
import Predict from "./pages/Predict.jsx";
import About from "./pages/About.jsx";

export default function App() {
  return (
    <div className="min-h-screen bg-blueprint-paper">
      <Navbar />
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/predict" element={<Predict />} />
          <Route path="/about" element={<About />} />
        </Routes>
      </main>
    </div>
  );
}
