import { useEffect, useState } from 'react';
import Keycloak from 'keycloak-js';
import {
  Activity,
  Anchor,
  Clock3,
  Compass,
  LogOut,
  MapPin,
  PackageCheck,
  Radar,
  RefreshCw,
  Search,
  Ship as ShipIcon,
  Signal,
  Waves,
  Wind,
} from 'lucide-react';
import { ApiError, fetchShips, type Ship } from './api';
import RadarMap from './RadarMap';

const keycloak = new Keycloak({
  url: import.meta.env.VITE_KEYCLOAK_URL ?? 'https://auth.ships.damoverflow.com',
  realm: import.meta.env.VITE_KEYCLOAK_REALM ?? 'controller-plus',
  clientId: import.meta.env.VITE_KEYCLOAK_CLIENT_ID ?? 'controller-plus-ui',
});

let authenticationTask: Promise<boolean> | undefined;

function initializeAuthentication() {
  authenticationTask ??= keycloak.init({
    onLoad: 'login-required',
    pkceMethod: 'S256',
    checkLoginIframe: false,
  });
  return authenticationTask;
}

keycloak.onTokenExpired = () => {
  void keycloak.updateToken(30).catch(() => keycloak.login());
};

type AuthState = 'checking' | 'ready' | 'error';

function coordinate(value: number, positive: string, negative: string) {
  return `${Math.abs(value).toFixed(4)} ${value >= 0 ? positive : negative}`;
}

function statusClass(status: string) {
  if (status === 'Assist') return 'status-assist';
  if (status === 'Surveying') return 'status-surveying';
  if (status === 'Approaching') return 'status-approaching';
  return 'status-underway';
}

