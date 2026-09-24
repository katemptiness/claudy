import { useState, useEffect, useRef, useCallback } from "react";

// ─────────────────────────────────────────────
// SPRITE DATA — 16×16 grids, 0=transparent, 1=body, 2=eyes, 3=blush, 4=accent
// ─────────────────────────────────────────────

const SPRITES = {
  idle: [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,2,2,1,1,2,2,1,1,0,0,0],
    [0,0,0,1,1,2,2,1,1,2,2,1,1,0,0,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0],
    [0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
  ],
  blink: [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,2,2,1,1,2,2,1,1,0,0,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0],
    [0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
  ],
  walk_a: [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,2,2,1,1,2,2,1,1,0,0,0],
    [0,0,0,1,1,2,2,1,1,2,2,1,1,0,0,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0],
    [0,0,0,0,1,0,0,0,0,1,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
  ],
  walk_b: [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,2,2,1,1,2,2,1,1,0,0,0],
    [0,0,0,1,1,2,2,1,1,2,2,1,1,0,0,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0],
    [0,0,0,0,0,0,1,0,0,0,0,1,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
  ],
  sleep_transition: [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,2,2,1,1,2,2,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0],
    [0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
  ],
  sleep_a: [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,2,2,1,1,2,2,1,1,0,0,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
  ],
  sleep_b: [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,2,2,1,1,2,2,1,1,0,0,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,0,1,0,0,0,0,1,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
  ],
  happy: [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,2,2,1,1,2,2,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,1,1,1,1,3,1,1,1,1,3,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0],
    [0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
  ],
  love: [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,2,1,2,1,2,1,2,1,1,0,0,0],
    [0,0,0,1,1,2,1,1,1,2,1,1,1,0,0,0],
    [0,1,1,1,1,3,1,1,1,1,3,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0],
    [0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
  ],
  demand: [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,1,0,0,0,0,0,0,0,0,0,0,0,0,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,2,2,1,1,2,2,1,1,0,0,0],
    [0,0,0,1,1,2,2,1,1,2,2,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0],
    [0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
  ],
  play_a: [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,2,2,1,1,2,2,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0],
    [0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
  ],
  play_b: [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,2,1,1,1,1,2,1,1,0,0,0],
    [0,0,0,1,1,2,2,1,1,2,2,1,1,0,0,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0],
    [0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
  ],
};

// ─────────────────────────────────────────────
// ANIMATION CYCLES
// ─────────────────────────────────────────────

const ANIMATIONS = {
  idle:    { frames: ["idle"], interval: 1000, loop: true },
  blink:   { frames: ["blink"], interval: 150, loop: false },
  walk:    { frames: ["walk_a", "walk_b"], interval: 200, loop: true },
  sleep_enter: { frames: ["sleep_transition", "sleep_a"], interval: 500, loop: false },
  sleep:   { frames: ["sleep_a", "sleep_b"], interval: 800, loop: true },
  happy:   { frames: ["happy", "idle", "happy"], interval: 200, loop: false },
  love:    { frames: ["love"], interval: 2000, loop: false },
  demand:  { frames: ["demand", "idle", "demand", "idle"], interval: 180, loop: true },
  play:    { frames: ["play_a", "play_b", "play_a", "happy"], interval: 250, loop: true },
};

// ─────────────────────────────────────────────
// COLORS
// ─────────────────────────────────────────────

const COLORS = {
  0: "transparent",
  1: "#D77757",    // body — Claude terracotta
  2: "#2D2D2D",    // eyes
  3: "#F0C0A0",    // blush
  4: "#E8A070",    // accent (unused for now)
};

const GRID = 16;
const PIXEL = 5;
const SPRITE_SIZE = GRID * PIXEL;

// ─────────────────────────────────────────────
// PARTICLE SYSTEM
// ─────────────────────────────────────────────

