"use client";

import { useState } from "react";
import Review from "@/components/review";
import Settings from "@/components/settings";
import Sidebar, { type PageView } from "@/components/sidebar";

export default function Home() {
  const [activeView, setActiveView] = useState<PageView>("review");

  return (
    <main className="flex min-h-dvh">
      <Sidebar activeView={activeView} onViewChange={setActiveView} />
      <section aria-label="Main" className="min-h-dvh min-w-0 flex-1 overflow-auto">
        {activeView === "review" ? <Review /> : <Settings />}
      </section>
    </main>
  );
}
