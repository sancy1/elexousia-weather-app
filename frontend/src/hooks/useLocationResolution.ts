/**
 * useLocationResolution Hook
 * Automatic location state machine:
 *   initializing → saved precise → granted-permission silent precise → IP estimate → needs_manual
 * London is never a default — it only appears if the user explicitly picks it.
 */

import { useState, useEffect, useCallback } from "react";
import { useAutoDetect } from "@/hooks/useAutoDetect";
import { weatherApi, type Coords } from "@/lib/weather";

export type LocationStatus =
  | "initializing"
  | "resolved_precise"
  | "resolved_approximate"
  | "resolved_manual"
  | "needs_manual";

const SAVED_LOCATION_KEY = "elexousia_last_location";
const GEO_DENIED_KEY = "elexousia_geo_denied";

interface SavedLocation {
  lat: number;
  lon: number;
  label: string;
  city?: string;
}

function readSavedLocation(): SavedLocation | null {
  try {
    const raw = window.localStorage.getItem(SAVED_LOCATION_KEY);
    if (!raw) return null;
    const saved = JSON.parse(raw) as SavedLocation;
    if (
      typeof saved.lat === "number" &&
      typeof saved.lon === "number" &&
      saved.label
    ) {
      return saved;
    }
  } catch {
    /* malformed storage */
  }
  return null;
}

async function geolocationPermissionGranted(): Promise<boolean> {
  try {
    if (!navigator.permissions?.query) return false;
    const perm = await navigator.permissions.query({
      name: "geolocation" as PermissionName,
    });
    return perm.state === "granted";
  } catch {
    return false;
  }
}

export function useLocationResolution() {
  const [city, setCity] = useState<string>("");
  const [locationStatus, setLocationStatus] = useState<LocationStatus>("initializing");
  const [ipLookupEnabled, setIpLookupEnabled] = useState(false);
  const [coords, setCoords] = useState<Coords | null>(null);
  const [locationLabel, setLocationLabel] = useState<string | null>(null);
  const [geoLoading, setGeoLoading] = useState(false);
  const [geoError, setGeoError] = useState<string | null>(null);

  const { data: autoData, error: autoError } = useAutoDetect(ipLookupEnabled);

  // Apply a precise coordinate fix: reverse-geocode, set city, persist consent.
  const applyPrecise = useCallback(async (lat: number, lon: number) => {
    const data = await weatherApi.getNearbyWeather(lat, lon);
    setCoords({ lat, lon });
    setLocationLabel(data.location_label);
    setCity(data.city);
    setLocationStatus("resolved_precise");
    try {
      window.localStorage.setItem(
        SAVED_LOCATION_KEY,
        JSON.stringify({ lat, lon, label: data.location_label, city: data.city })
      );
      window.localStorage.removeItem(GEO_DENIED_KEY);
    } catch {
      /* storage unavailable — fine */
    }
  }, []);

  // ── Resolution state machine (runs once on mount) ──
  useEffect(() => {
    let cancelled = false;
    (async () => {
      // 1. Previously approved precise location — restore silently.
      const saved = readSavedLocation();
      if (saved) {
        try {
          await applyPrecise(saved.lat, saved.lon);
          return;
        } catch {
          /* stale saved fix — fall through to IP */
        }
      }

      // 2. Permission already granted → silent precise fix (no prompt).
      //    IP lookup runs in parallel as fallback; precise wins if it arrives.
      const granted = await geolocationPermissionGranted();
      if (granted && "geolocation" in navigator) {
        setIpLookupEnabled(true);
        navigator.geolocation.getCurrentPosition(
          (pos) => {
            if (cancelled) return;
            applyPrecise(pos.coords.latitude, pos.coords.longitude).catch(() => {
              /* precise failed — IP estimate (already running) takes over */
            });
          },
          () => {
            /* IP fallback already enabled */
          },
          { enableHighAccuracy: false, timeout: 8000, maximumAge: 300000 }
        );
        return;
      }

      // 3. No precise permission → automatic IP-based estimate.
      setIpLookupEnabled(true);
    })();
    return () => {
      cancelled = true;
    };
  }, [applyPrecise]);

  // IP estimate resolved → approximate location (only while still initializing,
  // or recovering from needs_manual if a retry succeeds).
  useEffect(() => {
    if (!autoData?.city) return;
    if (locationStatus !== "initializing" && locationStatus !== "needs_manual") return;
    setCity(autoData.city);
    setLocationStatus("resolved_approximate");
  }, [autoData, locationStatus]);

  // IP lookup failed → neutral "choose your location" (no forced London).
  useEffect(() => {
    if (autoError && locationStatus === "initializing") {
      setLocationStatus("needs_manual");
    }
  }, [autoError, locationStatus]);

  // Explicit user action — request precise device location.
  const handleLocate = useCallback(() => {
    if (!("geolocation" in navigator)) {
      setGeoError("Location isn't supported by this browser.");
      return;
    }
    setGeoLoading(true);
    setGeoError(null);
    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        try {
          await applyPrecise(pos.coords.latitude, pos.coords.longitude);
        } catch {
          setGeoError("Couldn't load weather for your location. Try searching manually.");
          setIpLookupEnabled(true);
        } finally {
          setGeoLoading(false);
        }
      },
      (err) => {
        setGeoLoading(false);
        if (err.code === err.PERMISSION_DENIED) {
          try {
            window.localStorage.setItem(GEO_DENIED_KEY, "1");
          } catch {
            /* ignore */
          }
          setGeoError("Location access was blocked. You can still search for any city.");
          setIpLookupEnabled(true);
        } else if (err.code === err.TIMEOUT) {
          setGeoError("Location request timed out. Try again or search manually.");
        } else {
          setGeoError("Couldn't determine your location. Try searching manually.");
        }
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 300000 }
    );
  }, [applyPrecise]);

  // Manual city selection — always available, exits any auto state.
  const selectCity = useCallback((next: string) => {
    setCoords(null);
    setLocationLabel(null);
    setGeoError(null);
    setCity(next);
    setLocationStatus("resolved_manual");
  }, []);

  return {
    city,
    setCity,
    locationStatus,
    coords,
    locationLabel,
    geoLoading,
    geoError,
    handleLocate,
    selectCity,
  };
}