function createParticle(type, baseX, baseY) {
  const now = Date.now();
  switch (type) {
    case "zzz":
      return {
        type, x: baseX + 55, y: baseY - 10,
        vx: 0.3, vy: -0.6, life: 2000, born: now, opacity: 1,
        text: "z", size: 11, color: "#8BA4C4",
      };
    case "sparkle":
      return {
        type, x: baseX + Math.random() * 60 + 10, y: baseY - Math.random() * 20,
        vx: (Math.random() - 0.5) * 0.5, vy: -1.2 - Math.random() * 0.5,
        life: 800, born: now, opacity: 1,
        text: "✦", size: 10 + Math.random() * 6, color: "#FFD700",
      };
    case "heart":
      return {
        type, x: baseX + Math.random() * 50 + 15, y: baseY - 5,
        vx: (Math.random() - 0.5) * 0.4, vy: -1.0 - Math.random() * 0.4,
        life: 1200, born: now, opacity: 1,
        text: "♥", size: 10 + Math.random() * 5, color: "#FF6B8A",
      };
    case "note":
      return {
        type, x: baseX + Math.random() * 50 + 15, y: baseY - 5,
        vx: (Math.random() - 0.5) * 0.6, vy: -0.8 - Math.random() * 0.5,
        life: 1000, born: now, opacity: 1,
        text: ["♪", "♫", "♬"][Math.floor(Math.random() * 3)],
        size: 11 + Math.random() * 5, color: "#C084FC",
      };
    case "sweat":
      return {
        type, x: baseX + 62, y: baseY + 15,
        vx: 0.2, vy: 0.8,
        life: 600, born: now, opacity: 0.8,
        text: "💧", size: 9, color: "#60A5FA",
      };
    case "exclaim":
      return {
        type, x: baseX + 35, y: baseY - 18,
        vx: 0, vy: -0.3,
        life: 1000, born: now, opacity: 1,
        text: "❗", size: 14, color: "#FF4444",
      };
    default:
      return null;
  }
}

// ─────────────────────────────────────────────
// MAIN COMPONENT
// ─────────────────────────────────────────────

const NEEDS_DECAY = { energy: 0.08, attention: 0.12, fun: 0.10 };
const STATE_MESSAGES = {
  idle: "бродит...",
  walking: "гуляет ~",
  sleeping: "💤 спит...",
  playing: "играет! ♪",
  happy: "счастлив!",
  demanding: "хочет внимания!",
  love: "♥ обожает тебя",
};

