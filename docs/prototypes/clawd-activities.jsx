import { useState, useEffect, useRef, useCallback } from "react";

// ─── PALETTE ───
const C = {
  0: "transparent",
  1: "#D77757",  // body
  2: "#2D2D2D",  // eyes
  3: "#F0C0A0",  // blush
  4: "#7B5B3A",  // brown (book, rod)
  5: "#F5F0E8",  // cream (pages, paper)
  6: "#60A5FA",  // blue (screen, water, line)
  7: "#A855F7",  // purple (magic)
  8: "#8A8A9A",  // gray (laptop)
  9: "#FFD700",  // gold (star, sparkle)
};

const GRID = 16, PX = 5, SIZE = GRID * PX;

// ─── SPRITES ───
const S = {
  // ── BASE ──
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

  // ── READING ──
  read_a: [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,2,2,1,1,2,2,1,1,0,0,0],
    [0,0,1,1,1,1,1,1,1,1,1,1,1,1,0,0],
    [0,0,1,4,5,5,5,5,5,5,5,5,4,1,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0],
    [0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
  ],
  read_b: [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,2,2,1,1,2,2,1,1,0,0,0],
    [0,0,1,1,1,1,1,1,1,1,1,1,1,1,0,0],
    [0,0,1,4,5,5,5,5,5,5,4,4,4,1,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0],
    [0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
  ],
  read_react: [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,2,2,1,1,2,2,1,1,0,0,0],
    [0,0,0,1,1,2,2,1,1,2,2,1,1,0,0,0],
    [0,0,0,1,1,2,2,1,1,2,2,1,1,0,0,0],
    [0,0,1,1,1,1,1,1,1,1,1,1,1,1,0,0],
    [0,0,1,4,5,5,5,5,5,5,5,5,4,1,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0],
    [0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
  ],

  // ── MAGIC ──
  magic_hold: [
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
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,7,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,7,0],
    [0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0],
    [0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
  ],
  magic_raise: [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,9,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,7,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,7,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,2,2,1,1,2,2,1,1,0,0,0],
    [0,0,0,1,1,2,2,1,1,2,2,1,1,0,0,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0],
    [0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
  ],
  magic_cast: [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,2,2,1,1,2,2,1,1,0,0,0],
    [0,0,0,1,1,2,2,1,1,2,2,1,7,7,9,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0],
    [0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
  ],
  magic_done: [
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

  // ── LAPTOP ──
  work_a: [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,2,2,1,1,2,2,1,1,0,0,0],
    [0,0,0,1,1,2,2,1,1,2,2,1,1,0,0,0],
    [0,0,1,1,8,6,6,6,6,8,1,1,1,1,0,0],
    [0,0,1,1,8,8,8,8,8,8,1,1,1,1,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0],
    [0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
  ],
  work_b: [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,2,2,1,1,2,2,1,1,0,0,0],
    [0,0,0,1,1,2,2,1,1,2,2,1,1,0,0,0],
    [0,0,1,1,8,6,6,6,6,8,1,1,1,1,0,0],
    [0,0,1,1,8,8,8,8,8,8,1,1,1,1,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0],
    [0,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
  ],
  work_think: [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,2,2,1,1,1,2,1,1,0,0,0],
    [0,0,0,1,1,2,2,1,1,2,2,1,1,0,0,0],
    [0,0,1,1,8,6,6,6,6,8,1,1,1,1,0,0],
    [0,0,1,1,8,8,8,8,8,8,1,1,1,1,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0],
    [0,0,0,0,1,0,1,0,0,1,0,1,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
  ],

  // ── FISHING ──
  fish_wait: [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,4,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,4,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,4,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,4,0,0,0,0],
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
  fish_wait_b: [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,4,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,4,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,4,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,4,0,0,0,0],
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
  fish_bite: [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,4,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,4,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,4,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,4,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,2,2,1,1,2,2,1,1,0,0,0],
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
  fish_pull: [
    [0,0,0,0,0,0,0,0,0,0,0,0,4,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,4,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,4,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,4,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,2,2,1,1,2,2,1,1,0,0,0],
    [0,0,0,1,1,2,2,1,1,2,2,1,1,0,0,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,1,1,1,1,1,1,1,1,1,1,1,1,1,1,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,0,0,0,1,0,0,1,0,0,0,0,0,0],
    [0,0,0,0,1,0,0,0,0,0,0,1,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
  ],
  fish_happy: [
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
  fish_confused: [
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,1,1,1,1,1,1,1,1,1,1,0,0,0],
    [0,0,0,1,1,2,2,1,1,2,2,1,1,0,0,0],
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
};

// ─── FISHING CATCHES ───
const CATCHES = [
  { emoji: "🐟", name: "рыбка!", reaction: "happy",   particles: "sparkle" },
  { emoji: "🐡", name: "фугу!!",  reaction: "happy",   particles: "sparkle" },
  { emoji: "👢", name: "ботинок...", reaction: "confused", particles: "sweat" },
  { emoji: "🌿", name: "водоросли", reaction: "confused", particles: "sweat" },
  { emoji: "💎", name: "АЛМАЗ!!", reaction: "love",    particles: "heart" },
  { emoji: "📦", name: "коробка?!", reaction: "confused", particles: "question" },
  { emoji: "⭐", name: "звезда!!!", reaction: "love",    particles: "star" },
  { emoji: "🧦", name: "носок.", reaction: "confused", particles: "sweat" },
];

// ─── MAGIC RESULTS ───
const MAGIC_RESULTS = [
  { text: "✨ появился букет!", particles: "flower" },
  { text: "🌈 радуга!", particles: "rainbow" },
  { text: "⭐ звездопад!", particles: "star" },
  { text: "🦋 бабочка!", particles: "butterfly" },
  { text: "🔮 ничего... wait", particles: "poof" },
];

// ─── PARTICLE FACTORY ───
function mkP(type, bx, by) {
  const n = Date.now();
  const base = { born: n, opacity: 1 };
  const r = () => Math.random();
  switch (type) {
    case "zzz": return { ...base, type, x:bx+60, y:by-5, vx:0.3, vy:-0.5, life:2200, text:"z", size:11, color:"#8BA4C4" };
    case "sparkle": return { ...base, type, x:bx+r()*60+10, y:by-r()*15, vx:(r()-0.5)*0.5, vy:-1.2-r()*0.5, life:800, text:"✦", size:9+r()*7, color:"#FFD700" };
    case "heart": return { ...base, type, x:bx+r()*50+15, y:by-5, vx:(r()-0.5)*0.4, vy:-1-r()*0.4, life:1200, text:"♥", size:10+r()*5, color:"#FF6B8A" };
    case "note": return { ...base, type, x:bx+r()*50+15, y:by-5, vx:(r()-0.5)*0.6, vy:-0.8-r()*0.5, life:1000, text:["♪","♫","♬"][~~(r()*3)], size:11+r()*5, color:"#C084FC" };
    case "sweat": return { ...base, type, x:bx+65, y:by+15, vx:0.2, vy:0.8, life:600, text:"💧", size:9, color:"#60A5FA" };
    case "question": return { ...base, type, x:bx+35, y:by-18, vx:0, vy:-0.3, life:1200, text:"❓", size:14, color:"#FFA500" };
    case "exclaim": return { ...base, type, x:bx+35, y:by-18, vx:0, vy:-0.3, life:1000, text:"❗", size:14, color:"#FF4444" };
    case "star": return { ...base, type, x:bx+r()*70+5, y:by-r()*30, vx:(r()-0.5)*0.8, vy:-1.5-r()*0.5, life:1000, text:"⭐", size:8+r()*8, color:"#FFD700" };
    case "flower": return { ...base, type, x:bx+r()*60+10, y:by-r()*10, vx:(r()-0.5)*0.6, vy:-1-r()*0.3, life:1100, text:["🌸","🌼","🌺"][~~(r()*3)], size:10+r()*5, color:"#FFB7C5" };
    case "rainbow": return { ...base, type, x:bx+r()*60+10, y:by-r()*10, vx:(r()-0.5)*0.3, vy:-1.2-r()*0.3, life:1200, text:"✦", size:8+r()*8, color:["#FF6B6B","#FFA94D","#FFD43B","#69DB7C","#63E6E6","#748FFC","#DA77F2"][~~(r()*7)] };
    case "butterfly": return { ...base, type, x:bx+r()*60+10, y:by-r()*20, vx:(r()-0.5)*1.0, vy:-0.5-r()*0.5, life:2000, text:"🦋", size:11+r()*4, color:"#C084FC" };
    case "poof": return { ...base, type, x:bx+r()*50+15, y:by+r()*20, vx:(r()-0.5)*1.5, vy:-0.5-r()*0.3, life:600, text:"💨", size:10+r()*6, color:"#9CA3AF" };
    case "code": return { ...base, type, x:bx+r()*60+5, y:by-r()*10, vx:(r()-0.5)*0.3, vy:-0.8-r()*0.3, life:900, text:["</>","{ }","01","fn"][~~(r()*4)], size:8+r()*4, color:"#60A5FA" };
    case "page": return { ...base, type, x:bx+35, y:by+25, vx:(r()-0.5)*0.3, vy:-0.4, life:1500, text:"📖", size:8, color:"#F5F0E8" };
    case "fishItem": return null; // handled specially
    default: return { ...base, type, x:bx+30, y:by-10, vx:0, vy:-0.5, life:1000, text:"✦", size:10, color:"#FFD700" };
  }
}

// ─── COMPONENT ───
export default function ClawdActivities() {
  const canvasRef = useRef(null);
  const stateRef = useRef({
    x: 210, bounceY: 0, bouncePhase: 0, bouncing: false, shakeX: 0, shaking: false, shakeEnd: 0,
    activity: "idle", phase: 0, timer: 0, frameIndex: 0, frameTimer: 0,
    blinkTimer: 0, nextBlink: 2500, isBlinking: false,
    particles: [], particleTimer: 0,
    fishCatch: null, message: "", messageTimer: 0,
  });
  const [message, setMessage] = useState("");
  const [activity, setActivity] = useState("idle");
  const lastT = useRef(performance.now());
  const spriteCache = useRef({});
  const W = 520, H = 260, floorY = 152;

  const getSprite = useCallback((name) => {
    if (spriteCache.current[name]) return spriteCache.current[name];
    const off = document.createElement("canvas");
    off.width = SIZE; off.height = SIZE;
    const ctx = off.getContext("2d");
    const data = S[name];
    if (!data) return null;
    for (let r = 0; r < GRID; r++)
      for (let c = 0; c < GRID; c++) {
        if (data[r][c] === 0) continue;
        ctx.fillStyle = C[data[r][c]];
        ctx.fillRect(c * PX, r * PX, PX, PX);
      }
    spriteCache.current[name] = off;
    return off;
  }, []);

  // ─── ACTIVITY SEQUENCES ───
  const sequences = useRef({
    idle: { phases: [{ frames: ["idle"], interval: 1000, duration: Infinity }] },
    reading: {
      phases: [
        { frames: ["read_a"], interval: 500, duration: 800, msg: "берёт книжку..." },
        { frames: ["read_a","read_b"], interval: 600, duration: 4000, msg: "читает...", particle: "page", pInterval: 2000 },
        { frames: ["read_react"], interval: 200, duration: 1200, msg: "о! интересно!", particle: "exclaim", pInterval: 800, bounce: true },
        { frames: ["read_a","read_b"], interval: 600, duration: 3000, msg: "читает дальше..." },
        { frames: ["idle"], interval: 500, duration: 1500, msg: "закрыл книгу" },
      ],
    },
    magic: {
      phases: [
        { frames: ["magic_hold"], interval: 500, duration: 1000, msg: "достаёт палочку..." },
        { frames: ["magic_raise"], interval: 300, duration: 1200, msg: "замахивается...", bounce: true },
        { frames: ["magic_cast"], interval: 150, duration: 800, msg: "✨ ВЗМАХ!", particle: null, shake: true, castMagic: true },
        { frames: ["magic_done"], interval: 500, duration: 2500, msg: null, particle: null },
        { frames: ["idle"], interval: 500, duration: 1000, msg: "" },
      ],
    },
    working: {
      phases: [
        { frames: ["work_a"], interval: 400, duration: 800, msg: "открывает ноутбук..." },
        { frames: ["work_a","work_b"], interval: 180, duration: 3500, msg: "тук-тук-тук...", particle: "code", pInterval: 600 },
        { frames: ["work_think"], interval: 500, duration: 1500, msg: "хмм...", particle: "question", pInterval: 1200 },
        { frames: ["work_a","work_b"], interval: 150, duration: 2500, msg: "ПИШЕТ КОД!!", particle: "code", pInterval: 300, shake: true },
        { frames: ["magic_done"], interval: 500, duration: 1500, msg: "готово! ✨", particle: "sparkle", pInterval: 200 },
        { frames: ["idle"], interval: 500, duration: 1000, msg: "" },
      ],
    },
    fishing: {
      phases: [
        { frames: ["fish_wait"], interval: 500, duration: 800, msg: "забрасывает удочку..." },
        { frames: ["fish_wait","fish_wait_b"], interval: 800, duration: 3500, msg: "ждёт...", particle: "zzz", pInterval: 1500 },
        { frames: ["fish_bite"], interval: 120, duration: 1000, msg: "❗ клюёт!!", particle: "exclaim", pInterval: 600, shake: true },
        { frames: ["fish_pull","fish_bite"], interval: 150, duration: 1200, msg: "тянет!!!", shake: true },
        { frames: [null], interval: 500, duration: 2500, msg: null, fishReveal: true },
        { frames: ["idle"], interval: 500, duration: 1500, msg: "" },
      ],
    },
  });

  function startActivity(name) {
    const s = stateRef.current;
    s.activity = name;
    s.phase = 0;
    s.timer = 0;
    s.frameIndex = 0;
    s.frameTimer = 0;
    s.particles = [];
    s.particleTimer = 0;
    s.fishCatch = null;
    s.bouncing = false;
    s.bounceY = 0;
    s.shaking = false;
    s.shakeX = 0;
    s.message = "";
    s.messageTimer = 0;
    setActivity(name);
    setMessage("");
  }

  useEffect(() => {
    let af;
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");

    const tick = (now) => {
      const dt = now - lastT.current;
      lastT.current = now;
      const s = stateRef.current;
      const seq = sequences.current[s.activity];
      if (!seq) { af = requestAnimationFrame(tick); return; }

      const phases = seq.phases || [{ frames: seq.frames, interval: seq.interval, duration: Infinity }];
      const ph = phases[s.phase];
      if (!ph) {
        startActivity("idle");
        af = requestAnimationFrame(tick);
        return;
      }

      // Phase timer
      s.timer += dt;
      if (s.timer >= ph.duration && ph.duration !== Infinity) {
        if (s.phase < phases.length - 1) {
          s.phase++;
          s.timer = 0;
          s.frameIndex = 0;
          s.frameTimer = 0;
          s.particleTimer = 0;
          const np = phases[s.phase];
          if (np) {
            if (np.msg !== undefined && np.msg !== null) { s.message = np.msg; s.messageTimer = now; setMessage(np.msg); }
            if (np.bounce) { s.bouncing = true; s.bouncePhase = 0; }
            if (np.shake) { s.shaking = true; s.shakeEnd = now + np.duration; }
            if (np.castMagic) {
              const mr = MAGIC_RESULTS[~~(Math.random() * MAGIC_RESULTS.length)];
              s.message = mr.text; setMessage(mr.text);
              for (let i = 0; i < 8; i++) s.particles.push(mkP(mr.particles, s.x, floorY));
            }
            if (np.fishReveal) {
              const c = CATCHES[~~(Math.random() * CATCHES.length)];
              s.fishCatch = c;
              s.message = `${c.emoji} ${c.name}`; setMessage(`${c.emoji} ${c.name}`);
              for (let i = 0; i < 5; i++) s.particles.push(mkP(c.particles, s.x, floorY));
              s.particles.push({ type:"item", x:s.x+35, y:floorY+30, vx:0, vy:-0.8, life:2000, born:now, opacity:1, text:c.emoji, size:20, color:"#FFF" });
            }
          }
          af = requestAnimationFrame(tick);
          return;
        } else {
          // Last phase done — return to idle
          s.activity = "idle"; s.phase = 0; s.timer = 0;
          s.frameIndex = 0; s.frameTimer = 0;
          s.bouncing = false; s.bounceY = 0;
          s.shaking = false; s.shakeX = 0;
          s.message = ""; s.fishCatch = null;
          setActivity("idle"); setMessage("");
        }
      }

      // Initial message
      if (ph.msg && !s.message && s.timer < 100) {
        s.message = ph.msg; setMessage(ph.msg);
      }

      // Frame animation
      const frames = ph.fishReveal
        ? [s.fishCatch?.reaction === "happy" ? "fish_happy" : s.fishCatch?.reaction === "love" ? "fish_happy" : "fish_confused"]
        : (!ph.frames || ph.frames[0] === null ? ["idle"] : ph.frames);

      s.frameTimer += dt;
      if (s.frameTimer >= (ph.interval || 300)) {
        s.frameTimer = 0;
        s.frameIndex = (s.frameIndex + 1) % frames.length;
      }

      // Blink (idle only)
      if (s.activity === "idle" && !s.isBlinking) {
        s.blinkTimer += dt;
        if (s.blinkTimer > s.nextBlink) { s.isBlinking = true; s.blinkTimer = 0; }
      }
      if (s.isBlinking) {
        s.blinkTimer += dt;
        if (s.blinkTimer > 150) { s.isBlinking = false; s.blinkTimer = 0; s.nextBlink = 2000 + Math.random() * 4000; }
      }

      // Bounce
      if (s.bouncing) {
        s.bouncePhase += dt * 0.012;
        s.bounceY = Math.abs(Math.sin(s.bouncePhase)) * 10;
        if (s.bouncePhase > Math.PI * 3) { s.bouncing = false; s.bounceY = 0; }
      }

      // Shake
      if (s.shaking) {
        if (now > s.shakeEnd) { s.shaking = false; s.shakeX = 0; }
        else s.shakeX = (Math.random() - 0.5) * 5;
      }

      // Particles from phase
      if (ph.particle && ph.pInterval) {
        s.particleTimer += dt;
        if (s.particleTimer >= ph.pInterval) {
          s.particleTimer = 0;
          const p = mkP(ph.particle, s.x, floorY);
          if (p) s.particles.push(p);
        }
      }

      // Update particles
      s.particles = s.particles.filter(p => {
        const age = now - p.born;
        if (age > p.life) return false;
        p.x += p.vx; p.y += p.vy;
        p.opacity = Math.max(0, 1 - age / p.life);
        return true;
      });

      // ── RENDER ──
      ctx.clearRect(0, 0, W, H);

      // Fishing water
      if (s.activity === "fishing") {
        ctx.fillStyle = "rgba(96,165,250,0.06)";
        ctx.fillRect(0, floorY + SIZE - 4, W, H - floorY - SIZE + 4);
        ctx.strokeStyle = "rgba(96,165,250,0.15)";
        ctx.lineWidth = 1;
        ctx.beginPath();
        const wy = floorY + SIZE - 4;
        ctx.moveTo(0, wy);
        for (let wx = 0; wx < W; wx += 4) {
          ctx.lineTo(wx, wy + Math.sin((wx + now * 0.002) * 0.05) * 2);
        }
        ctx.stroke();

        // Fishing line
        if (s.phase >= 0 && s.phase <= 3) {
          ctx.strokeStyle = "rgba(96,165,250,0.4)";
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(s.x + 70, floorY + 2);
          const lineEndY = floorY + SIZE + 10 + (s.phase >= 2 ? Math.sin(now * 0.01) * 5 : 0);
          ctx.lineTo(s.x + 72, lineEndY);
          ctx.stroke();
        }
      }

      // Shadow
      ctx.fillStyle = "rgba(0,0,0,0.07)";
      ctx.beginPath();
      ctx.ellipse(s.x + s.shakeX + SIZE / 2, floorY + SIZE - 6, 24, 5, 0, 0, Math.PI * 2);
      ctx.fill();

      // Sprite
      let spriteName = (s.activity === "idle" && s.isBlinking) ? "blink" : frames[s.frameIndex % frames.length];
      const sprite = getSprite(spriteName);
      if (sprite) {
        ctx.drawImage(sprite, s.x + s.shakeX, floorY - s.bounceY);
      }

      // Particles
      for (const p of s.particles) {
        ctx.globalAlpha = p.opacity;
        ctx.font = `${p.size}px "Courier New", monospace`;
        ctx.fillStyle = p.color;
        ctx.fillText(p.text, p.x, p.y);
      }
      ctx.globalAlpha = 1;

      af = requestAnimationFrame(tick);
    };

    af = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(af);
  }, [getSprite]);

  const btnStyle = (active) => ({
    background: active ? "rgba(215,119,87,0.25)" : "rgba(215,119,87,0.08)",
    border: `1px solid rgba(215,119,87,${active ? "0.5" : "0.2"})`,
    borderRadius: 10, padding: "10px 14px",
    color: active ? "#E8A070" : "#D77757", cursor: activity !== "idle" && !active ? "not-allowed" : "pointer",
    fontFamily: '"Courier New", monospace', fontSize: 12,
    transition: "all 0.15s", opacity: activity !== "idle" && !active ? 0.4 : 1,
    lineHeight: 1.3, textAlign: "center",
  });

  return (
    <div style={{
      display:"flex", flexDirection:"column", alignItems:"center", gap:14,
      fontFamily:'"Courier New", monospace',
      background:"linear-gradient(180deg, #1a1520 0%, #2a2035 50%, #1e1828 100%)",
      minHeight:"100vh", padding:"24px 16px", color:"#e8ddd0",
    }}>
      <div style={{ fontSize:11, letterSpacing:3, textTransform:"uppercase", color:"#D7775760" }}>
        clawd activities demo
      </div>

      {/* Viewport */}
      <div style={{
        background:"linear-gradient(180deg, #2a2540 0%, #342a45 60%, #3d3350 100%)",
        borderRadius:16, padding:2,
        boxShadow:"0 0 40px rgba(215,119,87,0.08), inset 0 1px 0 rgba(255,255,255,0.05)",
        border:"1px solid rgba(215,119,87,0.15)",
      }}>
        <div style={{ borderRadius:14, overflow:"hidden", background:"linear-gradient(180deg, #1e1830 0%, #252040 100%)" }}>
          <canvas ref={canvasRef} width={W} height={H} style={{ display:"block", imageRendering:"pixelated" }} />
        </div>
      </div>

      {/* Message */}
      <div style={{
        fontSize:14, color:"#D77757", letterSpacing:0.5, minHeight:22,
        transition:"opacity 0.3s", opacity: message ? 1 : 0.3,
      }}>
        {message || "ожидает..."}
      </div>

      {/* Activity buttons */}
      <div style={{ display:"flex", gap:8, flexWrap:"wrap", justifyContent:"center", maxWidth: 480 }}>
        {[
          { key:"reading", icon:"📖", label:"читать\nкнигу" },
          { key:"magic", icon:"🪄", label:"взмах\nпалочкой" },
          { key:"working", icon:"💻", label:"работать\nза ноутом" },
          { key:"fishing", icon:"🎣", label:"ловить\nрыбу" },
        ].map(({ key, icon, label }) => (
          <button
            key={key}
            onClick={() => { if (activity === "idle") startActivity(key); }}
            disabled={activity !== "idle"}
            style={btnStyle(activity === key)}
            onMouseEnter={e => { if (activity === "idle") { e.target.style.background = "rgba(215,119,87,0.2)"; e.target.style.borderColor = "rgba(215,119,87,0.5)"; }}}
            onMouseLeave={e => { if (activity !== key) { e.target.style.background = "rgba(215,119,87,0.08)"; e.target.style.borderColor = "rgba(215,119,87,0.2)"; }}}
          >
            <div style={{ fontSize:22, marginBottom:4 }}>{icon}</div>
            <div style={{ whiteSpace:"pre-line" }}>{label}</div>
          </button>
        ))}
      </div>

      <div style={{ fontSize:10, color:"#5a4a60", marginTop:4, textAlign:"center", lineHeight:1.7, maxWidth:420 }}>
        каждая активность — последовательность фаз с отдельными спрайтами,<br/>
        частицами и таймингами. рыбалка вытаскивает случайные предметы :)
      </div>
    </div>
  );
}
