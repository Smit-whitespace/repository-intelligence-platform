import React from "react";
import ReactDOM from "react-dom/client";
import { captureTokenFromUrl } from "@/stores/authStore";
import { App } from "./App";
import "@/assets/styles.css";

// Before the first render: a sign-in link (?token=...) signs the app in.
captureTokenFromUrl();

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
