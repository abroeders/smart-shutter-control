"""Solar position (NOAA algorithm, about 0.1° accuracy) and the geometry of a window."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class SunPosition:
    azimuth: float  # degrees, 0 = north, 90 = east, 180 = south, 270 = west
    elevation: float  # degrees above the horizon (geometric, without refraction)

    @classmethod
    def at(cls, latitude: float, longitude: float, epoch: float) -> SunPosition:
        jd = epoch / 86400.0 + 2440587.5
        t = (jd - 2451545.0) / 36525.0
        l0 = (280.46646 + t * (36000.76983 + t * 0.0003032)) % 360
        m = 357.52911 + t * (35999.05029 - 0.0001537 * t)
        e = 0.016708634 - t * (0.000042037 + 0.0000001267 * t)
        mr = math.radians(m)
        c = (
            math.sin(mr) * (1.914602 - t * (0.004817 + 0.000014 * t))
            + math.sin(2 * mr) * (0.019993 - 0.000101 * t)
            + math.sin(3 * mr) * 0.000289
        )
        true_long = l0 + c
        omega = 125.04 - 1934.136 * t
        app_long = true_long - 0.00569 - 0.00478 * math.sin(math.radians(omega))
        eps0 = 23 + (26 + (21.448 - t * (46.815 + t * (0.00059 - t * 0.001813))) / 60) / 60
        eps = eps0 + 0.00256 * math.cos(math.radians(omega))
        decl = math.asin(math.sin(math.radians(eps)) * math.sin(math.radians(app_long)))
        y = math.tan(math.radians(eps / 2)) ** 2
        l0r = math.radians(l0)
        eq_time = 4 * math.degrees(
            y * math.sin(2 * l0r)
            - 2 * e * math.sin(mr)
            + 4 * e * y * math.sin(mr) * math.cos(2 * l0r)
            - 0.5 * y * y * math.sin(4 * l0r)
            - 1.25 * e * e * math.sin(2 * mr)
        )
        minutes = (epoch % 86400) / 60.0
        true_solar = (minutes + eq_time + 4 * longitude) % 1440
        hour_angle = true_solar / 4 - 180 if true_solar / 4 >= 0 else true_solar / 4 + 180
        lat, ha = math.radians(latitude), math.radians(hour_angle)
        cos_zenith = math.sin(lat) * math.sin(decl) + math.cos(lat) * math.cos(decl) * math.cos(ha)
        zenith = math.acos(max(-1.0, min(1.0, cos_zenith)))
        elevation = 90 - math.degrees(zenith)
        denom = math.cos(lat) * math.sin(zenith)
        if abs(denom) < 1e-9:
            azimuth = 180.0 if latitude > 0 else 0.0
        else:
            cos_az = (math.sin(lat) * math.cos(zenith) - math.sin(decl)) / denom
            az = math.degrees(math.acos(max(-1.0, min(1.0, cos_az))))
            azimuth = (az + 180) % 360 if hour_angle > 0 else (540 - az) % 360
        return cls(azimuth, elevation)


@dataclass(frozen=True)
class WindowGeometry:
    azimuth: float  # outward normal of the window, degrees like SunPosition.azimuth
    tilt: float = 90.0  # from the horizontal: 90 = vertical
    min_elevation: float = 0.0
    max_elevation: float = 90.0

    def incidence(self, sun: SunPosition) -> float:
        """Angle between the sun and the window normal, degrees (0 = straight on, ≥ 90 = behind)."""
        a, b = math.radians(sun.elevation), math.radians(self.tilt)
        cos_i = math.sin(a) * math.cos(b) + math.cos(a) * math.sin(b) * math.cos(
            math.radians(sun.azimuth - self.azimuth)
        )
        return math.degrees(math.acos(max(-1.0, min(1.0, cos_i))))

    def sun_on(self, sun: SunPosition, max_incidence: float = 85.0) -> bool:
        return (
            sun.elevation > 0
            and self.min_elevation <= sun.elevation <= self.max_elevation
            and self.incidence(sun) < max_incidence
        )