export default function ClawdTamagotchi() {
  const canvasRef = useRef(null);
  const stateRef = useRef({
    // position
    x: 200, y: 0,
    targetX: 200,
    facingRight: true,
    // bounce offset for animations
    bounceY: 0,
    bouncePhase: 0,
    bouncing: false,
    shakeX: 0,
    shaking: false,
    shakeEnd: 0,
    // animation
    currentAnim: "idle",
    frameIndex: 0,
    frameTimer: 0,
    animDone: false,
    // state machine
    state: "idle",
    stateTimer: 0,
    // needs
    needs: { energy: 80, attention: 60, fun: 70 },
    // blink
    blinkTimer: 0,
    nextBlink: 2000,
    isBlinking: false,
    // particles
    particles: [],
    particleTimer: 0,
    // interaction
    lastClick: 0,
    clickCount: 0,
  });

  const [displayState, setDisplayState] = useState("idle");
  const [displayNeeds, setDisplayNeeds] = useState({ energy: 80, attention: 60, fun: 70 });
  const lastTimeRef = useRef(performance.now());
  const areaWidth = 520;
  const floorY = 180;

  // Pre-render sprites to offscreen canvases
  const spriteCacheRef = useRef({});

  const getSprite = useCallback((name) => {
    if (spriteCacheRef.current[name]) return spriteCacheRef.current[name];
    const offscreen = document.createElement("canvas");
    offscreen.width = SPRITE_SIZE;
    offscreen.height = SPRITE_SIZE;
    const ctx = offscreen.getContext("2d");
    const data = SPRITES[name];
    if (!data) return null;
    for (let row = 0; row < GRID; row++) {
      for (let col = 0; col < GRID; col++) {
        const val = data[row][col];
        if (val === 0) continue;
        ctx.fillStyle = COLORS[val];
        ctx.fillRect(col * PIXEL, row * PIXEL, PIXEL, PIXEL);
      }
    }
    spriteCacheRef.current[name] = offscreen;
    return offscreen;
  }, []);

  // Game loop
  useEffect(() => {
    let animFrame;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    const tick = (now) => {
      const dt = now - lastTimeRef.current;
      lastTimeRef.current = now;
      const s = stateRef.current;

      // ── Needs decay ──
      s.needs.energy = Math.max(0, s.needs.energy - NEEDS_DECAY.energy * dt / 1000);
      s.needs.attention = Math.max(0, s.needs.attention - NEEDS_DECAY.attention * dt / 1000);
      s.needs.fun = Math.max(0, s.needs.fun - NEEDS_DECAY.fun * dt / 1000);

      // ── Blink (only during idle-ish states) ──
      if (["idle", "walking"].includes(s.state) && !s.isBlinking) {
        s.blinkTimer += dt;
        if (s.blinkTimer > s.nextBlink) {
          s.isBlinking = true;
          s.blinkTimer = 0;
        }
      }
      if (s.isBlinking) {
        s.blinkTimer += dt;
        if (s.blinkTimer > 150) {
          s.isBlinking = false;
          s.blinkTimer = 0;
          s.nextBlink = 2000 + Math.random() * 4000;
        }
      }

      // ── Animation frame advancement ──
      const anim = ANIMATIONS[s.currentAnim];
      if (anim && !s.animDone) {
        s.frameTimer += dt;
        if (s.frameTimer >= anim.interval) {
          s.frameTimer = 0;
          s.frameIndex++;
          if (s.frameIndex >= anim.frames.length) {
            if (anim.loop) {
              s.frameIndex = 0;
            } else {
              s.frameIndex = anim.frames.length - 1;
              s.animDone = true;
            }
          }
        }
      }

      // ── Bounce animation ──
      if (s.bouncing) {
        s.bouncePhase += dt * 0.012;
        s.bounceY = Math.abs(Math.sin(s.bouncePhase)) * 12;
        if (s.bouncePhase > Math.PI * 3) {
          s.bouncing = false;
          s.bounceY = 0;
          s.bouncePhase = 0;
        }
      }

      // ── Shake animation ──
      if (s.shaking) {
        if (now > s.shakeEnd) {
          s.shaking = false;
          s.shakeX = 0;
        } else {
          s.shakeX = (Math.random() - 0.5) * 6;
        }
      }

      // ── State machine ──
      s.stateTimer += dt;

      switch (s.state) {
        case "idle": {
          if (s.needs.energy < 15) {
            enterState(s, "sleeping");
          } else if (s.needs.attention < 15) {
            enterState(s, "demanding");
          } else if (s.stateTimer > 3000 + Math.random() * 4000) {
            const roll = Math.random();
            if (roll < 0.4) enterState(s, "walking");
            else if (roll < 0.6 && s.needs.fun < 50) enterState(s, "playing");
            else if (roll < 0.7 && s.needs.energy < 40) enterState(s, "sleeping");
            else enterState(s, "idle"); // reset timer
          }
          break;
        }
        case "walking": {
          // Move toward target
          const speed = 0.06 * dt;
          const dx = s.targetX - s.x;
          if (Math.abs(dx) < 2) {
            enterState(s, "idle");
          } else {
            s.x += Math.sign(dx) * Math.min(speed, Math.abs(dx));
            s.facingRight = dx > 0;
          }
          break;
        }
        case "sleeping": {
          s.needs.energy = Math.min(100, s.needs.energy + 0.15 * dt / 1000);
          // Zzz particles
          s.particleTimer += dt;
          if (s.particleTimer > 1200) {
            s.particleTimer = 0;
            s.particles.push(createParticle("zzz", s.x, floorY));
          }
          if (s.needs.energy > 90 && s.stateTimer > 5000) {
            enterState(s, "idle");
          }
          break;
        }
        case "playing": {
          s.needs.fun = Math.min(100, s.needs.fun + 0.3 * dt / 1000);
          s.bouncing = true;
          // Notes
          s.particleTimer += dt;
          if (s.particleTimer > 500) {
            s.particleTimer = 0;
            s.particles.push(createParticle("note", s.x, floorY));
          }
          if (s.stateTimer > 4000 || s.needs.fun > 85) {
            s.bouncing = false;
            s.bounceY = 0;
            enterState(s, "idle");
          }
          break;
        }
        case "happy": {
          if (s.stateTimer > 2000) {
            enterState(s, "idle");
          }
          break;
        }
        case "love": {
          s.particleTimer += dt;
          if (s.particleTimer > 300) {
            s.particleTimer = 0;
            s.particles.push(createParticle("heart", s.x, floorY));
          }
          if (s.stateTimer > 2500) {
            enterState(s, "idle");
          }
          break;
        }
        case "demanding": {
          s.shaking = true;
          s.shakeEnd = now + 100;
          s.particleTimer += dt;
          if (s.particleTimer > 800) {
            s.particleTimer = 0;
            s.particles.push(createParticle("exclaim", s.x, floorY));
          }
          if (s.needs.attention > 50) {
            s.shaking = false;
            s.shakeX = 0;
            enterState(s, "happy");
          } else if (s.stateTimer > 6000) {
            s.shaking = false;
            s.shakeX = 0;
            enterState(s, "idle");
          }
          break;
        }
      }

      // ── Update particles ──
      s.particles = s.particles.filter((p) => {
        const age = now - p.born;
        if (age > p.life) return false;
        p.x += p.vx;
        p.y += p.vy;
        p.opacity = 1 - age / p.life;
        return true;
      });

      // ── RENDER ──
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Shadow
      const shadowX = s.x + s.shakeX + 18;
      const shadowY = floorY + SPRITE_SIZE - 8;
      ctx.fillStyle = "rgba(0,0,0,0.08)";
      ctx.beginPath();
      ctx.ellipse(shadowX + (SPRITE_SIZE - 36) / 2, shadowY, 22, 5, 0, 0, Math.PI * 2);
      ctx.fill();

      // Determine which sprite to show
      let spriteName;
      if (s.isBlinking && ["idle", "walking"].includes(s.state)) {
        spriteName = "blink";
      } else {
        const anim = ANIMATIONS[s.currentAnim];
        spriteName = anim ? anim.frames[s.frameIndex] : "idle";
      }
      const sprite = getSprite(spriteName);

      if (sprite) {
        ctx.save();
        const drawX = s.x + s.shakeX;
        const drawY = floorY - s.bounceY;
        if (!s.facingRight) {
          ctx.translate(drawX + SPRITE_SIZE, drawY);
          ctx.scale(-1, 1);
          ctx.drawImage(sprite, 0, 0);
        } else {
          ctx.drawImage(sprite, drawX, drawY);
        }
        ctx.restore();
      }

      // Particles
      for (const p of s.particles) {
        ctx.globalAlpha = p.opacity;
        ctx.font = `${p.size}px "Courier New", monospace`;
        ctx.fillStyle = p.color;
        ctx.fillText(p.text, p.x, p.y);
      }
      ctx.globalAlpha = 1;

      // Update React state (throttled)
      if (s.state !== displayState) setDisplayState(s.state);
      setDisplayNeeds({ ...s.needs });

      animFrame = requestAnimationFrame(tick);
    };

    animFrame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(animFrame);
  }, [getSprite, displayState]);

  function enterState(s, newState) {
    s.state = newState;
    s.stateTimer = 0;
    s.particleTimer = 0;
    s.animDone = false;
    s.frameIndex = 0;
    s.frameTimer = 0;

    switch (newState) {
      case "idle":
        s.currentAnim = "idle";
        break;
      case "walking":
        s.currentAnim = "walk";
        s.targetX = Math.random() * (areaWidth - SPRITE_SIZE);
        break;
      case "sleeping":
        s.currentAnim = "sleep_enter";
        setTimeout(() => {
          if (s.state === "sleeping") {
            s.currentAnim = "sleep";
            s.frameIndex = 0;
            s.animDone = false;
          }
        }, 1000);
        break;
      case "playing":
        s.currentAnim = "play";
        s.bouncing = true;
        s.bouncePhase = 0;
        break;
      case "happy":
        s.currentAnim = "happy";
        s.bouncing = true;
        s.bouncePhase = 0;
        s.particles.push(createParticle("sparkle", s.x, floorY));
        s.particles.push(createParticle("sparkle", s.x, floorY));
        s.particles.push(createParticle("sparkle", s.x, floorY));
        break;
      case "love":
        s.currentAnim = "love";
        break;
      case "demanding":
        s.currentAnim = "demand";
        s.particles.push(createParticle("exclaim", s.x, floorY));
        break;
    }
  }

  // Click handler
  function handleClick(e) {
    const s = stateRef.current;
    const rect = canvasRef.current.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    // Hit test on crab
    if (mx >= s.x && mx <= s.x + SPRITE_SIZE && my >= floorY && my <= floorY + SPRITE_SIZE) {
      const now = Date.now();
      if (now - s.lastClick < 500) s.clickCount++;
      else s.clickCount = 1;
      s.lastClick = now;

      s.needs.attention = Math.min(100, s.needs.attention + 25);

      if (s.state === "sleeping") {
        // Wake up!
        s.needs.energy = Math.min(100, s.needs.energy + 10);
        enterState(s, "happy");
      } else if (s.clickCount >= 3) {
        enterState(s, "love");
        s.clickCount = 0;
      } else {
        enterState(s, "happy");
        s.bouncing = true;
        s.bouncePhase = 0;
      }
    }
  }

  // Action buttons
  function feedAction() {
    const s = stateRef.current;
    s.needs.energy = Math.min(100, s.needs.energy + 30);
    enterState(s, "happy");
    for (let i = 0; i < 4; i++) {
      s.particles.push(createParticle("sparkle", s.x, floorY));
    }
  }

  function playAction() {
    const s = stateRef.current;
    enterState(s, "playing");
  }

  function petAction() {
    const s = stateRef.current;
    s.needs.attention = Math.min(100, s.needs.attention + 35);
    enterState(s, "love");
  }

  const needBarColor = (val) => {
    if (val > 60) return "#6DBF67";
    if (val > 30) return "#E8B84B";
    return "#E05555";
  };

  return (
    <div style={{
      display: "flex", flexDirection: "column", alignItems: "center", gap: 16,
      fontFamily: '"Courier New", monospace',
      background: "linear-gradient(180deg, #1a1520 0%, #2a2035 50%, #1e1828 100%)",
      minHeight: "100vh", padding: "24px 16px", color: "#e8ddd0",
    }}>
      <div style={{
        fontSize: 11, letterSpacing: 3, textTransform: "uppercase",
        color: "#D7775780", marginBottom: 4,
      }}>
        clawd tamagotchi
      </div>

      {/* Main viewport */}
      <div style={{
        position: "relative",
        background: "linear-gradient(180deg, #2a2540 0%, #342a45 60%, #3d3350 100%)",
        borderRadius: 16, padding: 2,
        boxShadow: "0 0 40px rgba(215,119,87,0.08), inset 0 1px 0 rgba(255,255,255,0.05)",
        border: "1px solid rgba(215,119,87,0.15)",
      }}>
        <div style={{
          borderRadius: 14, overflow: "hidden",
          background: "linear-gradient(180deg, #1e1830 0%, #252040 100%)",
        }}>
          <canvas
            ref={canvasRef}
            width={areaWidth}
            height={280}
            onClick={handleClick}
            style={{
              display: "block", cursor: "pointer",
              imageRendering: "pixelated",
            }}
          />
          {/* Floor line */}
          <div style={{
            position: "absolute", bottom: 26, left: 12, right: 12,
            height: 1, background: "rgba(215,119,87,0.12)",
          }} />
        </div>
      </div>

      {/* Status */}
      <div style={{
        fontSize: 13, color: "#D77757", letterSpacing: 1,
        minHeight: 20,
      }}>
        {STATE_MESSAGES[displayState] || "..."}
      </div>

      {/* Needs bars */}
      <div style={{
        display: "flex", gap: 20, fontSize: 11, width: areaWidth, justifyContent: "center",
      }}>
        {[
          { label: "энергия", key: "energy", icon: "⚡" },
          { label: "внимание", key: "attention", icon: "💛" },
          { label: "веселье", key: "fun", icon: "✦" },
        ].map(({ label, key, icon }) => (
          <div key={key} style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 4 }}>
            <span style={{ color: "#8a7a90", fontSize: 10, letterSpacing: 1 }}>
              {icon} {label}
            </span>
            <div style={{
              width: 120, height: 8, background: "#1a1520",
              borderRadius: 4, overflow: "hidden",
              border: "1px solid rgba(255,255,255,0.05)",
            }}>
              <div style={{
                height: "100%", borderRadius: 4,
                width: `${displayNeeds[key]}%`,
                background: needBarColor(displayNeeds[key]),
                transition: "width 0.3s, background 0.5s",
                boxShadow: `0 0 6px ${needBarColor(displayNeeds[key])}40`,
              }} />
            </div>
          </div>
        ))}
      </div>

      {/* Action buttons */}
      <div style={{ display: "flex", gap: 10, marginTop: 4 }}>
        {[
          { label: "покормить", icon: "🍙", action: feedAction },
          { label: "поиграть", icon: "🎾", action: playAction },
          { label: "погладить", icon: "🤚", action: petAction },
        ].map(({ label, icon, action }) => (
          <button
            key={label}
            onClick={action}
            style={{
              background: "rgba(215,119,87,0.1)",
              border: "1px solid rgba(215,119,87,0.25)",
              borderRadius: 10, padding: "8px 16px",
              color: "#D77757", cursor: "pointer",
              fontFamily: '"Courier New", monospace',
              fontSize: 12, letterSpacing: 0.5,
              transition: "all 0.15s",
            }}
            onMouseEnter={(e) => {
              e.target.style.background = "rgba(215,119,87,0.2)";
              e.target.style.borderColor = "rgba(215,119,87,0.5)";
            }}
            onMouseLeave={(e) => {
              e.target.style.background = "rgba(215,119,87,0.1)";
              e.target.style.borderColor = "rgba(215,119,87,0.25)";
            }}
          >
            {icon} {label}
          </button>
        ))}
      </div>

      <div style={{
        fontSize: 10, color: "#5a4a60", marginTop: 8, textAlign: "center",
        lineHeight: 1.6, maxWidth: 400,
      }}>
        кликни на крабика — он обрадуется. кликни три раза подряд — влюбится.<br/>
        потребности падают со временем. если внимание упадёт — начнёт требовать.
      </div>
    </div>
  );
}
