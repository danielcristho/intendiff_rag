import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AnnotatorGate } from "@/components/AnnotatorGate";
import { AppLayout } from "@/components/AppLayout";
import { AuditPage } from "@/pages/AuditPage";
import { CardsPage } from "@/pages/CardsPage";
import { HnPage } from "@/pages/HnPage";
import { OverviewPage } from "@/pages/OverviewPage";

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 15_000, refetchOnWindowFocus: false } },
});

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AnnotatorGate>
        <BrowserRouter>
          <Routes>
            <Route element={<AppLayout />}>
              <Route path="/overview" element={<OverviewPage />} />
              <Route path="/audit" element={<AuditPage />} />
              <Route path="/cards" element={<CardsPage />} />
              <Route path="/hn" element={<HnPage />} />
            </Route>
            <Route path="*" element={<Navigate to="/audit" replace />} />
          </Routes>
        </BrowserRouter>
      </AnnotatorGate>
    </QueryClientProvider>
  );
}
