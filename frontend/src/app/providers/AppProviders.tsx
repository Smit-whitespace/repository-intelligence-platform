import { QueryClientProvider } from "@tanstack/react-query";
import { RouterProvider } from "react-router";
import { Toaster } from "sonner";
import { ErrorBoundary } from "@/components/common/ErrorBoundary";
import { queryClient } from "@/lib/api/queryClient";
import { ThemeProvider } from "./ThemeProvider";
import { router } from "../router/router";

export function AppProviders() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <RouterProvider router={router} />
          <Toaster richColors position="bottom-right" />
        </ThemeProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}
