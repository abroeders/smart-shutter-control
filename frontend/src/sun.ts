// Where the sun is in the sky for a date and location (#34), for the sun's path in the view.

const J2000 = Date.UTC(2000, 0, 1, 12, 0, 0);
const RAD = Math.PI / 180;

const normalizeDegrees = (value: number): number => ((value % 360) + 360) % 360;

/** Low-precision solar position (about 0.5°): azimuth from the north, clockwise; elevation in degrees. */
export function sunPosition(date: Date, latitude: number, longitude: number): { azimuth: number; elevation: number } {
  const d = (date.getTime() - J2000) / 86400000;
  const meanAnomaly = normalizeDegrees(357.529 + 0.98560028 * d) * RAD;
  const meanLongitude = normalizeDegrees(280.459 + 0.98564736 * d);
  const eclipticLongitude = (meanLongitude + 1.915 * Math.sin(meanAnomaly) + 0.02 * Math.sin(2 * meanAnomaly)) * RAD;
  const obliquity = (23.439 - 0.00000036 * d) * RAD;
  const rightAscension = Math.atan2(Math.cos(obliquity) * Math.sin(eclipticLongitude), Math.cos(eclipticLongitude));
  const declination = Math.asin(Math.sin(obliquity) * Math.sin(eclipticLongitude));

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
  return { azimuth: normalizeDegrees(southAzimuth / RAD + 180), elevation: elevation / RAD };
}
