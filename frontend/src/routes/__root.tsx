import { Outlet, Link, createRootRoute } from "@tanstack/react-router";
import { AuthProvider } from "@/contexts/AuthContext";
import { LoginPromoModal } from "@/components/auth/LoginPromoModal";

/**
 * NotFoundComponent
 * Rendered when the user navigates to a URL that doesn't match any routes.
 */
function NotFoundComponent() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <div className="max-w-md text-center">
        <h1 className="text-7xl font-bold text-foreground">404</h1>
        <h2 className="mt-4 text-xl font-semibold text-foreground">Page not found</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          The page you&apos;re looking for doesn&apos;t exist or has been moved.
        </p>
        <div className="mt-6">
          <Link
            to="/"
            className="inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            Go home
          </Link>
        </div>
      </div>
    </div>
  );
}

/**
 * RootComponent
 * The master layout wrapper for your entire application.
 * Note: QueryClientProvider is handled in main.tsx to avoid duplicate providers.
 */
function RootComponent() {
  return (
    <AuthProvider>
      <Outlet />
      <LoginPromoModal />
    </AuthProvider>
  );
}

/**
 * Route Configuration
 * Defines the root of the route tree.
 */
export const Route = createRootRoute({
  component: RootComponent,
  notFoundComponent: NotFoundComponent,
});