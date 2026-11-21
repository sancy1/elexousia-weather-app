/**
 * Mocked tests for useLocationResolution — the automatic location state machine.
 * No live network calls: useAutoDetect and weatherApi are fully mocked.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { useLocationResolution } from "@/hooks/useLocationResolution";
import { useAutoDetect } from "@/hooks/useAutoDetect";
import { weatherApi } from "@/lib/weather";

vi.mock("@/hooks/useAutoDetect", () => ({ useAutoDetect: vi.fn() }));
vi.mock("@/lib/weather", () => ({
  weatherApi: { getNearbyWeather: vi.fn() },
}));

const mockedAutoDetect = vi.mocked(useAutoDetect);
const mockedNearby = vi.mocked(weatherApi.getNearbyWeather);

// Controllable auto-detect state
let autoState: { data?: { city?: string } | undefined; error?: unknown };
let lastEnabled: boolean | undefined;

const NEARBY_OK = {
  location_label: "Magodo, Mile 12, Lagos, Nigeria",
  city: "Lagos",
  country: "Nigeria",
} as never;

function setPermission(state: "granted" | "denied" | "prompt" | "unsupported") {
  if (state === "unsupported") {
    // @ts-expect-error simulate missing Permissions API
    delete navigator.permissions;
    return;
  }
  Object.defineProperty(navigator, "permissions", {
    configurable: true,
    value: {
      query: vi.fn().mockResolvedValue({ state }),
    },
  });
}

function setGeolocation(
  impl?: (success: PositionCallback, error?: PositionErrorCallback) => void
) {
  Object.defineProperty(navigator, "geolocation", {
    configurable: true,
    value: impl
      ? { getCurrentPosition: vi.fn(impl) }
      : undefined,
  });
}

beforeEach(() => {
  window.localStorage.clear();
  autoState = { data: undefined, error: undefined };
  lastEnabled = undefined;
  mockedAutoDetect.mockImplementation((enabled = true) => {
    lastEnabled = enabled;
    return { data: autoState.data, error: autoState.error } as never;
  });
  mockedNearby.mockResolvedValue(NEARBY_OK);
  setPermission("denied"); // default: no precise permission → IP path
  setGeolocation(); // default: no geolocation API
});

afterEach(() => {
  vi.clearAllMocks();
});

describe("useLocationResolution", () => {
  it("starts in initializing with empty city — never defaults to London", () => {
    const { result } = renderHook(() => useLocationResolution());
    expect(result.current.locationStatus).toBe("initializing");
    expect(result.current.city).toBe("");
  });

  it("IP estimate success → resolved_approximate with detected city", async () => {
    const { result, rerender } = renderHook(() => useLocationResolution());

    // IP lookup gets enabled automatically (no permission)
    await waitFor(() => expect(lastEnabled).toBe(true));

    autoState = { data: { city: "Lagos" } };
    rerender();

    await waitFor(() =>
      expect(result.current.locationStatus).toBe("resolved_approximate")
    );
    expect(result.current.city).toBe("Lagos");
    expect(result.current.city).not.toBe("London");
  });

  it("IP lookup failure → needs_manual (no forced London)", async () => {
    const { result, rerender } = renderHook(() => useLocationResolution());
    await waitFor(() => expect(lastEnabled).toBe(true));

    autoState = { error: new Error("ip lookup failed") };
    rerender();

    await waitFor(() =>
      expect(result.current.locationStatus).toBe("needs_manual")
    );
    expect(result.current.city).toBe("");
  });

  it("saved precise location → resolved_precise without IP lookup", async () => {
    window.localStorage.setItem(
      "elexousia_last_location",
      JSON.stringify({ lat: 6.6, lon: 3.3, label: "Magodo, Lagos", city: "Lagos" })
    );

    const { result } = renderHook(() => useLocationResolution());

    await waitFor(() =>
      expect(result.current.locationStatus).toBe("resolved_precise")
    );
    expect(result.current.city).toBe("Lagos");
    expect(result.current.locationLabel).toBe("Magodo, Mile 12, Lagos, Nigeria");
    expect(result.current.coords).toEqual({ lat: 6.6, lon: 3.3 });
    // IP lookup must NOT be enabled — precise restore short-circuits it
    expect(lastEnabled).toBe(false);
    expect(mockedNearby).toHaveBeenCalledWith(6.6, 3.3);
  });

  it("granted permission → silent precise fix without user click", async () => {
    setPermission("granted");
    setGeolocation((success) => {
      success({
        coords: { latitude: 6.61, longitude: 3.36 },
      } as GeolocationPosition);
    });

    const { result } = renderHook(() => useLocationResolution());

    await waitFor(() =>
      expect(result.current.locationStatus).toBe("resolved_precise")
    );
    expect(result.current.city).toBe("Lagos");
    expect(result.current.locationLabel).toContain("Magodo");
    // IP runs in parallel as fallback
    expect(lastEnabled).toBe(true);
  });

  it("granted permission but geolocation fails → IP estimate takes over", async () => {
    setPermission("granted");
    setGeolocation((_success, error) => {
      error?.({
        code: 1,
        PERMISSION_DENIED: 1,
        POSITION_UNAVAILABLE: 2,
        TIMEOUT: 3,
        message: "denied",
      } as GeolocationPositionError);
    });

    const { result, rerender } = renderHook(() => useLocationResolution());
    await waitFor(() => expect(lastEnabled).toBe(true));

    autoState = { data: { city: "Lagos" } };
    rerender();

    await waitFor(() =>
      expect(result.current.locationStatus).toBe("resolved_approximate")
    );
    expect(result.current.city).toBe("Lagos");
  });

  it("handleLocate success → resolved_precise and persists consent", async () => {
    setGeolocation((success) => {
      success({
        coords: { latitude: 6.62, longitude: 3.37 },
      } as GeolocationPosition);
    });

    const { result } = renderHook(() => useLocationResolution());
    await waitFor(() => expect(lastEnabled).toBe(true)); // IP path first

    await act(async () => {
      result.current.handleLocate();
    });

    await waitFor(() =>
      expect(result.current.locationStatus).toBe("resolved_precise")
    );
    expect(result.current.coords).toEqual({ lat: 6.62, lon: 3.37 });
    const saved = JSON.parse(
      window.localStorage.getItem("elexousia_last_location")!
    );
    expect(saved.lat).toBe(6.62);
    expect(saved.label).toContain("Magodo");
  });

  it("handleLocate permission denied → geoError, IP fallback enabled, denial remembered", async () => {
    setGeolocation((_success, error) => {
      error?.({
        code: 1,
        PERMISSION_DENIED: 1,
        POSITION_UNAVAILABLE: 2,
        TIMEOUT: 3,
        message: "denied",
      } as GeolocationPositionError);
    });

    const { result } = renderHook(() => useLocationResolution());
    await waitFor(() => expect(lastEnabled).toBe(true));

    await act(async () => {
      result.current.handleLocate();
    });

    await waitFor(() => expect(result.current.geoError).toBeTruthy());
    expect(result.current.geoError).toContain("blocked");
    expect(window.localStorage.getItem("elexousia_geo_denied")).toBe("1");
  });

  it("selectCity → resolved_manual and clears coords/label", async () => {
    const { result } = renderHook(() => useLocationResolution());
    await waitFor(() => expect(lastEnabled).toBe(true));

    act(() => {
      result.current.selectCity("Paris");
    });

    expect(result.current.locationStatus).toBe("resolved_manual");
    expect(result.current.city).toBe("Paris");
    expect(result.current.coords).toBeNull();
    expect(result.current.locationLabel).toBeNull();
  });
});
