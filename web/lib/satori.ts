import satori from "satori";
import { Resvg } from "@resvg/resvg-js";
import { readFileSync } from "fs";
import { join } from "path";
import type { ReactNode } from "react";

// ── Font loading ────────────────────────────────────────────────────────────

let _fontBuffer: Buffer | null = null;

function getFontBuffer(): Buffer {
  if (_fontBuffer) return _fontBuffer;
  const fontPath = join(process.cwd(), "public", "fonts", "NotoSansSC-Regular.ttf");
  _fontBuffer = readFileSync(fontPath);
  return _fontBuffer;
}

// ── Render JSX to PNG ───────────────────────────────────────────────────────

export interface RenderOptions {
  width: number;
  height: number;
}

/**
 * Render a React element to SVG using Satori.
 */
export async function renderToSvg(
  element: ReactNode,
  options: RenderOptions
): Promise<string> {
  const fontData = getFontBuffer();

  const svg = await satori(element as React.ReactElement, {
    width: options.width,
    height: options.height,
    fonts: [
      {
        name: "Noto Sans SC",
        data: fontData,
        weight: 400,
        style: "normal",
      },
    ],
  });

  return svg;
}

/**
 * Render a React element to PNG buffer using Satori + resvg-js.
 */
export async function renderToPng(
  element: ReactNode,
  options: RenderOptions
): Promise<Buffer> {
  const svg = await renderToSvg(element, options);

  const resvg = new Resvg(svg, {
    fitTo: {
      mode: "width",
      value: options.width,
    },
  });

  const pngData = resvg.render();
  return Buffer.from(pngData.asPng());
}

// ── Preset sizes ────────────────────────────────────────────────────────────

export const SIZES = {
  /** 小红书标准尺寸 */
  XHS: { width: 1080, height: 1440 } as const,
  /** 朋友圈正方形 */
  MOMENT: { width: 1080, height: 1080 } as const,
  /** Instagram Story */
  STORY: { width: 1080, height: 1920 } as const,
} as const;
