import React from "react";
import { createRoot } from "react-dom/client";
import { App } from "@/app/App";
import "@/styles/index.css";

const rootElement = document.getElementById("root");
if (!rootElement) throw new Error("Không tìm thấy phần tử root trong index.html.");

createRoot(rootElement).render(<React.StrictMode><App /></React.StrictMode>);
