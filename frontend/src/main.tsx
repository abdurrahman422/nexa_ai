import React from "react";
import ReactDOM from "react-dom/client";

import App from "./app/App";
import { DesignProvider } from "./providers";
import { InteractionProvider } from "./interaction";
import "./styles/index.css";

const rootElement = document.getElementById("root");

if (!rootElement) {
  throw new Error("Root element '#root' was not found.");
}

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <DesignProvider>
      <InteractionProvider>
        <App />
      </InteractionProvider>
    </DesignProvider>
  </React.StrictMode>
);
