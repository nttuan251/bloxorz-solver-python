// Colour themes. Each theme sets the CSS sky (app.css, [data-theme=...]) and every colour the
// 3D scene uses. Switch with the palette dock or the T key. `glow` is the animated rim around
// the block, `extras` adds a sky feature (a black hole, or the sun with clouds).

export const THEMES = [
  {
    id: "aurora",
    name: "Aurora",
    note: "Polar night, icy tiles, green light rolling across the sky",
    exposure: 1.0,
    hemi: ["#c6fff0", "#06101e", 0.7],
    sun: ["#e3f4ff", 1.8],
    rim: ["#53ffb0", 1.5],
    stars: ["#ffffff", "#d9fff1", "#b5e8ff", "#c8ffd9"],
    dust: "#b9ffe2",
    board: {
      stone: "#8fa3b3", rock: "#16212f", fragile: "#6aa9c9", wood: "#5d5248", brass: "#9fe8cf",
      hole: "#02060b", glow: "#6dffb5", beam: "#8affc6", light: "#4dff9f",
      heatLow: "#ffd36e", heatHigh: "#ff5c8a", path: "#ffffff",
    },
    block: { body: "#8a1c3a", emissive: "#2e0410", idle: "#5a4250", inlay: "#ffd9a8", ring: "#8affc6" },
    glow: ["#8affc6", "#4fd1ff", "#b47bff", "#ff6fae"],
    extras: "blackhole",
  },
  {
    id: "dusk",
    name: "Dusk",
    note: "Warm evening sky with the sun and drifting clouds",
    exposure: 1.05,
    hemi: ["#ffe9d6", "#5a4f86", 1.25],
    sun: ["#ffd7b0", 2.4],
    rim: ["#9fb2ff", 0.9],
    stars: ["#ffe2b8", "#fff4e0"],
    dust: "#ffe2b8",
    starCount: 0,
    board: {
      stone: "#e7dccb", rock: "#8a7363", fragile: "#eab565", wood: "#a97e55", brass: "#c99f4f",
      hole: "#1d140d", glow: "#ffcf7a", beam: "#ffd28a", light: "#ffc469",
      heatLow: "#8be7f2", heatHigh: "#5e5cf0", path: "#f2c46d",
    },
    block: { body: "#1f6f7d", emissive: "#000000", idle: "#5b7f86", inlay: "#e7b955", ring: "#f2c46d" },
    glow: ["#7f8cff", "#c86bff", "#ff5fa2", "#ffb347"],
    extras: "sun",
  },
];

export const themeById = id => THEMES.find(t => t.id === id) || THEMES[0];
