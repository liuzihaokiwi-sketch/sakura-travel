import { getWeathernewsSpots, type Spot } from "@/lib/data";
import RushClient from "@/components/rush/RushClient";

export default function RushPage() {
  // Load data at build time (SSG)
  let dataByCity: Record<string, Spot[]> = {};

  try {
    const raw = getWeathernewsSpots();
    // Sort each city's spots by score descending
    for (const [city, spots] of Object.entries(raw)) {
      dataByCity[city] = [...spots].sort((a, b) => (b.score || 0) - (a.score || 0));
    }
  } catch {
    // Fallback if data files not available
    dataByCity = {};
  }

  return (
    <div style={{ height: "calc(100vh - 3.5rem)" }}>
      <RushClient dataByCity={dataByCity} />
    </div>
  );
}
