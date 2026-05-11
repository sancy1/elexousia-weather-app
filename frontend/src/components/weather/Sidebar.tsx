import { useEffect, useRef, useState } from "react";
import {
  CloudSun, Plus, Search, MapPin, Briefcase, Home, Plane,
  PanelLeftClose, PanelLeftOpen, X, Trash2,
} from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";
import { LoginButton } from "@/components/auth/LoginButton";
import { UserMenu } from "@/components/auth/UserMenu";
import { weatherApi } from "@/lib/weather";

interface SavedLocation {
  id: number;
  city_name: string;
  country_code: string;
  label: string;
  latitude: number;
  longitude: number;
  timezone: string;
  display_order: number;
  is_default: boolean;
}

interface SearchHistoryItem {
  id: number;
  user_id: number;
  city_name: string;
  country_code: string;
  searched_at: string;
  temperature: number | null;
  condition: string | null;
}

interface Props {
  activeId: string;
  onSelect: (id: string) => void;
  onCitySelect: (city: string) => void;
  mobileOpen?: boolean;
  onMobileClose?: () => void;
  currentCity?: string;
}

const formatSearchDate = (dateString: string): string => {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) return "Today";
  if (diffDays === 1) return "Yesterday";
  if (diffDays < 7) return `${diffDays} days ago`;
  return date.toLocaleDateString();
};

const labelIcon = (l: string) => {
  if (l === "Home") return Home;
  if (l === "Work") return Briefcase;
  return Plane;
};

const MIN_W = 220;
const MAX_W = 420;
const COLLAPSED_W = 68;

