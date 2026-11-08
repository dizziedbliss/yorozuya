import { useQuery } from "@tanstack/react-query";
import { useEffect, useRef } from "react";
import { NavLink, Route, Routes, useLocation } from "react-router";
import { PassphraseGate } from "./components/PassphraseGate";
import { api } from "./lib/api";
import { reducedMotion } from "./lib/motion";
import { Fresher } from "./pages/Fresher";
import { JobPoster } from "./pages/JobPoster";
import { Receipts } from "./pages/Receipts";
import { Soon } from "./pages/Soon";

const PAGE_OF: Record<string, string> = { "": "fresher", jobs: "poster", receipts: "receipts", log: "log", curated: "curated", settings: "settings" };

export function App() {
  const location = useLocation();
  const wipe = useRef<HTMLDivElement>(null);
  const first = useRef(true);

  // Each page wears its own paper (Log is Tizón cream); the body carries which one.
  useEffect(() => {
    document.body.dataset.page = PAGE_OF[location.pathname.split("/")[1] ?? ""] ?? "fresher";
    scrollTo(0, 0);
    if (first.current || reducedMotion()) { first.current = false; return; }
    const el = wipe.current;
    if (!el) return;
    el.classList.remove("go");
    void el.offsetWidth; // restart the animation
    el.classList.add("go");
  }, [location.pathname]);

  return (
    <>
      <div className="grain" aria-hidden="true" />
      <div className="wipe" ref={wipe} aria-hidden="true" />
      <PassphraseGate>
        <Nav />
        <main>
          <Routes>
            <Route index element={<Fresher />} />
            <Route path="jobs/:id" element={<JobPoster />} />
            <Route path="receipts" element={<Receipts />} />
            <Route path="log" element={<Soon what="The log" />} />
            <Route path="curated" element={<Soon what="Curated" />} />
            <Route path="settings" element={<Soon what="Settings" />} />
            <Route path="*" element={<Soon what="This page" lost />} />
          </Routes>
        </main>
      </PassphraseGate>
    </>
  );
}

function Nav() {
  const receipts = useQuery({ queryKey: ["receipts"], queryFn: api.receipts });
  const sent = receipts.data?.stats.sent ?? 0;
  const cls = ({ isActive }: { isActive: boolean }) => (isActive ? "active" : "");
  return (
    <header className="navbar">
      <nav className="wrap nav" aria-label="Pages">
        <NavLink to="/" end className={cls}>Fresher</NavLink>
        <NavLink to="/receipts" className={cls}>Receipts{sent > 0 && <span className="count" aria-label={`${sent} sent`}>{sent}</span>}</NavLink>
        <NavLink to="/log" className={cls}>Log</NavLink>
        <NavLink to="/curated" className={cls}>Curated</NavLink>
        <NavLink to="/settings" className={cls}>Settings</NavLink>
      </nav>
    </header>
  );
}
