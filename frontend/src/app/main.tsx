import React from "react";
import ReactDOM from "react-dom/client";
import { signInFromUrl } from "@/stores/authStore";
import { App } from "./App";
import "@/assets/styles.css";

// A sign-in link (?code=...) signs the app in; the code is removed from
// the address bar at once, and the app shows when the token arrives.
void signInFromUrl();

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