export function Sidebar({ activeId, onSelect, onCitySelect, mobileOpen, onMobileClose, currentCity }: Props) {
  const [width, setWidth] = useState(280);
  const [collapsed, setCollapsed] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [savedLocations, setSavedLocations] = useState<SavedLocation[]>([]);
  const [loadingLocations, setLoadingLocations] = useState(false);
  const [searchHistory, setSearchHistory] = useState<SearchHistoryItem[]>([]);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const [showAddLocation, setShowAddLocation] = useState(false);
  const [addLocationQuery, setAddLocationQuery] = useState("");
  const [addLocationLabel, setAddLocationLabel] = useState("Home");
  const dragging = useRef(false);
  const { user, loading } = useAuth();

  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      if (!dragging.current) return;
      const w = Math.min(MAX_W, Math.max(MIN_W, e.clientX));
      setWidth(w);
      if (collapsed) setCollapsed(false);
    };
    const onUp = () => {
      dragging.current = false;
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
  }, [collapsed]);

  useEffect(() => {
    if (user && !loading) {
      fetchSavedLocations();
      fetchSearchHistory();
    }
  }, [user, loading]);

  const startDrag = () => {
    dragging.current = true;
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  };

  // Sort saved locations: current city first, then by display_order
  const sortedSavedLocations = [...savedLocations].sort((a, b) => {
    if (currentCity) {
      const aMatch = a.city_name.toLowerCase() === currentCity.toLowerCase();
      const bMatch = b.city_name.toLowerCase() === currentCity.toLowerCase();
      if (aMatch && !bMatch) return -1;
      if (!aMatch && bMatch) return 1;
    }
    return a.display_order - b.display_order;
  });

  const effectiveWidth = collapsed ? COLLAPSED_W : width;

  const handleCitySelect = (city: string) => {
    console.log("Sidebar: City selected:", city);
    onCitySelect(city);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const query = searchQuery.trim();
    if (query) {
      console.log("Sidebar: Searching for:", query);
      onCitySelect(query);
      addToSearchHistory(query);
      setSearchQuery("");
    }
  };

  const addToSearchHistory = async (city: string) => {
    if (!user) {
      console.log("Search history: User not logged in, skipping save");
      return;
    }
    
    console.log("Search history: Adding to search history:", city);
    try {
      console.log("Search history: Calling API with:", { city_name: city, country_code: "" });
      
      // Fetch weather data to get temperature and condition
      let temperature: number | undefined;
      let condition: string | undefined;
      try {
        const weatherData = await weatherApi.getCurrentWeather(city);
        temperature = weatherData.temperature_c;
        condition = weatherData.condition;
        console.log("Search history: Weather data fetched:", { temperature, condition });
      } catch (error) {
        console.log("Search history: Could not fetch weather data, saving without temp/condition");
      }
      
      const result = await weatherApi.addSearchHistory({
        city_name: city,
        country_code: "",
        temperature,
        condition
      });
      console.log("Search history: API response:", result);
      await fetchSearchHistory();
    } catch (error: any) {
      console.error("Search history: Failed to add to search history:", error);
      console.error("Search history: Error details:", {
        message: error.message,
        detail: error.detail,
        status: error.status,
        stack: error.stack
      });
    }
  };

  const fetchSavedLocations = async () => {
    try {
      setLoadingLocations(true);
      console.log("Fetching saved locations...");
      const data = await weatherApi.getSavedLocations();
      console.log("Saved locations fetched:", data);
      setSavedLocations(data.locations);
    } catch (error: any) {
      console.error("Failed to fetch saved locations:", error);
    } finally {
      setLoadingLocations(false);
    }
  };

  const fetchSearchHistory = async () => {
    if (!user) return;
    
    try {
      setLoadingHistory(true);
      console.log("Fetching search history...");
      const data = await weatherApi.getSearchHistory();
      console.log("Search history fetched:", data);
      setSearchHistory(data);
    } catch (error: any) {
      console.error("Failed to fetch search history:", error);
    } finally {
      setLoadingHistory(false);
    }
  };

  const handleDeleteLocation = async (locationId: number) => {
    try {
      await weatherApi.deleteLocation(locationId);
      await fetchSavedLocations();
    } catch (error) {
      console.error("Failed to delete location:", error);
    }
  };

  const handleAddLocation = async () => {
    const city = addLocationQuery.trim();
    if (!city) {
      alert("Please enter a city name");
      return;
    }

    if (!user) {
      alert("Please log in to save locations");
      return;
    }

    console.log("Saved location: Attempting to save location:", { city, label: addLocationLabel, user: user.id });

    try {
      console.log("Saved location: Calling API with:", { city_name: city, country_code: "", label: addLocationLabel });
      const result = await weatherApi.saveLocation({
        city_name: city,
        country_code: "",
        label: addLocationLabel,
      });
      console.log("Saved location: API response:", result);
      await fetchSavedLocations();
      setAddLocationQuery("");
      setShowAddLocation(false);
      alert("Location saved successfully!");
    } catch (error: any) {
      console.error("Saved location: Failed to save location:", error);
      console.error("Saved location: Error details:", {
        message: error.message,
        detail: error.detail,
        status: error.status,
        stack: error.stack
      });
      let errorMsg = "Unknown error";
      if (error.detail) {
        errorMsg = error.detail;
      } else if (error.message) {
        errorMsg = error.message;
      } else if (typeof error === "string") {
        errorMsg = error;
      }
      alert(`Failed to save location: ${errorMsg}`);
    }
  };

  const handleDeleteSearchHistory = async (id: number) => {
    try {
      await weatherApi.deleteSearchHistory(id);
      await fetchSearchHistory();
    } catch (error) {
      console.error("Failed to delete search history item:", error);
    }
  };

  const handleClearSearchHistory = async () => {
    try {
      await weatherApi.clearSearchHistory();
      await fetchSearchHistory();
    } catch (error) {
      console.error("Failed to clear search history:", error);
    }
  };

  const content = (showLabels: boolean) => (
    <>
      <div className="flex items-center gap-2.5 px-4 h-[52px] border-b border-border shrink-0">
        <div className="h-8 w-8 shrink-0 rounded-lg bg-gradient-to-br from-primary to-primary-glow flex items-center justify-center shadow-[0_0_20px_-5px_var(--primary-glow)]">
          <CloudSun className="h-4 w-4 text-primary-foreground" strokeWidth={2.5} />
        </div>
        {showLabels && (
          <div className="flex flex-col leading-tight flex-1 min-w-0">
            <span className="text-[13px] font-semibold tracking-tight truncate">EL-Exousia</span>
            <span className="text-[10px] text-muted-foreground tracking-wider uppercase truncate">Weather Intel</span>
          </div>
        )}
        <button
          onClick={() => setCollapsed((c) => !c)}
          className="hidden md:flex h-7 w-7 items-center justify-center rounded-md hover:bg-accent text-muted-foreground hover:text-foreground transition-colors"
          title={collapsed ? "Expand" : "Collapse to icons"}
        >
          {collapsed ? <PanelLeftOpen className="h-3.5 w-3.5" /> : <PanelLeftClose className="h-3.5 w-3.5" />}
        </button>
        {onMobileClose && (
          <button
            onClick={onMobileClose}
            className="md:hidden h-7 w-7 flex items-center justify-center rounded-md hover:bg-accent"
          >
            <X className="h-4 w-4" />
          </button>
        )}
      </div>

      {showLabels && (
        <button
          onClick={() => setShowAddLocation(!showAddLocation)}
          className="mx-3 mt-3 flex items-center justify-center gap-2 h-10 rounded-lg bg-primary/10 hover:bg-primary/20 border border-primary/30 text-primary text-sm font-medium transition-all hover:shadow-[0_0_20px_-8px_var(--primary)] group"
          title="Add location"
        >
          <Plus className="h-4 w-4 transition-transform group-hover:rotate-90" />
          Add location
        </button>
      )}

      {showLabels && showAddLocation && (
        <div className="mx-3 mt-2 space-y-2">
          <input
            type="text"
            value={addLocationQuery}
            onChange={(e) => setAddLocationQuery(e.target.value)}
            placeholder="City name..."
            className="w-full h-9 px-3 rounded-lg bg-background/60 border border-border text-xs placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary/50 focus:border-primary/50 transition-all"
          />
          <select
            value={addLocationLabel}
            onChange={(e) => setAddLocationLabel(e.target.value)}
            className="w-full h-9 px-3 rounded-lg bg-background/60 border border-border text-xs focus:outline-none focus:ring-1 focus:ring-primary/50 focus:border-primary/50 transition-all"
          >
            <option value="Home">Home</option>
            <option value="Work">Work</option>
            <option value="Travel">Travel</option>
          </select>
          <button
            onClick={handleAddLocation}
            className="w-full h-9 rounded-lg bg-primary hover:bg-primary/90 text-primary-foreground text-xs font-medium transition-all"
          >
            Save location
          </button>
        </div>
      )}

      {showLabels && (
        <form onSubmit={handleSearch} className="mx-3 mt-3 relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search cities…"
            className="w-full h-9 pl-9 pr-3 rounded-lg bg-background/60 border border-border text-xs placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-primary/50 focus:border-primary/50 transition-all"
          />
        </form>
      )}

      <div className="flex-1 overflow-y-auto scrollbar-thin px-2 mt-4 pb-4">
        {showLabels && (
          <div className="px-2 mb-2 flex items-center justify-between">
            <span className="text-[10px] font-semibold tracking-[0.12em] text-muted-foreground uppercase">
              Search History
            </span>
            <button
              onClick={handleClearSearchHistory}
              className="text-[10px] text-muted-foreground hover:text-foreground transition-colors"
              title="Clear all"
            >
              Clear
            </button>
          </div>
        )}
        <div className="space-y-1">
          {loadingHistory ? (
            <div className="px-3 py-2 text-xs text-muted-foreground">Loading...</div>
          ) : searchHistory.length === 0 ? (
            <div className="px-3 py-2 text-xs text-muted-foreground">No search history</div>
          ) : (
            searchHistory.map((item) => {
              const active = item.id.toString() === activeId;
              if (!showLabels) {
                return (
                  <button
                    key={item.id}
                    onClick={() => {
                      onSelect(item.id.toString());
                      handleCitySelect(item.city_name);
                    }}
                    title={item.city_name}
                    className={`w-full flex justify-center py-2 rounded-lg transition-all group ${
                      active ? "bg-accent/80" : "hover:bg-accent/40"
                    }`}
                  >
                    <div className="h-7 w-7 rounded-md bg-secondary flex items-center justify-center text-[10px] font-semibold">
                      {item.city_name.slice(0, 2).toUpperCase()}
                    </div>
                  </button>
                );
              }
              return (
                <button
                  key={item.id}
                  onClick={() => {
                    onSelect(item.id.toString());
                    handleCitySelect(item.city_name);
                  }}
                  className={`w-full flex items-center gap-3 px-3 py-1.5 rounded-lg transition-all group relative ${
                    active ? "bg-accent/80 shadow-[inset_0_0_0_1px_var(--border)]" : "hover:bg-accent/40"
                  }`}
                >
                  {active && (
                    <span className="absolute left-0 top-1/2 -translate-y-1/2 h-6 w-0.5 rounded-r bg-primary-glow" />
                  )}
                  <div className="flex-1 text-left min-w-0">
                    <div className="text-[13px] font-medium truncate">{item.city_name}</div>
                    <div className="text-[11px] text-muted-foreground mt-0.5 truncate">
                      {formatSearchDate(item.searched_at)}
                      {item.temperature && item.condition && (
                        <span className="ml-2">· {item.temperature}°C · {item.condition}</span>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteSearchHistory(item.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 hover:bg-accent rounded transition-all"
                    title="Remove"
                  >
                    <Trash2 className="h-3 w-3 text-muted-foreground" />
                  </button>
                </button>
              );
            })
          )}
        </div>

        <div className={`mt-6 mb-2 px-2 ${showLabels ? "" : "hidden"}`}>
          <span className="text-[10px] font-semibold tracking-[0.12em] text-muted-foreground uppercase">
            Saved Locations
          </span>
        </div>
        <div className={`space-y-1 ${showLabels ? "" : "mt-4"}`}>
          {loadingLocations ? (
            <div className="px-3 py-2 text-xs text-muted-foreground">Loading...</div>
          ) : savedLocations.length === 0 ? (
            <div className="px-3 py-2 text-xs text-muted-foreground">No saved locations</div>
          ) : (
            savedLocations.map((loc) => {
              const Icon = labelIcon(loc.label);
              if (!showLabels) {
                return (
                  <button
                    key={loc.id}
                    onClick={() => handleCitySelect(loc.city_name)}
                    title={loc.city_name}
                    className="w-full flex justify-center py-2 rounded-lg hover:bg-accent/40 transition-all group"
                  >1
                    <div className="h-7 w-7 rounded-md bg-secondary flex items-center justify-center">
                      <Icon className="h-3.5 w-3.5 text-muted-foreground" />
                    </div>
                  </button>
                );
              }
              return (
                <button
                  key={loc.id}
                  onClick={() => handleCitySelect(loc.city_name)}
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-accent/40 transition-all group"
                >
                  <div className="h-7 w-7 rounded-md bg-secondary flex items-center justify-center">
                    <Icon className="h-3.5 w-3.5 text-muted-foreground" />
                  </div>
                  <div className="flex-1 text-left min-w-0">
                    <div className="text-[13px] font-medium truncate">{loc.city_name}</div>
                    <div className="text-[10px] text-muted-foreground truncate">{loc.label}</div>
                  </div>
                  <MapPin className="h-3 w-3 text-muted-foreground" />
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDeleteLocation(loc.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 hover:bg-accent rounded transition-all"
                    title="Remove"
                  >
                    <Trash2 className="h-3 w-3 text-muted-foreground" />
                  </button>
                </button>
              );
            })
          )}
        </div>
      </div>

      <div className="border-t border-border p-3 shrink-0">
        {!loading && user ? (
          <div className={`flex items-center gap-3 ${showLabels ? "" : "justify-center"}`}>
            <div className="h-8 w-8 rounded-full bg-gradient-to-br from-primary-glow to-primary flex items-center justify-center text-[11px] font-semibold shrink-0 overflow-hidden">
              {user.avatar_url ? (
                <img src={user.avatar_url} alt={user.name} className="h-full w-full object-cover" />
              ) : (
                <span>{user.initials}</span>
              )}
            </div>
            {showLabels && (
              <>
                <div className="flex-1 min-w-0">
                  <div className="text-[12px] font-medium truncate">{user.name}</div>
                  <div className="text-[10px] text-muted-foreground">{user.email}</div>
                </div>
                <UserMenu />
              </>
            )}
          </div>
        ) : !loading && !user ? (
          <div className={showLabels ? "" : "justify-center"}>
            <LoginButton variant="default" />
          </div>
        ) : null}
      </div>
    </>
  );

  return (
    <>
      <aside
        className="hidden md:flex relative shrink-0 flex-col border-r border-border bg-background-elevated/40 backdrop-blur-xl transition-[width] duration-200"
        style={{ width: effectiveWidth }}
      >
        {content(!collapsed)}
        {!collapsed && (
          <div
            onMouseDown={startDrag}
            onDoubleClick={() => setWidth(280)}
            className="absolute top-0 right-0 h-full w-1.5 cursor-col-resize group z-30"
          >
            <div className="absolute inset-y-0 right-0 w-px bg-border group-hover:bg-primary-glow transition-colors" />
            <div className="absolute top-1/2 -translate-y-1/2 right-[-3px] h-10 w-1.5 rounded-full bg-primary/0 group-hover:bg-primary/40 transition-colors" />
          </div>
        )}
      </aside>

      {mobileOpen && (
        <div className="md:hidden fixed inset-0 z-50 flex animate-fade-in">
          <div
            onClick={onMobileClose}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
          />
          <aside className="relative w-[280px] max-w-[80vw] flex flex-col border-r border-border bg-background-elevated animate-slide-up">
            {content(true)}
          </aside>
        </div>
      )}
    </>
  );
}
