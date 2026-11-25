export interface Ship {
  id: string;
  name: string;
  callSign: string;
  mmsi: string;
  vesselType: string;
  destination: string;
  status: string;
  latitude: number;
  longitude: number;
  speedKnots: number;
  heading: number;
  cargoPercent: number;
  updatedAt: string;
}

export class ApiError extends Error {
  constructor(message: string, readonly status: number) {
    super(message);
    this.name = 'ApiError';
  }
}

const apiUrl = (import.meta.env.VITE_API_URL ?? 'https://api.ships.damoverflow.com/api').replace(/\/$/, '');

export async function fetchShips(accessToken: string, signal: AbortSignal): Promise<Ship[]> {
  const response = await fetch(`${apiUrl}/ships`, {
    headers: {
      Accept: 'application/json',
      Authorization: `Bearer ${accessToken}`,
    },
    signal,
  });

  if (!response.ok) {
    throw new ApiError(`Ship feed returned ${response.status}.`, response.status);
  }

  return response.json() as Promise<Ship[]>;
}