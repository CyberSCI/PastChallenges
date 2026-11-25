import type { KeyboardEvent } from 'react';
import type { Ship } from './api';
import saintJohnGeoJson from './saint-john-map.json?raw';

type Coordinate = [number, number];

interface MapFeature {
  id: string;
  properties: {
    name?: string;
    natural?: string;
    place?: string;
    water?: string;
  };
  geometry: {
    type: string;
    coordinates: unknown;
  };
}

interface MapFeatureCollection {
  features: MapFeature[];
}

interface RadarMapProps {
  ships: Ship[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

const chartArea = {
  left: 34,
  top: 28,
  width: 1032,
  height: 584,
};

const gridLines = Array.from({ length: 11 }, (_, index) => index);
const mapFeatures = (JSON.parse(saintJohnGeoJson) as MapFeatureCollection).features;
const chartFocus = {
  west: -66.17,
  east: -65.97,
  south: 45.155,
  north: 45.285,
};

function mercatorY(latitude: number) {
  const radians = (latitude * Math.PI) / 180;
  return Math.log(Math.tan(Math.PI / 4 + radians / 2));
}

function latitudeFromMercatorY(value: number) {
  return ((2 * Math.atan(Math.exp(value)) - Math.PI / 2) * 180) / Math.PI;
}

const chart = (() => {
  const mercatorSouth = mercatorY(chartFocus.south);
  const mercatorNorth = mercatorY(chartFocus.north);
  const dataWidth = ((chartFocus.east - chartFocus.west) * Math.PI) / 180;
  const dataHeight = mercatorNorth - mercatorSouth;
  const aspectRatio = chartArea.width / chartArea.height;
  const padding = 0.025;
  const height = Math.max(dataHeight, dataWidth / aspectRatio) * (1 + padding * 2);
  const width = height * aspectRatio;
  const centerLongitude = ((chartFocus.west + chartFocus.east) / 2) * (Math.PI / 180);
  const centerMercator = (mercatorSouth + mercatorNorth) / 2;
  const longitudeSpan = (width * 180) / Math.PI;
  const viewMercatorSouth = centerMercator - height / 2;
  const viewMercatorNorth = centerMercator + height / 2;

  return {
    west: (centerLongitude * 180) / Math.PI - longitudeSpan / 2,
    east: (centerLongitude * 180) / Math.PI + longitudeSpan / 2,
    mercatorSouth: viewMercatorSouth,
    mercatorNorth: viewMercatorNorth,
  };
})();

function projectCoordinate([longitude, latitude]: Coordinate) {
  return {
    x: chartArea.left + ((longitude - chart.west) / (chart.east - chart.west)) * chartArea.width,
    y: chartArea.top + ((chart.mercatorNorth - mercatorY(latitude)) / (chart.mercatorNorth - chart.mercatorSouth)) * chartArea.height,
  };
}

function latitudeAtFraction(fraction: number) {
  const mercatorLatitude = chart.mercatorNorth - fraction * (chart.mercatorNorth - chart.mercatorSouth);
  return latitudeFromMercatorY(mercatorLatitude);
}

function simplifyCoordinates(coordinates: Coordinate[]): Coordinate[] {
  if (coordinates.length <= 2) return coordinates;

  const projected = coordinates.map(projectCoordinate);
  const retained = new Uint8Array(coordinates.length);
  const stack: [number, number][] = [[0, coordinates.length - 1]];
  retained[0] = 1;
  retained[coordinates.length - 1] = 1;

  while (stack.length > 0) {
    const [startIndex, endIndex] = stack.pop()!;
    const start = projected[startIndex];
    const end = projected[endIndex];
    const deltaX = end.x - start.x;
    const deltaY = end.y - start.y;
    const lengthSquared = deltaX * deltaX + deltaY * deltaY;
    let farthestDistanceSquared = 0.65 * 0.65;
    let farthestIndex = -1;

    for (let index = startIndex + 1; index < endIndex; index += 1) {
      const point = projected[index];
      const projection = lengthSquared === 0
        ? 0
        : Math.max(0, Math.min(1, ((point.x - start.x) * deltaX + (point.y - start.y) * deltaY) / lengthSquared));
      const nearestX = start.x + projection * deltaX;
      const nearestY = start.y + projection * deltaY;
      const distanceX = point.x - nearestX;
      const distanceY = point.y - nearestY;
      const distanceSquared = distanceX * distanceX + distanceY * distanceY;

      if (distanceSquared > farthestDistanceSquared) {
        farthestDistanceSquared = distanceSquared;
        farthestIndex = index;
      }
    }

    if (farthestIndex >= 0) {
      retained[farthestIndex] = 1;
      stack.push([startIndex, farthestIndex], [farthestIndex, endIndex]);
    }
  }

  return coordinates.filter((_, index) => retained[index] === 1);
}

function pathForCoordinates(coordinates: Coordinate[], close = false) {
  const path = simplifyCoordinates(coordinates)
    .map((coordinate, index) => {
      const point = projectCoordinate(coordinate);
      return `${index === 0 ? 'M' : 'L'}${point.x.toFixed(1)} ${point.y.toFixed(1)}`;
    })
    .join(' ');

  return close ? `${path} Z` : path;
}

function getLineStrings(feature: MapFeature): Coordinate[][] {
  if (feature.geometry.type === 'LineString') return [feature.geometry.coordinates as Coordinate[]];
  if (feature.geometry.type === 'MultiLineString') return feature.geometry.coordinates as Coordinate[][];
  return [];
}

function getPolygons(feature: MapFeature): Coordinate[][][] {
  if (feature.geometry.type === 'Polygon') return [feature.geometry.coordinates as Coordinate[][]];
  if (feature.geometry.type === 'MultiPolygon') return feature.geometry.coordinates as Coordinate[][][];
  return [];
}

function pathForPolygon(rings: Coordinate[][]) {
  return rings.map((ring) => pathForCoordinates(ring, true)).join(' ');
}

function coordinateKey([longitude, latitude]: Coordinate) {
  return `${longitude.toFixed(7)},${latitude.toFixed(7)}`;
}

function getLastVerticalEdgeIntersectionY(coordinates: Coordinate[], edgeX: number) {
  const projected = coordinates.map(projectCoordinate);
  let intersectionY: number | undefined;

  for (let index = 1; index < projected.length; index += 1) {
    const start = projected[index - 1];
    const end = projected[index];
    const fraction = (edgeX - start.x) / (end.x - start.x);
    if (fraction < 0 || fraction > 1 || !Number.isFinite(fraction)) continue;

    const candidateY = start.y + fraction * (end.y - start.y);
    if (candidateY >= chartArea.top && candidateY <= chartArea.top + chartArea.height) {
      intersectionY = candidateY;
    }
  }

  return intersectionY;
}

function getMainlandCoastline(segments: Coordinate[][]): Coordinate[] {
  const endpointCounts = new Map<string, number>();
  segments.forEach((segment) => {
    [segment[0], segment[segment.length - 1]].forEach((coordinate) => {
      const key = coordinateKey(coordinate);
      endpointCounts.set(key, (endpointCounts.get(key) ?? 0) + 1);
    });
  });

  const openEndpoints = segments.flatMap((segment, segmentIndex) => [
    { coordinate: segment[0], segmentIndex },
    { coordinate: segment[segment.length - 1], segmentIndex },
  ]).filter(({ coordinate }) => endpointCounts.get(coordinateKey(coordinate)) === 1);
  const start = openEndpoints.sort((a, b) => a.coordinate[0] - b.coordinate[0])[0];
  if (!start) return segments.reduce((longest, segment) => segment.length > longest.length ? segment : longest, []);

  const firstSegment = segments[start.segmentIndex];
  const coastline = coordinateKey(firstSegment[0]) === coordinateKey(start.coordinate)
    ? [...firstSegment]
    : [...firstSegment].reverse();
  const usedSegments = new Set([start.segmentIndex]);

  while (true) {
    const endpoint = coordinateKey(coastline[coastline.length - 1]);
    const nextIndex = segments.findIndex((segment, index) => (
      !usedSegments.has(index)
      && (coordinateKey(segment[0]) === endpoint || coordinateKey(segment[segment.length - 1]) === endpoint)
    ));
    if (nextIndex < 0) break;

    const nextSegment = segments[nextIndex];
    const orientedSegment = coordinateKey(nextSegment[0]) === endpoint
      ? nextSegment
      : [...nextSegment].reverse();
    coastline.push(...orientedSegment.slice(1));
    usedSegments.add(nextIndex);
  }

  return coastline;
}

const coastlineSegments = mapFeatures.flatMap((feature) => (
  feature.properties.natural === 'coastline' ? getLineStrings(feature) : []
));
const coastlinePaths = coastlineSegments.map((segment) => pathForCoordinates(segment));
const mainlandCoastline = getMainlandCoastline(coastlineSegments);
const firstCoastPoint = projectCoordinate(mainlandCoastline[0]);
const rightCoastIntersectionY = getLastVerticalEdgeIntersectionY(
  mainlandCoastline,
  chartArea.left + chartArea.width,
);
const lastCoastPoint = projectCoordinate(mainlandCoastline[mainlandCoastline.length - 1]);
const mainlandLandPath = [
  pathForCoordinates(mainlandCoastline),
  `L ${chartArea.left + chartArea.width} ${(rightCoastIntersectionY ?? lastCoastPoint.y).toFixed(1)} L ${chartArea.left + chartArea.width} ${chartArea.top} L ${chartArea.left} ${chartArea.top} L ${chartArea.left} ${firstCoastPoint.y.toFixed(1)} Z`,
].join(' ');
const islandPaths = mapFeatures.flatMap((feature) => (
  feature.properties.place === 'islet' || feature.properties.place === 'island' || feature.properties.natural === 'coastline'
    ? getPolygons(feature).map(pathForPolygon)
    : []
));
const riverPaths = mapFeatures.flatMap((feature) => (
  feature.properties.natural === 'water' && feature.properties.water === 'river'
    ? getPolygons(feature).map(pathForPolygon)
    : []
));

function findPlace(name: string): Coordinate | undefined {
  const place = mapFeatures.find((feature) => (
    feature.properties.name === name && feature.geometry.type === 'Point'
  ));
  return place ? place.geometry.coordinates as Coordinate : undefined;
}

const placeLabels = ['Saint John', 'Lorneville', 'Taylors Island'].flatMap((name) => {
  const coordinate = findPlace(name);
  return coordinate ? [{ name: name.toUpperCase(), coordinate }] : [];
});
const partridgeIsland = mapFeatures.find((feature) => feature.properties.name === 'Partridge Island');
const partridgeRing = partridgeIsland ? getPolygons(partridgeIsland)[0]?.[0] : undefined;
const partridgeCenter = partridgeRing?.length
  ? partridgeRing.reduce<Coordinate>((center, coordinate) => [center[0] + coordinate[0] / partridgeRing.length, center[1] + coordinate[1] / partridgeRing.length], [0, 0])
  : undefined;

function projectPosition(ship: Ship) {
  return projectCoordinate([ship.longitude, ship.latitude]);
}

export default function RadarMap({ ships, selectedId, onSelect }: RadarMapProps) {
  function selectWithKeyboard(event: KeyboardEvent<SVGGElement>, id: string) {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onSelect(id);
    }
  }

  return (
    <svg className="radar-map" viewBox="0 0 1100 640" role="img" aria-label="Live vessel positions in the Bay of Fundy off Saint John, New Brunswick">
      <defs>
        <pattern id="chart-grid" width="44" height="44" patternUnits="userSpaceOnUse">
          <path d="M 44 0 L 0 0 0 44" className="chart-grid-line" />
        </pattern>
        <clipPath id="chart-clip">
          <rect x="18" y="18" width="1064" height="604" rx="2" />
        </clipPath>
      </defs>
      <rect width="1100" height="640" className="chart-water" />
      <rect width="1100" height="640" fill="url(#chart-grid)" />
      <g clipPath="url(#chart-clip)">
        <path className="chart-landmass" d={mainlandLandPath} />
        {riverPaths.map((path, index) => <path key={`river-${index}`} className="chart-water-area" d={path} fillRule="evenodd" />)}
        {islandPaths.map((path, index) => <path key={`island-${index}`} className="chart-island" d={path} fillRule="evenodd" />)}
        {coastlinePaths.map((path, index) => <path key={`coast-${index}`} className="chart-coastline" d={path} />)}

        <g className="chart-place-labels" aria-hidden="true">
          {placeLabels.map((label) => {
            const point = projectCoordinate(label.coordinate);
            return <text key={label.name} x={point.x} y={point.y - 9} textAnchor="middle">{label.name}</text>;
          })}
          {partridgeCenter && (() => {
            const point = projectCoordinate(partridgeCenter);
            return <text x={point.x + 18} y={point.y + 4}>PARTRIDGE ISLAND</text>;
          })()}
          <text x="464" y="102" className="water-label" transform="rotate(-18 464 102)">SAINT JOHN RIVER</text>
          <text x="514" y="548" className="water-label">BAY OF FUNDY</text>
          {gridLines.map((line) => (
            <text key={`lat-${line}`} x="24" y={chartArea.top + (line / 10) * chartArea.height + 14} className="coordinate-label">
              {`${latitudeAtFraction(line / 10).toFixed(2)}N`}
            </text>
          ))}
          {gridLines.map((line) => (
            <text key={`lon-${line}`} x={chartArea.left + (line / 10) * chartArea.width} y="614" className="coordinate-label" textAnchor="middle">
              {`${Math.abs(chart.west + (line / 10) * (chart.east - chart.west)).toFixed(2)}W`}
            </text>
          ))}
        </g>

        {ships.map((ship) => {
          const point = projectPosition(ship);
          const isSelected = ship.id === selectedId;
          const radians = (ship.heading * Math.PI) / 180;
          const headingLineX = point.x + Math.sin(radians) * 38;
          const headingLineY = point.y - Math.cos(radians) * 38;
          const labelX = point.x > 760 ? point.x - 18 : point.x + 18;

          return (
            <g
              key={ship.id}
              className={`vessel-track${isSelected ? ' is-selected' : ''}`}
              role="button"
              tabIndex={0}
              aria-label={`Select ${ship.name}, ${ship.speedKnots.toFixed(1)} knots`}
              aria-pressed={isSelected}
              onClick={() => onSelect(ship.id)}
              onKeyDown={(event) => selectWithKeyboard(event, ship.id)}
            >
              <line className="vessel-trail" x1={point.x} y1={point.y} x2={headingLineX} y2={headingLineY} />
              <g transform={`translate(${point.x} ${point.y}) rotate(${ship.heading})`}>
                <circle className="vessel-pulse" r="17" />
                <path className="vessel-symbol" d="M0 -12 L8 8 L0 4 L-8 8 Z" />
                <circle className="vessel-core" r="2.2" />
              </g>
              <text className="vessel-label" x={labelX} y={point.y - 7} textAnchor={point.x > 760 ? 'end' : 'start'}>
                {ship.name.toUpperCase()}
              </text>
              <text className="vessel-label-meta" x={labelX} y={point.y + 9} textAnchor={point.x > 760 ? 'end' : 'start'}>
                {`${ship.speedKnots.toFixed(1)} KN / ${String(ship.heading).padStart(3, '0')} DEG`}
              </text>
            </g>
          );
        })}
      </g>
      <g className="compass-mark" aria-hidden="true" transform="translate(1030 67)">
        <path d="M0 -20 L7 7 L0 3 L-7 7 Z" />
        <text x="0" y="-28" textAnchor="middle">N</text>
      </g>
      <text className="map-reference" x="22" y="28">CHART 45.2 N / 66.1 W</text>
      <text className="map-reference map-reference-attribution" x="1078" y="598" textAnchor="end">&#169; OpenStreetMap contributors</text>
      <text className="map-reference map-reference-right" x="1078" y="615" textAnchor="end">BAY OF FUNDY / 04</text>
    </svg>
  );
}