export default function App() {
  const [authState, setAuthState] = useState<AuthState>('checking');
  const [authError, setAuthError] = useState('');
  const [operator, setOperator] = useState('Operator');
  const [ships, setShips] = useState<Ship[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [clock, setClock] = useState(new Date());
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const [connectionError, setConnectionError] = useState('');
  const [initialLoad, setInitialLoad] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let active = true;
    void initializeAuthentication()
      .then((authenticated) => {
        if (!active) return;
        if (!authenticated) throw new Error('Authentication was not completed.');
        const token = keycloak.tokenParsed as { preferred_username?: string; name?: string } | undefined;
        setOperator(token?.preferred_username ?? token?.name ?? 'Operator');
        setAuthState('ready');
      })
      .catch((error: unknown) => {
        if (!active) return;
        setAuthError(error instanceof Error ? error.message : 'Identity service is unavailable.');
        setAuthState('error');
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const timer = window.setInterval(() => setClock(new Date()), 1000);
    return () => window.clearInterval(timer);
  }, []);

  useEffect(() => {
    if (authState !== 'ready') return;

    let disposed = false;
    let requestActive = false;
    let controller: AbortController | undefined;

    const refreshFleet = async () => {
      if (requestActive) return;
      requestActive = true;
      controller = new AbortController();
      setRefreshing(true);

      try {
        await keycloak.updateToken(30);
        if (!keycloak.token) throw new Error('Access token is not available.');
        const nextShips = await fetchShips(keycloak.token, controller.signal);
        if (disposed) return;
        setShips(nextShips);
        setLastUpdated(new Date());
        setConnectionError('');
      } catch (error) {
        if (disposed || (error instanceof DOMException && error.name === 'AbortError')) return;
        if (error instanceof ApiError && error.status === 401) {
          setConnectionError('Access denied by the ship API.');
        } else {
          setConnectionError(error instanceof Error ? error.message : 'Ship feed is unavailable.');
        }
      } finally {
        requestActive = false;
        if (!disposed) {
          setRefreshing(false);
          setInitialLoad(false);
        }
      }
    };

    void refreshFleet();
    const timer = window.setInterval(() => void refreshFleet(), 10_000);
    return () => {
      disposed = true;
      window.clearInterval(timer);
      controller?.abort();
    };
  }, [authState, refreshKey]);

  useEffect(() => {
    if (ships.length > 0 && !ships.some((ship) => ship.id === selectedId)) {
      setSelectedId(ships[0].id);
    }
  }, [ships, selectedId]);

  if (authState !== 'ready') {
    return (
      <main className="auth-gate">
        <div className="auth-gate-mark"><Anchor size={25} strokeWidth={1.7} /></div>
        <div className="auth-gate-copy">
          <p className="eyebrow">CONTROLLER PLUS / SECURE ACCESS</p>
          <h1>{authState === 'checking' ? 'Opening operations link' : 'Identity link unavailable'}</h1>
          <p>{authState === 'checking' ? 'CONTACTING AUTHORITY / CONTROLLER-PLUS' : authError}</p>
          {authState === 'error' && (
            <button className="button-primary" type="button" onClick={() => window.location.reload()}>
              <RefreshCw size={15} /> Retry connection
            </button>
          )}
        </div>
        <div className="auth-gate-rings" aria-hidden="true" />
      </main>
    );
  }

  const selectedShip = ships.find((ship) => ship.id === selectedId) ?? null;
  const filteredShips = ships.filter((ship) => {
    const query = search.trim().toLowerCase();
    return !query || `${ship.name} ${ship.callSign} ${ship.destination} ${ship.mmsi}`.toLowerCase().includes(query);
  });
  const movingShips = ships.filter((ship) => ship.speedKnots >= 4).length;
  const slowShips = ships.length - movingShips;
  const highLoadShips = ships.filter((ship) => ship.cargoPercent >= 75).length;
  const utcTime = new Intl.DateTimeFormat('en-GB', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    timeZone: 'UTC',
  }).format(clock);

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#fleet" aria-label="Controller Plus fleet picture">
          <span className="brand-mark"><ShipIcon size={21} strokeWidth={1.7} /></span>
          <span className="brand-copy">
            <strong>Controller Plus</strong>
            <small>MARITIME OPERATIONS</small>
          </span>
        </a>
        <div className="topbar-right">
          <span className="location-chip"><MapPin size={14} /> SAINT JOHN / BAY OF FUNDY</span>
          <span className={`feed-indicator${connectionError ? ' is-degraded' : ''}`}>
            <span className="feed-dot" />
            {connectionError ? 'LINK DEGRADED' : initialLoad ? 'LINKING' : 'LIVE FEED'}
          </span>
          <span className="utc-clock"><Clock3 size={14} /> {utcTime} UTC</span>
          <button
            className={`icon-button${refreshing ? ' is-spinning' : ''}`}
            type="button"
            aria-label="Refresh ship positions"
            title="Refresh positions"
            onClick={() => setRefreshKey((value) => value + 1)}
          >
            <RefreshCw size={16} />
          </button>
          <span className="operator-chip"><span className="operator-avatar">{operator.slice(0, 1).toUpperCase()}</span>{operator}</span>
          <button
            className="icon-button signout-button"
            type="button"
            aria-label="Sign out"
            title="Sign out"
            onClick={() => void keycloak.logout({ redirectUri: window.location.origin })}
          >
            <LogOut size={16} />
          </button>
        </div>
      </header>

      <main id="fleet" className="main-content">
        <section className="page-heading" aria-labelledby="page-title">
          <div>
            <p className="eyebrow"><span className="eyebrow-rule" /> TRAFFIC SURVEILLANCE / SAINT JOHN</p>
            <h1 id="page-title">Fleet picture <span>04</span></h1>
          </div>
          <div className="sync-note">
            <span className="sync-label">LAST POSITION REPORT</span>
            <strong>{lastUpdated ? `${new Intl.DateTimeFormat('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit', timeZone: 'UTC' }).format(lastUpdated)} UTC` : 'AWAITING FEED'}</strong>
          </div>
        </section>

        <section className="telemetry-strip" aria-label="Fleet summary">
          <div className="telemetry-item">
            <span className="telemetry-icon"><Radar size={16} /></span>
            <span className="telemetry-copy"><small>TRACKS</small><strong>{String(ships.length).padStart(2, '0')}</strong></span>
            <span className="telemetry-detail">ACTIVE</span>
          </div>
          <div className="telemetry-item">
            <span className="telemetry-icon telemetry-icon-green"><Activity size={16} /></span>
            <span className="telemetry-copy"><small>UNDERWAY</small><strong>{String(movingShips).padStart(2, '0')}</strong></span>
            <span className="telemetry-detail">OVER 4 KN</span>
          </div>
          <div className="telemetry-item">
            <span className="telemetry-icon telemetry-icon-copper"><Anchor size={16} /></span>
            <span className="telemetry-copy"><small>SLOW / ASSIST</small><strong>{String(slowShips).padStart(2, '0')}</strong></span>
            <span className="telemetry-detail">LOW SPEED</span>
          </div>
          <div className="telemetry-item telemetry-item-last">
            <span className="telemetry-icon telemetry-icon-gold"><PackageCheck size={16} /></span>
            <span className="telemetry-copy"><small>HEAVY LOAD</small><strong>{String(highLoadShips).padStart(2, '0')}</strong></span>
            <span className="telemetry-detail">75%+ CARGO</span>
          </div>
        </section>

        {connectionError && (
          <div className="connection-alert" role="alert">
            <Signal size={16} />
            <span>DATA LINK INTERRUPTED</span>
            <small>{connectionError}</small>
            <button type="button" onClick={() => setRefreshKey((value) => value + 1)}>Retry feed</button>
          </div>
        )}

        <section className="operations-grid" aria-label="Ship operations">
          <aside className="roster-panel" aria-labelledby="roster-title">
            <div className="panel-heading">
              <div>
                <p className="panel-kicker">AIS / 01</p>
                <h2 id="roster-title">Vessel manifest</h2>
              </div>
              <span className="count-badge">{String(ships.length).padStart(2, '0')}</span>
            </div>
            <label className="search-field">
              <Search size={15} aria-hidden="true" />
              <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Find vessel" aria-label="Search vessels" />
              <kbd>/</kbd>
            </label>
            <div className="roster-label-row"><span>VESSEL / CALL SIGN</span><span>SOG</span></div>
            <ul className="vessel-list">
              {filteredShips.map((ship) => (
                <li key={ship.id}>
                  <button
                    className={`vessel-row${selectedId === ship.id ? ' is-selected' : ''}`}
                    type="button"
                    aria-pressed={selectedId === ship.id}
                    onClick={() => setSelectedId(ship.id)}
                  >
                    <span className="vessel-row-icon"><ShipIcon size={17} strokeWidth={1.7} /></span>
                    <span className="vessel-row-main">
                      <strong>{ship.name}</strong>
                      <small><span className={`status-dot ${statusClass(ship.status)}`} />{ship.callSign} / {ship.status}</small>
                    </span>
                    <span className="vessel-row-speed">{ship.speedKnots.toFixed(1)}<small>KN</small></span>
                  </button>
                </li>
              ))}
              {filteredShips.length === 0 && <li className="empty-roster">NO MATCHING VESSELS</li>}
            </ul>
            <div className="roster-footer">
              <span><span className="feed-dot" /> {ships.length} TRACKS IN AREA</span>
              <Compass size={15} />
            </div>
          </aside>

          <section className="map-panel" aria-labelledby="map-title">
            <div className="map-panel-header">
              <div>
                <p className="panel-kicker">LIVE PLOT / AIS OVERLAY</p>
                <h2 id="map-title">Saint John Harbour <span>45.2 N / 66.1 W</span></h2>
              </div>
              <div className="map-tools">
                <span className="range-tag"><Waves size={14} /> 12 NM</span>
                <span className="map-status"><span className="feed-dot" /> AUTO SCAN</span>
              </div>
            </div>
            <div className="map-stage">
              <RadarMap ships={ships} selectedId={selectedId} onSelect={setSelectedId} />
              {initialLoad && ships.length === 0 && <div className="map-loading">ACQUIRING TARGETS...</div>}
            </div>
            <div className="map-footer">
              <div className="map-legend"><span className="legend-mark legend-active" /> ACTIVE TRACK <span className="legend-mark legend-selected" /> SELECTED <span className="legend-line" /> COURSE VECTOR</div>
              <span className="map-scale"><Wind size={14} /> COG / SOG</span>
            </div>
          </section>

          <aside className="detail-panel" aria-labelledby="detail-title">
            <div className="panel-heading detail-heading">
              <div>
                <p className="panel-kicker" title={selectedShip?.id}>TRACK / {selectedShip ? selectedShip.id.slice(0, 8).toUpperCase() : '---'}</p>
                <h2 id="detail-title">Vessel data</h2>
              </div>
              <span className="detail-signal"><Signal size={16} /></span>
            </div>
            {selectedShip ? (
              <>
                <div className="selected-vessel">
                  <span className="selected-type">{selectedShip.vesselType.toUpperCase()}</span>
                  <h3>{selectedShip.name}</h3>
                  <p>{selectedShip.callSign} <span>/</span> {selectedShip.mmsi}</p>
                  <div className={`detail-status ${statusClass(selectedShip.status)}`}>
                    <span className="status-dot" /> {selectedShip.status.toUpperCase()}
                  </div>
                </div>
                <div className="detail-metrics">
                  <div className="detail-metric">
                    <span><Activity size={14} /> SPEED</span>
                    <strong>{selectedShip.speedKnots.toFixed(1)} <small>KN</small></strong>
                  </div>
                  <div className="detail-metric">
                    <span><Compass size={14} /> COURSE</span>
                    <strong>{String(selectedShip.heading).padStart(3, '0')} <small>DEG</small></strong>
                  </div>
                </div>
                <div className="coordinate-readout">
                  <span>POSITION / WGS 84</span>
                  <strong>{coordinate(selectedShip.latitude, 'N', 'S')}</strong>
                  <strong>{coordinate(selectedShip.longitude, 'E', 'W')}</strong>
                </div>
                <div className="destination-row">
                  <span>DESTINATION</span>
                  <strong><MapPin size={14} /> {selectedShip.destination}</strong>
                </div>
                <div className="cargo-block">
                  <div><span>CARGO LOAD</span><strong>{selectedShip.cargoPercent}%</strong></div>
                  <div className="cargo-track"><span style={{ width: `${selectedShip.cargoPercent}%` }} /></div>
                </div>
                <div className="detail-bottom">
                  <span>LAST SIGNAL</span>
                  <strong>{new Intl.DateTimeFormat('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit', timeZone: 'UTC' }).format(new Date(selectedShip.updatedAt))} UTC</strong>
                </div>
              </>
            ) : (
              <div className="detail-empty"><ShipIcon size={22} /><span>SELECT A VESSEL TRACK</span></div>
            )}
          </aside>
        </section>

        <footer className="app-footer">
          <span><span className="footer-mark">CP</span> CONTROLLER PLUS / NAVAL TRAFFIC SERVICE</span>
          <span><Clock3 size={13} /> POSITIONS REFRESH EVERY 10 SEC</span>
          <span>SIMULATION FEED / NOT FOR NAVIGATION</span>
        </footer>
      </main>
    </div>
  );
}