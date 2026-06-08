import { useState } from "react";

import { LocationList } from "./LocationList";
import { SectorList } from "./SectorList";

type Tab = "setores" | "locais";

export function SetoresLocaisPage() {
  const [tab, setTab] = useState<Tab>("setores");

  return (
    <div className="flex flex-col h-full">
      <div className="border-b bg-white px-6 pt-4">
        <div className="flex gap-0">
          <button
            onClick={() => setTab("setores")}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              tab === "setores"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            Setores
          </button>
          <button
            onClick={() => setTab("locais")}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              tab === "locais"
                ? "border-blue-600 text-blue-600"
                : "border-transparent text-gray-500 hover:text-gray-700"
            }`}
          >
            Locais
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {tab === "setores" ? <SectorList /> : <LocationList />}
      </div>
    </div>
  );
}
