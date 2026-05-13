/**
 * Gentle login reminder: delayed, once per browser session if dismissed.
 */

import { useEffect, useState, useRef } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useAuth } from "@/contexts/AuthContext";
import { LoginButton } from "@/components/auth/LoginButton";
import { MapPin, Bell } from "lucide-react";

const STORAGE_KEY = "elexousia_login_promo_dismissed_session";
const DELAY_MS = 32_000;

export function LoginPromoModal() {
  const { user, loading } = useAuth();
  const [open, setOpen] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (loading || user) {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
      }
      if (user) setOpen(false);
      return;
    }

    if (typeof sessionStorage === "undefined") return;
    if (sessionStorage.getItem(STORAGE_KEY) === "1") return;

    timerRef.current = setTimeout(() => {
      if (sessionStorage.getItem(STORAGE_KEY) === "1") return;
      setOpen(true);
    }, DELAY_MS);

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, [user, loading]);

  const handleOpenChange = (next: boolean) => {
    if (!next) {
      try {
        sessionStorage.setItem(STORAGE_KEY, "1");
      } catch {
        /* ignore quota / private mode */
      }
    }
    setOpen(next);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent
        className="max-w-[min(92vw,420px)] border-0 bg-transparent p-0 shadow-none gap-0 overflow-visible sm:rounded-2xl data-[state=open]:zoom-in-95 [&>button]:right-3 [&>button]:top-3 [&>button]:rounded-full [&>button]:border [&>button]:border-primary/35 [&>button]:bg-card/95 [&>button]:p-2 [&>button]:text-foreground [&>button]:opacity-100 [&>button]:shadow-[0_0_16px_-4px_oklch(0.55_0.16_252/0.4)] [&>button]:hover:bg-primary/15 [&>button]:hover:text-foreground"
      >
        <div className="login-promo-neon rounded-2xl p-[2px]">
          {/* Solid panel so neon gradient does not wash out body copy */}
          <div className="rounded-[14px] bg-background border border-border px-6 pb-6 pt-9 shadow-[var(--shadow-card)]">
            <DialogHeader className="space-y-3 text-center sm:text-center pr-2">
              <DialogTitle className="text-xl font-semibold tracking-tight text-foreground">
                Sign in for the full experience
              </DialogTitle>
              <DialogDescription className="text-sm leading-relaxed text-foreground/95 text-balance">
                Save favorite locations in the sidebar and get notifications when weather shifts for those places.
                Use Google or GitHub below—it only takes a moment.
              </DialogDescription>
            </DialogHeader>
            <ul className="mt-4 flex flex-col gap-2 text-left text-[13px] leading-snug text-foreground/95">
              <li className="flex items-start gap-2 rounded-lg border border-border bg-secondary/60 px-3 py-2.5">
                <MapPin className="mt-0.5 h-4 w-4 shrink-0 text-primary" aria-hidden />
                <span className="text-foreground">Keep Home, Work, and travel spots one tap away.</span>
              </li>
              <li className="flex items-start gap-2 rounded-lg border border-border bg-secondary/60 px-3 py-2.5">
                <Bell className="mt-0.5 h-4 w-4 shrink-0 text-primary" aria-hidden />
                <span className="text-foreground">Alerts tied to your saved locations (where enabled).</span>
              </li>
            </ul>
            <div className="mt-6">
              <LoginButton variant="default" />
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
