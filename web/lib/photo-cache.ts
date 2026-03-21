/**
 * Photo cache utility for Satori card generation.
 * Fetches remote images and converts to base64 data URIs.
 * Caches locally to output/.photo-cache/ to avoid re-downloading.
 */

import { existsSync, mkdirSync, readFileSync, writeFileSync } from "fs";
import { join } from "path";

const DEFAULT_CACHE_DIR = join(process.cwd(), "output", ".photo-cache");

function ensureDir(dir: string) {
  if (!existsSync(dir)) mkdirSync(dir, { recursive: true });
}

function slugify(url: string): string {
  return url.replace(/[^a-zA-Z0-9]/g, "_").slice(-120) + ".jpg";
}

/**
 * Fetch a remote photo URL → base64 data URI.
 * Returns cached version if available.
 */
export async function fetchPhotoAsDataUri(
  url: string,
  cacheDir = DEFAULT_CACHE_DIR
): Promise<string | null> {
  if (!url) return null;

  ensureDir(cacheDir);
  const cacheFile = join(cacheDir, slugify(url));

  // Check cache first
  if (existsSync(cacheFile)) {
    const buf = readFileSync(cacheFile);
    const ext = url.includes(".png") ? "png" : "jpeg";
    return `data:image/${ext};base64,${buf.toString("base64")}`;
  }

  // Fetch remote
  try {
    const res = await fetch(url, {
      signal: AbortSignal.timeout(8000),
      headers: { "User-Agent": "Mozilla/5.0 SakuraRush/1.0" },
    });
    if (!res.ok) return null;

    const arrayBuf = await res.arrayBuffer();
    const buf = Buffer.from(arrayBuf);

    // Save to cache
    writeFileSync(cacheFile, buf);

    const ext = url.includes(".png") ? "png" : "jpeg";
    return `data:image/${ext};base64,${buf.toString("base64")}`;
  } catch (err) {
    console.warn(`  ⚠️ Failed to fetch photo: ${url}`, (err as Error).message);
    return null;
  }
}

/**
 * Batch fetch photos for multiple spots.
 * Returns a map of spot name → base64 data URI.
 */
export async function batchFetchPhotos(
  spots: Array<{ name: string; photo?: string }>,
  cacheDir = DEFAULT_CACHE_DIR,
  concurrency = 5
): Promise<Record<string, string>> {
  const result: Record<string, string> = {};
  const queue = spots.filter((s) => s.photo);

  // Process in batches
  for (let i = 0; i < queue.length; i += concurrency) {
    const batch = queue.slice(i, i + concurrency);
    const promises = batch.map(async (spot) => {
      const uri = await fetchPhotoAsDataUri(spot.photo!, cacheDir);
      if (uri) result[spot.name] = uri;
    });
    await Promise.all(promises);
  }

  return result;
}
