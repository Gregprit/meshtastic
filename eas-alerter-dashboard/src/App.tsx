import { NavLink, Route, Routes } from "react-router-dom";
import Dashboard from "./pages/Dashboard";
import BBSViewer from "./pages/BBSViewer";
import Settings from "./pages/Settings";
import HistoryView from "./pages/HistoryView";

export default function App() {
  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>Meshtastic SAME/EAS Alerter</h1>
        <nav>
          <NavLink to="/" end>
            Dashboard
          </NavLink>
          <NavLink to="/bbs">BBS Viewer</NavLink>
          <NavLink to="/history">History</NavLink>
          <NavLink to="/settings">Settings</NavLink>
        </nav>
      </header>
      <main>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/bbs" element={<BBSViewer />} />
          <Route path="/history" element={<HistoryView />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  );
}
