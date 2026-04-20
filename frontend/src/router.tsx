import { createBrowserRouter, Navigate } from "react-router-dom";
import { AppShell } from "./components/AppShell";
import { ChatPage } from "./pages/ChatPage";
import { MarketChartPage } from "./pages/MarketChartPage";
import { OptionsPage } from "./pages/OptionsPage";
import { FNOPage } from "./pages/FNOPage";
import { RunsPage } from "./pages/RunsPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <Navigate to="/chat" replace /> },
      { path: "chat", element: <ChatPage /> },
      { path: "market", element: <MarketChartPage /> },
      { path: "options", element: <OptionsPage /> },
      { path: "fno", element: <FNOPage /> },
      { path: "runs", element: <RunsPage /> },
    ],
  },
]);
