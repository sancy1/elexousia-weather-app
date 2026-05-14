import { MapPin, Settings, Menu } from "lucide-react";
import { Notifications } from "./Notifications";

interface Props {
  city: string;
  unit: "C" | "F";
  onUnit: (u: "C" | "F") => void;
  onMenu?: () => void;
  user?: any;
}

export function TopBar({ city, unit, onUnit, onMenu, user }: Props) {
  return (
    <header className="h-[60px] shrink-0 flex items-center justify-between px-5 border-b border-border bg-background/80 backdrop-blur-xl sticky top-0 z-20">     
      <div className="flex items-center gap-3">
        <button onClick={onMenu} className="md:hidden h-9 w-9 flex items-center justify-center rounded-lg hover:bg-accent">
          <Menu className="h-4 w-4" />
        </button>
        <div className="hidden sm:flex items-center gap-2.5">
          <span className="text-[15px] font-semibold tracking-tight">EL-Exousia Weather</span>
          <span className="text-[10px] px-1.5 py-0.5 rounded bg-primary/15 text-primary-glow font-medium tracking-wider uppercase">Live</span>
        </div>
        <button className="ml-2 flex items-center gap-2 h-9 px-3 rounded-lg bg-secondary hover:bg-accent border border-border transition-all group">
          <MapPin className="h-3.5 w-3.5 text-primary-glow group-hover:scale-110 transition-transform" />
          <span className="text-[12px] font-medium">{city}</span>
        </button>
      </div>

      <div className="flex items-center gap-2">
        <div className="flex items-center bg-secondary border border-border rounded-lg p-0.5">
          {(["C", "F"] as const).map((u) => (
            <button
              key={u}
              onClick={() => onUnit(u)}
              className={`h-7 w-9 text-[12px] font-medium rounded-md transition-all ${
                unit === u
                  ? "bg-primary text-primary-foreground shadow-[0_0_12px_-4px_var(--primary)]"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              °{u}
            </button>
          ))}
        </div>
        <Notifications user={user} />
        {/* <button className="h-9 w-9 flex items-center justify-center rounded-lg hover:bg-accent text-muted-foreground hover:text-foreground transition-colors">   
          <Settings className="h-4 w-4" />
        </button> */}
      </div>
    </header>
  );
}
