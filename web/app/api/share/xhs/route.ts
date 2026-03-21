/**
 * XHS Social Card API — dynamic generation via Satori + resvg
 *
 * Node.js runtime (needs fs for font/data/photo-cache).
 *
 * Endpoints:
 *   GET /api/share/xhs?type=xhs-cover&city=tokyo
 *   GET /api/share/xhs?type=xhs-spot&city=tokyo&spot=0
 *   GET /api/share/xhs?type=xhs-spot&city=kyoto&spot=2
 *   GET /api/share/xhs?type=xhs-compare
 *   GET /api/share/xhs?type=wechat-moment&city=osaka
 *   GET /api/share/xhs?type=xhs-story&city=tokyo
 *
 * Returns: image/png
 */

import { NextRequest, NextResponse } from "next/server";
import { getRushScores } from "@/lib/data";
import { CITY_NAMES } from "@/lib/card-colors";
import {
  createXhsCoverElement,
  createXhsSpotElement,
  createXhsCompareElement,
  createMomentElement,
  createXhsStoryElement,
  type TemplateData,
} from "@/lib/card-templates";
import { batchFetchPhotos } from "@/lib/photo-cache";
import { renderToPng, SIZES } from "@/lib/satori";

// Force Node.js runtime — we need fs for fonts, data files, and photo cache
export const runtime = "nodejs";

// Cache for 10 minutes, stale-while-revalidate for 1 hour
export const revalidate = 600;

// ── Helpers ─────────────────────────────────────────────────────────────────

function buildTemplateData(cityCode: string): TemplateData | null {
  const rushData = getRushScores();
  const cityData = rushData.cities.find((c) => c.city_code === cityCode);
  if (!cityData) return null;

  return {
    city: cityCode,
    cityName: CITY_NAMES[cityCode] || cityData.city_name_cn,
    spots: cityData.spots,
    photoBuffers: {}, // will be filled after photo fetch
    updatedAt: rushData.updated_at || new Date().toISOString(),
  };
}

function buildAllTemplateData(): TemplateData[] {
  const rushData = getRushScores();
  return rushData.cities.map((c) => ({
    city: c.city_code,
    cityName: CITY_NAMES[c.city_code] || c.city_name_cn,
    spots: c.spots,
    photoBuffers: {},
    updatedAt: rushData.updated_at || new Date().toISOString(),
  }));
}

// ── Route Handler ───────────────────────────────────────────────────────────

const VALID_TYPES = ["xhs-cover", "xhs-spot", "xhs-compare", "wechat-moment", "xhs-story"] as const;
type CardType = (typeof VALID_TYPES)[number];

export async function GET(req: NextRequest) {
  try {
    const { searchParams } = new URL(req.url);
    const type = (searchParams.get("type") ?? "xhs-cover") as CardType;
    const city = (searchParams.get("city") ?? "tokyo").toLowerCase();
    const spotIndex = parseInt(searchParams.get("spot") ?? "0", 10);

    if (!VALID_TYPES.includes(type)) {
      return NextResponse.json(
        { error: `Invalid type. Valid: ${VALID_TYPES.join(", ")}` },
        { status: 400 },
      );
    }

    // Determine which size to render
    let size: { width: number; height: number };
    switch (type) {
      case "wechat-moment":
        size = SIZES.MOMENT;
        break;
      case "xhs-story":
        size = SIZES.STORY;
        break;
      default:
        size = SIZES.XHS;
        break;
    }

    let element: React.ReactElement;

    if (type === "xhs-compare") {
      // Compare needs all cities
      const allData = buildAllTemplateData();
      // Fetch photos for top spot of each city (for thumbnails if needed)
      for (const data of allData) {
        const topSpots = data.spots.slice(0, 1);
        data.photoBuffers = await batchFetchPhotos(topSpots);
      }
      element = createXhsCompareElement(allData);
    } else {
      // Single city templates
      const data = buildTemplateData(city);
      if (!data) {
        return NextResponse.json(
          { error: `City "${city}" not found. Available: ${Object.keys(CITY_NAMES).join(", ")}` },
          { status: 404 },
        );
      }

      // Fetch photos — for cover/story we need top 3, for spot just 1
      const spotsToFetch =
        type === "xhs-spot"
          ? [data.spots[spotIndex]].filter(Boolean)
          : data.spots.slice(0, 3);
      data.photoBuffers = await batchFetchPhotos(spotsToFetch);

      switch (type) {
        case "xhs-cover":
          element = createXhsCoverElement(data);
          break;
        case "xhs-spot":
          if (spotIndex >= data.spots.length) {
            return NextResponse.json(
              { error: `Spot index ${spotIndex} out of range. City "${city}" has ${data.spots.length} spots.` },
              { status: 404 },
            );
          }
          element = createXhsSpotElement(data, spotIndex);
          break;
        case "wechat-moment":
          element = createMomentElement(data);
          break;
        case "xhs-story":
          element = createXhsStoryElement(data);
          break;
        default:
          element = createXhsCoverElement(data);
      }
    }

    // Render to PNG
    const pngBuffer = await renderToPng(element, size);

    return new NextResponse(new Uint8Array(pngBuffer), {
      status: 200,
      headers: {
        "Content-Type": "image/png",
        "Cache-Control": "public, s-maxage=600, stale-while-revalidate=3600",
        "Content-Disposition": `inline; filename="${type}_${city}.png"`,
      },
    });
  } catch (err) {
    console.error("XHS card generation failed:", err);
    return NextResponse.json(
      { error: "Card generation failed", details: (err as Error).message },
      { status: 500 },
    );
  }
}
