// What the moon's phase and place in the sky are for a date and location.

const J2000 = Date.UTC(2000, 0, 1, 12, 0, 0);
const SYNODIC_MONTH = 29.530588853;
const REFERENCE_NEW_MOON = Date.UTC(2000, 0, 6, 18, 14, 0);
const RAD = Math.PI / 180;

const normalizeDegrees = (value: number): number => ((value % 360) + 360) % 360;

export function moonPhase(date: Date): number {
  const elapsed = (date.getTime() - REFERENCE_NEW_MOON) / 86400000;
  return ((elapsed / SYNODIC_MONTH) % 1 + 1) % 1;
}

export function moonPosition(date: Date, latitude: number, longitude: number): { azimuth: number; elevation: number } {
  const d = (date.getTime() - J2000) / 86400000;
  const L = normalizeDegrees(218.316 + 13.176396 * d);
  const M = normalizeDegrees(134.963 + 13.064993 * d);
  const F = normalizeDegrees(93.272 + 13.229350 * d);
  const longitudeEcliptic = (L + 6.289 * Math.sin(M * RAD)) * RAD;
  const latitudeEcliptic = 5.128 * Math.sin(F * RAD) * RAD;

  const obliquity = 23.4397 * RAD;
  const sinObliquity = Math.sin(obliquity);
  const cosObliquity = Math.cos(obliquity);
  const sinLat = Math.sin(latitudeEcliptic);
  const cosLat = Math.cos(latitudeEcliptic);

  const xEquatorial = cosLat * Math.cos(longitudeEcliptic);
  const yEquatorial = cosLat * Math.sin(longitudeEcliptic) * cosObliquity - sinLat * sinObliquity;
  const zEquatorial = cosLat * Math.sin(longitudeEcliptic) * sinObliquity + sinLat * cosObliquity;
  const rightAscension = Math.atan2(yEquatorial, xEquatorial);
  const declination = Math.asin(zEquatorial);

  const latitudeRad = latitude * RAD;
  // local sidereal time: east longitudes are positive
  const localSidereal = normalizeDegrees(280.16 + 360.9856235 * d + longitude) * RAD;
  const hourAngle = localSidereal - rightAscension;
  const elevation = Math.asin(
    Math.sin(latitudeRad) * Math.sin(declination) +
    Math.cos(latitudeRad) * Math.cos(declination) * Math.cos(hourAngle),
  );
  // measured from the south, westward positive; + 180° gives the azimuth from the north, clockwise
  const southAzimuth = Math.atan2(
    Math.sin(hourAngle),
    Math.cos(hourAngle) * Math.sin(latitudeRad) - Math.tan(declination) * Math.cos(latitudeRad),
  );
  const azimuth = normalizeDegrees(southAzimuth / RAD + 180);

  return { azimuth, elevation: elevation / RAD };
}
