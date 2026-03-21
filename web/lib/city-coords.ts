export interface CityCoord {
  code: string;
  name_cn: string;
  lat: number;
  lng: number;
  zoom: number;
}

export const CITY_COORDS: Record<string, CityCoord> = {
  tokyo: { code: "tokyo", name_cn: "东京", lat: 35.6762, lng: 139.6503, zoom: 12 },
  kyoto: { code: "kyoto", name_cn: "京都", lat: 35.0116, lng: 135.7681, zoom: 13 },
  osaka: { code: "osaka", name_cn: "大阪", lat: 34.6937, lng: 135.5023, zoom: 12 },
  nagoya: { code: "nagoya", name_cn: "名古屋", lat: 35.1815, lng: 136.9066, zoom: 12 },
  fukuoka: { code: "fukuoka", name_cn: "福冈", lat: 33.5904, lng: 130.4017, zoom: 12 },
  hiroshima: { code: "hiroshima", name_cn: "广岛", lat: 34.3853, lng: 132.4553, zoom: 12 },
  sapporo: { code: "sapporo", name_cn: "札幌", lat: 43.0621, lng: 141.3544, zoom: 12 },
  sendai: { code: "sendai", name_cn: "仙台", lat: 38.2682, lng: 140.8694, zoom: 12 },
  kagoshima: { code: "kagoshima", name_cn: "鹿儿岛", lat: 31.5966, lng: 130.5571, zoom: 12 },
  shizuoka: { code: "shizuoka", name_cn: "静冈", lat: 34.9756, lng: 138.3827, zoom: 12 },
};

export function getCityCoord(cityCode: string): CityCoord {
  return CITY_COORDS[cityCode] || CITY_COORDS.tokyo;
}
