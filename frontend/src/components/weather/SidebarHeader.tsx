import { CloudSun, PanelLeftClose, PanelLeftOpen, X } from "lucide-react";

interface Props {
  showLabels: boolean;
  collapsed: boolean;
  onToggleCollapse: () => void;
  onMobileClose?: () => void;
}

/**
 * Shared sidebar logo header — used by both the main sidebar view and the
 * Chat History panel so both feel like the same sidebar environment.
 */
export function SidebarHeader({ showLabels, collapsed, onToggleCollapse, onMobileClose }: Props) {
  return (
    <div className="flex items-center gap-2.5 px-4 h-[52px] border-b border-border shrink-0">
      <div className="h-8 w-8 shrink-0 rounded-lg bg-gradient-to-br from-primary to-primary-glow flex items-center justify-center shadow-[0_0_20px_-5px_var(--primary-glow)]">
        <CloudSun className="h-4 w-4 text-primary-foreground" strokeWidth={2.5} />
      </div>
      {showLabels && (
        <div className="flex flex-col leading-tight flex-1 min-w-0">
          <span className="text-[13px] font-semibold tracking-tight truncate">Elexousia</span>
          <span className="text-[10px] text-muted-foreground tracking-wider uppercase truncate">Weather Intel</span>
        </div>
      )}
      <button
        onClick={onToggleCollapse}
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
  );
}
