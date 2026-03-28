import React from "react";
import { createCliRenderer, createRoot } from "@gridland/core";
import { App } from "./App";

async function main() {
  const renderer = await createCliRenderer();
  createRoot(renderer).render(<App />);
}

main();
