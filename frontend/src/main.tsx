import React from "react";
import ReactDOM from "react-dom/client";
import { RouterProvider } from "@tanstack/react-router";
import { QueryClientProvider } from "@tanstack/react-query";
import { router, queryClient } from "./router";

// Standard CSS import (Tailwind v4 is handled via vite.config.ts)
import "./styles.css";

// 1. Grab the root element from index.html
const rootElement = document.getElementById("root");

// 2. Safeguard against missing root element
if (!rootElement) {
  throw new Error(
    "Failed to find the root element. Please ensure your index.html has a <div id='root'></div>"
  );
}

// 3. Render the application using React 18+ syntax
const root = ReactDOM.createRoot(rootElement);

root.render(
  <React.StrictMode>
    {/* Provides TanStack Query (weather data fetching) to the whole app */}
    <QueryClientProvider client={queryClient}>
      {/* Provides TanStack Router (navigation) to the whole app */}
      <RouterProvider router={router} />
    </QueryClientProvider>
  </React.StrictMode>
);