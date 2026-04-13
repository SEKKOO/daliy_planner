#!/usr/bin/env python3
from __future__ import annotations

import io
import json
import os
import sqlite3
import subprocess
import tempfile
import zipfile
from datetime import date, datetime, timedelta
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from shutil import which
from urllib.parse import parse_qs, quote, urlparse
from xml.sax.saxutils import escape


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "planner.db"
HOST = "0.0.0.0"
PORT = 8000
CODEX_BIN = which("codex") or "/opt/homebrew/bin/codex"
NODE_BIN = which("node") or "/opt/homebrew/bin/node"
DEFAULT_PAGE_SETTINGS = {
    "weekly_monday_am": "",
    "weekly_monday_pm": "",
    "weekly_tuesday_am": "",
    "weekly_tuesday_pm": "",
    "weekly_wednesday_am": "",
    "weekly_wednesday_pm": "",
    "weekly_thursday_am": "",
    "weekly_thursday_pm": "",
    "weekly_friday_am": "",
    "weekly_friday_pm": "",
    "weekly_saturday_am": "",
    "weekly_saturday_pm": "",
    "weekly_sunday_am": "",
    "weekly_sunday_pm": "",
    "weekly_other_pending": "",
}
WEEKLY_PLAN_KEYS = tuple(DEFAULT_PAGE_SETTINGS.keys())
DEFAULT_UI_SETTINGS = {
    "background_image": "",
    "region_opacity": 0.94,
}


INDEX_HTML = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>每日计划台账</title>
  <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0' y1='0' x2='1' y2='1'%3E%3Cstop offset='0' stop-color='%232e77d0'/%3E%3Cstop offset='1' stop-color='%2358a8ff'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect x='10' y='8' width='44' height='48' rx='12' fill='url(%23g)'/%3E%3Crect x='16' y='17' width='32' height='26' rx='7' fill='white' fill-opacity='.96'/%3E%3Crect x='20' y='22' width='18' height='4' rx='2' fill='%23d5e7ff'/%3E%3Crect x='20' y='30' width='12' height='4' rx='2' fill='%23d5e7ff'/%3E%3Cpath d='M23 38l5 5 11-12' fill='none' stroke='%232e77d0' stroke-width='4.2' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E">
  <style>
    :root {
      color-scheme: light;
      --bg: #eef5ff;
      --bg-soft: #f8fbff;
      --bg-deep: #e2edfb;
      --panel: rgba(255, 255, 255, 0.46);
      --panel-strong: rgba(255, 255, 255, 0.3);
      --panel-soft: rgba(244, 249, 255, 0.2);
      --ink: #12304f;
      --muted: #5c7592;
      --line: rgba(49, 102, 173, 0.16);
      --line-soft: rgba(49, 102, 173, 0.1);
      --accent: #2e77d0;
      --accent-deep: #1e58a0;
      --accent-soft: #dfeeff;
      --accent-glow: rgba(46, 119, 208, 0.14);
      --accent-strong: #1957ab;
      --ok: #1e8a64;
      --warn: #b17610;
      --danger: #be3c45;
      --shadow: 0 18px 45px rgba(37, 90, 160, 0.12);
      --shadow-strong: 0 24px 55px rgba(30, 88, 160, 0.11), 0 6px 18px rgba(46, 119, 208, 0.06);
      --card-shadow: 0 14px 30px rgba(35, 86, 156, 0.09);
      --button-shadow: 0 10px 20px rgba(46, 119, 208, 0.12);
      --radius: 24px;
      --fs-xxs: 11px;
      --fs-xs: 12px;
      --fs-sm: 13px;
      --fs-md: 14px;
      --fs-lg: 16px;
    }

    body[data-theme="dark"] {
      color-scheme: dark;
      --bg: #0f1726;
      --bg-soft: #162033;
      --bg-deep: #0b1220;
      --panel: rgba(20, 31, 49, 0.5);
      --panel-strong: rgba(26, 39, 64, 0.34);
      --panel-soft: rgba(26, 39, 64, 0.22);
      --ink: #e7f0ff;
      --muted: #98abc9;
      --line: rgba(128, 170, 231, 0.18);
      --line-soft: rgba(128, 170, 231, 0.12);
      --accent: #68a9ff;
      --accent-deep: #c4deff;
      --accent-soft: rgba(75, 126, 205, 0.22);
      --accent-glow: rgba(104, 169, 255, 0.22);
      --accent-strong: #90c2ff;
      --ok: #4fd3a0;
      --warn: #f2bf5c;
      --danger: #ff7d88;
      --shadow: 0 22px 46px rgba(3, 8, 20, 0.42);
      --shadow-strong: 0 24px 55px rgba(3, 8, 20, 0.46), 0 6px 18px rgba(104, 169, 255, 0.08);
      --card-shadow: 0 16px 30px rgba(3, 8, 20, 0.34);
      --button-shadow: 0 10px 20px rgba(6, 14, 28, 0.28);
    }

    html {
      min-height: 100%;
      background:
        radial-gradient(circle at 14% 10%, rgba(107, 176, 255, 0.16), transparent 24%),
        radial-gradient(circle at 82% 92%, rgba(58, 122, 203, 0.12), transparent 26%),
        linear-gradient(180deg, #f9fcff 0%, #eef5ff 40%, #dce8f8 100%);
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      position: relative;
      overflow-x: hidden;
      color: var(--ink);
      font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
      background: transparent;
      padding: 34px 16px 46px;
      transition: background 0.25s ease, color 0.2s ease;
      -webkit-font-smoothing: antialiased;
      text-rendering: optimizeLegibility;
    }

    .page-background {
      position: fixed;
      inset: -12vh 0 -12vh 0;
      z-index: 0;
      pointer-events: none;
      background-color: var(--bg-deep);
      background-repeat: no-repeat, no-repeat, no-repeat, no-repeat;
      background-position: center, center, center, center;
      background-size: cover, cover, auto, auto;
      transform: translate3d(0, 0, 0) scale3d(1, 1, 1);
      transform-origin: center top;
      transition: background-image 0.25s ease, background-color 0.25s ease, transform 0.2s ease-out, filter 0.2s ease-out;
      will-change: transform, filter;
    }

    body::before,
    body::after {
      content: "";
      position: fixed;
      inset: auto;
      pointer-events: none;
      z-index: 0;
    }

    body::before {
      top: 108px;
      right: -100px;
      width: 300px;
      height: 300px;
      border-radius: 36% 64% 60% 40%;
      background: radial-gradient(circle at 35% 35%, rgba(46, 119, 208, 0.14), rgba(46, 119, 208, 0.02) 68%, transparent 74%);
      filter: blur(12px);
    }

    body::after {
      left: -150px;
      bottom: 42px;
      width: 260px;
      height: 260px;
      border-radius: 50%;
      background: radial-gradient(circle, rgba(94, 168, 255, 0.1), transparent 70%);
    }

    .shell {
      width: min(1220px, calc(100vw - 32px));
      margin: 0 auto;
      position: relative;
      z-index: 1;
    }

    .page-theme-toggle {
      position: fixed;
      top: 16px;
      right: 20px;
      z-index: 20;
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 8px;
    }

    .visual-file-name {
      min-height: 40px;
      padding: 10px 12px;
      border-radius: 14px;
      border: 1px dashed rgba(49, 102, 173, 0.18);
      background: rgba(246, 250, 255, 0.88);
      color: var(--muted);
      font-size: var(--fs-xs);
      line-height: 1.5;
      overflow-wrap: anywhere;
    }

    .background-settings-button {
      min-width: 108px;
    }

    .background-settings-menu {
      width: min(360px, calc(100vw - 24px));
      padding: 16px;
      border-radius: 22px;
      border: 1px solid rgba(255,255,255,0.24);
      background:
        linear-gradient(180deg, rgba(255,255,255,0.42), rgba(244,249,255,0.24)),
        linear-gradient(135deg, rgba(46,119,208,0.04), transparent 72%);
      box-shadow: 0 18px 34px rgba(41, 91, 156, 0.08);
      backdrop-filter: blur(16px);
      display: grid;
      gap: 14px;
    }

    .background-settings-menu[hidden] {
      display: none;
    }

    .background-settings-head {
      display: grid;
      gap: 4px;
    }

    .background-settings-title {
      margin: 0;
      font-size: 15px;
      font-weight: 700;
      color: var(--accent-strong);
    }

    .background-settings-note {
      margin: 0;
      color: var(--muted);
      font-size: var(--fs-xs);
      line-height: 1.6;
    }

    .background-settings-actions {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }

    .background-settings-group {
      display: grid;
      gap: 10px;
      padding: 14px;
      border-radius: 18px;
      border: 1px solid rgba(255,255,255,0.18);
      background: linear-gradient(180deg, rgba(255,255,255,0.18), rgba(247,250,255,0.08));
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.18);
    }

    .background-settings-group-title {
      font-size: var(--fs-xs);
      font-weight: 700;
      color: var(--accent-deep);
      letter-spacing: 0.02em;
    }

    .visual-slider-row {
      display: grid;
      gap: 8px;
    }

    .visual-slider-top {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      font-size: var(--fs-xs);
      color: var(--accent-deep);
      font-weight: 700;
    }

    .visual-slider-value {
      min-width: 46px;
      text-align: right;
      color: var(--muted);
      font-weight: 600;
    }

    .visual-slider {
      accent-color: var(--accent);
      padding: 0;
      min-height: 0;
      box-shadow: none;
      background: transparent;
      border: 0;
    }

    .hero {
      display: grid;
      grid-template-columns: 1fr;
      gap: 18px;
      margin: 22px 0 22px;
      width: 100%;
    }

    .hero-card,
    .panel {
      background: var(--panel);
      border-radius: var(--radius);
      border: 1px solid rgba(255, 255, 255, 0.28);
      box-shadow: 0 18px 40px rgba(38, 86, 150, 0.06);
      backdrop-filter: blur(20px) saturate(120%);
      width: 100%;
    }

    .hero-card {
      position: relative;
      overflow: hidden;
      padding: 22px;
    }

    .panel {
      position: relative;
      overflow: hidden;
      padding: 26px;
    }

    .hero-card::before,
    .panel::before {
      content: "";
      position: absolute;
      inset: 0 0 auto 0;
      height: 1px;
      background: linear-gradient(90deg, rgba(46, 119, 208, 0.2), rgba(46, 119, 208, 0.02));
      pointer-events: none;
    }

    .hero-card::after {
      content: "";
      position: absolute;
      right: -44px;
      bottom: -60px;
      width: 220px;
      height: 220px;
      border-radius: 44px;
      transform: rotate(18deg);
      background: linear-gradient(140deg, rgba(46, 119, 208, 0.16), rgba(126, 192, 255, 0.08));
    }

    .eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 6px 10px;
      border-radius: 999px;
      background: var(--accent-soft);
      color: var(--accent-deep);
      font-size: var(--fs-xs);
      letter-spacing: 0.06em;
    }

    h1 {
      margin: 12px 0 8px;
      font-size: clamp(22px, 3vw, 30px);
      line-height: 1.15;
      letter-spacing: -0.03em;
    }

    .lead {
      margin: 0;
      max-width: 55ch;
      color: var(--muted);
      line-height: 1.65;
      font-size: var(--fs-sm);
    }

    .hero-side {
      display: block;
      padding: 0;
    }

    .metric,
    .weekly-plan {
      padding: 20px;
      border-radius: 22px;
      background:
        linear-gradient(180deg, rgba(255,255,255,0.28), rgba(244,249,255,0.14)),
        linear-gradient(135deg, rgba(46,119,208,0.06), rgba(46,119,208,0));
      border: 1px solid rgba(255,255,255,0.22);
      box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.2),
        0 14px 30px rgba(35, 86, 156, 0.05);
      backdrop-filter: blur(18px) saturate(120%);
    }

    .weekly-plan-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
      margin-bottom: 16px;
      padding-bottom: 12px;
      border-bottom: 1px solid rgba(49, 102, 173, 0.09);
    }

    .weekly-plan-meta {
      display: grid;
      gap: 4px;
    }

    .weekly-plan-subtitle {
      color: var(--accent-strong);
      font-size: 15px;
      font-weight: 700;
      line-height: 1.5;
      max-width: 72ch;
    }

    .weekly-plan-actions {
      display: flex;
      gap: 8px;
      align-items: center;
      flex-wrap: wrap;
      justify-content: flex-end;
    }

    .weekly-plan-saved-at {
      font-size: var(--fs-xs);
      color: var(--muted);
      white-space: nowrap;
      padding-right: 4px;
    }

    .theme-toggle {
      min-width: 108px;
      justify-content: center;
      background: linear-gradient(180deg, rgba(255,255,255,0.96), rgba(246,250,255,0.88));
      color: var(--accent-deep);
      border: 1px solid rgba(49, 102, 173, 0.12);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.48);
      backdrop-filter: blur(10px);
    }

    .tiny-btn {
      padding: 7px 12px;
      font-size: 12px;
      line-height: 1;
    }

    .weekly-board-scroll {
      overflow-x: auto;
      padding-bottom: 4px;
      border-radius: 20px;
      background: linear-gradient(180deg, rgba(255, 255, 255, 0.18), rgba(240, 247, 255, 0.08));
      border: 1px solid rgba(255,255,255,0.18);
      padding: 12px;
      backdrop-filter: blur(12px);
    }

    .weekly-board {
      min-width: 1280px;
      display: grid;
      grid-template-columns: 62px repeat(5, minmax(96px, 0.8fr)) repeat(2, minmax(82px, 0.68fr)) minmax(230px, 1.2fr);
      gap: 8px;
      align-items: stretch;
    }

    .weekly-head,
    .weekly-label,
    .weekly-cell,
    .weekly-pending {
      border-radius: 18px;
      border: 1px solid var(--line-soft);
      background: linear-gradient(180deg, var(--panel-strong), var(--panel-soft));
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.18), var(--card-shadow);
    }

    .weekly-corner {
      border-radius: 18px;
      background: linear-gradient(135deg, var(--accent-soft), transparent);
      border: 1px dashed var(--line);
    }

    .weekly-head {
      padding: 12px 10px;
      text-align: center;
      font-size: var(--fs-xs);
      font-weight: 700;
      color: var(--accent-deep);
    }

    .weekly-head.workday,
    .weekly-cell.workday {
      background:
        linear-gradient(180deg, rgba(236, 245, 255, 0.96), rgba(248, 251, 255, 0.92));
    }

    .weekly-head.weekend,
    .weekly-cell.weekend {
      background:
        linear-gradient(180deg, rgba(255, 244, 230, 0.94), rgba(255, 249, 240, 0.9));
      border-color: rgba(214, 154, 72, 0.18);
    }

    .weekly-head.pending-head,
    .weekly-pending {
      background:
        linear-gradient(180deg, rgba(232, 244, 255, 0.96), rgba(242, 249, 255, 0.94));
    }

    .weekly-label {
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 10px 4px;
      font-size: var(--fs-xs);
      font-weight: 700;
      color: var(--accent-deep);
      letter-spacing: 0.04em;
    }

    .weekly-cell {
      padding: 10px;
    }

    .weekly-cell textarea,
    .weekly-pending textarea {
      min-height: 88px;
      height: 100%;
      border-radius: 14px;
    }

    .weekly-pending {
      grid-column: 9;
      grid-row: 2 / span 2;
      padding: 10px;
    }

    .weekly-pending textarea {
      min-height: 188px;
    }

    .metric-label {
      font-size: var(--fs-xxs);
      color: var(--muted);
      letter-spacing: 0.08em;
      text-transform: uppercase;
      margin-bottom: 6px;
    }

    .metric-value {
      font-size: var(--fs-lg);
      font-weight: 700;
      margin-bottom: 4px;
    }

    .metric-note {
      color: var(--muted);
      line-height: 1.55;
      font-size: var(--fs-sm);
    }

    .layout {
      display: grid;
      grid-template-columns: 1fr;
      gap: 20px;
      align-items: start;
      width: 100%;
    }

    .panel {
      padding: 26px;
    }

    .panel-header {
      display: flex;
      justify-content: space-between;
      align-items: flex-end;
      gap: 14px;
      margin-bottom: 18px;
    }

    .panel-title {
      margin: 0;
      font-size: 15px;
      letter-spacing: 0;
      font-weight: 700;
      color: var(--accent-strong);
    }

    .panel-subtitle {
      margin: 5px 0 0;
      color: var(--muted);
      font-size: var(--fs-sm);
      line-height: 1.6;
    }

    .toolbar-title .panel-subtitle {
      max-width: 58ch;
    }

    .toolbar,
    .field-row,
    .month-toolbar,
    .stats-grid {
      display: grid;
      gap: 14px;
    }

    .toolbar {
      grid-template-columns: minmax(0, 1fr) auto;
      align-items: center;
      margin-bottom: 14px;
      padding: 16px 18px;
      border-radius: 20px;
      position: relative;
      overflow: hidden;
      background:
        linear-gradient(180deg, rgba(255,255,255,0.34), rgba(246,250,255,0.16)),
        linear-gradient(135deg, rgba(46,119,208,0.04), transparent 70%);
      border: 1px solid rgba(255,255,255,0.22);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.24), 0 8px 18px rgba(46, 119, 208, 0.03);
      backdrop-filter: blur(16px);
    }

    .toolbar::after {
      content: "";
      position: absolute;
      inset: 0 auto 0 0;
      width: 4px;
      background: linear-gradient(180deg, var(--accent), rgba(46, 119, 208, 0.12));
    }

    .toolbar-title {
      min-width: 0;
    }

    .toolbar-title .panel-title {
      text-transform: none;
      letter-spacing: 0;
      font-size: 16px;
      line-height: 1.45;
    }

    .toolbar-date {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 8px 12px;
      border-radius: 16px;
      border: 1px solid rgba(255,255,255,0.18);
      background: linear-gradient(180deg, rgba(255,255,255,0.22), rgba(244,249,255,0.08));
      white-space: nowrap;
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.12);
      backdrop-filter: blur(12px);
    }

    .toolbar-date label {
      margin: 0;
      font-size: var(--fs-xs);
      color: var(--accent-deep);
    }

    .toolbar-date input {
      width: 154px;
      min-width: 154px;
      padding: 6px 8px;
      border-radius: 12px;
    }

    .editor-list-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      margin: 0 0 14px;
      padding-bottom: 10px;
      border-bottom: 1px solid rgba(49, 102, 173, 0.08);
    }

    .editor-list-title {
      margin: 0;
      font-size: 16px;
      font-weight: 700;
      color: var(--accent-strong);
    }

    .editor-list-note {
      margin: 4px 0 0;
      color: var(--muted);
      font-size: var(--fs-sm);
      line-height: 1.55;
    }

    .editor-workbench {
      margin-top: 14px;
      padding: 16px;
      border-radius: 22px;
      border: 1px solid rgba(49, 102, 173, 0.1);
      background:
        linear-gradient(180deg, rgba(255,255,255,0.28), rgba(244,249,255,0.12)),
        linear-gradient(135deg, rgba(46,119,208,0.035), transparent 72%);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.18), 0 12px 28px rgba(46, 119, 208, 0.04);
      backdrop-filter: blur(18px);
    }

    .week-toolbar {
      display: grid;
      grid-template-columns: auto minmax(0, 1fr) auto;
      gap: 12px;
      align-items: center;
      margin-bottom: 12px;
      padding: 12px;
      border-radius: 20px;
      background:
        linear-gradient(180deg, rgba(255,255,255,0.24), rgba(246,250,255,0.1)),
        linear-gradient(135deg, rgba(46,119,208,0.03), transparent);
      border: 1px solid rgba(255,255,255,0.18);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.16);
      backdrop-filter: blur(14px);
    }

    .week-strip {
      display: grid;
      grid-template-columns: repeat(7, minmax(110px, 1fr));
      gap: 10px;
    }

    .week-btn {
      border-radius: 18px;
      padding: 8px 10px;
      border: 1px solid var(--line);
      background: linear-gradient(180deg, var(--panel-strong), var(--panel-soft));
      color: var(--ink);
      text-align: left;
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.16);
      transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease, background 0.18s ease;
    }

    .week-btn.weekend {
      background: linear-gradient(180deg, rgba(255, 244, 230, 0.94), rgba(255, 249, 240, 0.9));
      border-color: rgba(214, 154, 72, 0.18);
    }

    .week-btn:hover {
      border-color: rgba(46, 119, 208, 0.24);
      box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.85),
        0 10px 18px rgba(46, 119, 208, 0.08);
    }

    .week-btn.active {
      background: linear-gradient(135deg, var(--accent), #56a8ff);
      color: #fff;
      border-color: transparent;
      box-shadow: 0 10px 24px rgba(46, 119, 208, 0.2);
    }

    .week-btn.weekend.active {
      background: linear-gradient(135deg, #f0a14a, #f5bf76);
      color: #fff;
      border-color: transparent;
      box-shadow: 0 10px 24px rgba(214, 154, 72, 0.22);
    }

    .week-btn-name {
      display: block;
      font-size: var(--fs-xs);
      font-weight: 700;
      margin-bottom: 2px;
    }

    .week-btn-date {
      display: block;
      font-size: var(--fs-xxs);
      opacity: 0.9;
    }

    .week-range {
      font-size: var(--fs-xs);
      color: var(--muted);
      margin-bottom: 0;
      display: none;
    }

    .field-row {
      grid-template-columns: repeat(3, minmax(0, 1fr));
    }

    .month-toolbar {
      grid-template-columns: 1fr auto auto;
      align-items: end;
      margin-bottom: 16px;
      padding: 14px;
      border-radius: 20px;
      background:
        linear-gradient(180deg, rgba(255,255,255,0.26), rgba(243,249,255,0.1)),
        linear-gradient(135deg, rgba(46,119,208,0.06), transparent 75%);
      border: 1px solid rgba(255,255,255,0.2);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.16);
      backdrop-filter: blur(16px);
    }

    .stats-grid {
      grid-template-columns: repeat(3, minmax(0, 1fr));
      margin-bottom: 14px;
    }

    .field,
    .stack {
      display: grid;
      gap: 8px;
    }

    label {
      font-size: var(--fs-xs);
      font-weight: 700;
    }

    input,
    select,
    textarea,
    button {
      font: inherit;
      font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
    }

    input,
    select,
    textarea {
      width: 100%;
      border-radius: 14px;
      border: 1px solid rgba(255,255,255,0.26);
      background: linear-gradient(180deg, rgba(255,255,255,0.24), rgba(247,250,255,0.12));
      color: var(--ink);
      padding: 9px 11px;
      font-size: var(--fs-xs);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.14);
      backdrop-filter: blur(10px);
      transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease, background 0.2s ease;
    }

    input::placeholder,
    textarea::placeholder {
      color: var(--muted);
      opacity: 0.82;
    }

    input:focus,
    select:focus,
    textarea:focus {
      outline: none;
      border-color: rgba(46, 119, 208, 0.58);
      box-shadow: 0 0 0 4px rgba(46, 119, 208, 0.12);
      transform: translateY(-1px);
    }

    textarea {
      min-height: 72px;
      resize: vertical;
      line-height: 1.6;
      font-family: "PingFang SC", "Microsoft YaHei", sans-serif;
      font-weight: 400;
      letter-spacing: 0;
    }

    button {
      border: 0;
      border-radius: 14px;
      padding: 9px 14px;
      font-size: var(--fs-xxs);
      font-weight: 600;
      letter-spacing: 0.01em;
      cursor: pointer;
      transition: transform 0.18s ease, box-shadow 0.18s ease, background-color 0.18s ease, border-color 0.18s ease, color 0.18s ease, opacity 0.18s ease;
      white-space: nowrap;
    }

    button:hover {
      opacity: 0.98;
      transform: translateY(-0.5px);
      box-shadow: var(--button-shadow);
    }

    .primary {
      background: linear-gradient(135deg, #2b74cd, #4c97f6);
      color: #fff;
      border: 1px solid rgba(46, 119, 208, 0.18);
      box-shadow: 0 10px 18px rgba(46, 119, 208, 0.14);
    }

    .secondary {
      background: linear-gradient(180deg, rgba(255,255,255,0.24), rgba(245,249,255,0.12));
      color: var(--ink);
      border: 1px solid rgba(255,255,255,0.22);
      backdrop-filter: blur(10px);
    }

    .danger {
      background: linear-gradient(180deg, #fff4f4, #ffe9ea);
      color: var(--danger);
      border: 1px solid rgba(190, 60, 69, 0.16);
    }

    .soft {
      background: linear-gradient(180deg, rgba(235,245,255,0.28), rgba(229, 240, 255, 0.14));
      color: var(--accent-deep);
      border: 1px solid rgba(255,255,255,0.2);
      backdrop-filter: blur(10px);
    }

    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-top: 16px;
    }

    .editor-actions {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 14px;
      flex-wrap: wrap;
      margin-top: 16px;
      padding: 12px 14px;
      border-radius: 20px;
      background: linear-gradient(180deg, rgba(247, 251, 255, 0.26), rgba(242, 248, 255, 0.14));
      border: 1px solid rgba(255,255,255,0.2);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.16);
      backdrop-filter: blur(14px);
    }

    .editor-actions .actions {
      margin-top: 0;
    }

    .status {
      min-height: 24px;
      margin-top: 10px;
      color: var(--muted);
      font-size: var(--fs-xs);
      padding-left: 2px;
    }

    .status.success { color: var(--ok); }
    .status.warning { color: var(--warn); }
    .status.error { color: var(--danger); }

    .list-editor,
    .recent-list,
    .month-list {
      display: grid;
      gap: 12px;
    }

    .item-card,
    .entry-card,
    .stat-card {
      border-radius: 20px;
      border: 1px solid rgba(255,255,255,0.22);
      background: linear-gradient(180deg, rgba(255,255,255,0.2), rgba(244,249,255,0.1));
      box-shadow: 0 12px 24px rgba(35, 86, 156, 0.04);
      backdrop-filter: blur(14px);
    }

    .table-scroll {
      overflow-x: visible;
      padding: 0;
      border-radius: 18px;
      border: 0;
      background: transparent;
      box-shadow: none;
    }

    .table-editor {
      width: 100%;
      min-width: 0;
      border-radius: 18px;
      border: 1px solid rgba(255,255,255,0.22);
      background: linear-gradient(180deg, rgba(255,255,255,0.22), rgba(246,250,255,0.12));
      overflow: hidden;
      box-shadow: 0 14px 28px rgba(43, 91, 158, 0.04);
      backdrop-filter: blur(18px);
    }

    .table-header,
    .item-row {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 0.92fr) minmax(0, 1.38fr) minmax(0, 1.04fr) 56px;
      gap: 0;
      align-items: stretch;
    }

    .table-header {
      background:
        linear-gradient(180deg, rgba(239, 246, 255, 0.28), rgba(230, 239, 251, 0.14)),
        linear-gradient(90deg, rgba(46,119,208,0.05), transparent);
      border-bottom: 1px solid rgba(255,255,255,0.16);
      font-size: var(--fs-xs);
      font-weight: 700;
      color: var(--accent-deep);
      letter-spacing: 0.02em;
      position: sticky;
      top: 0;
      z-index: 1;
    }

    .table-header > div:last-child,
    .item-row > div:last-child {
      border-right: 0;
    }

    .table-header > div {
      min-width: 0;
      padding: 10px 10px;
      border-right: 1px solid rgba(49, 102, 173, 0.08);
      display: flex;
      align-items: center;
      justify-content: center;
      line-height: 1.15;
    }

    .item-row > div {
      padding: 12px 10px;
      border-right: 1px solid rgba(49, 102, 173, 0.08);
      min-width: 0;
    }

    .item-row {
      border-bottom: 1px solid rgba(255,255,255,0.14);
      background: rgba(255, 255, 255, 0.14);
      transition: background 0.18s ease, box-shadow 0.18s ease;
    }

    .item-row:nth-child(even) {
      background: rgba(249, 252, 255, 0.08);
    }

    .item-row:hover {
      background: rgba(242, 248, 255, 0.2);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.22);
    }

    .item-row:last-child {
      border-bottom: 0;
    }

    .item-row input,
    .item-row select,
    .item-row textarea {
      min-width: 0;
      border-radius: 12px;
      padding: 10px 12px;
      background: linear-gradient(180deg, rgba(255,255,255,0.24), rgba(248,251,255,0.12));
    }

    .item-row textarea {
      min-height: 92px;
      resize: vertical;
      line-height: 1.55;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }

    .base-info-cell,
    .service-content-cell,
    .issue-risk-cell {
      display: flex;
      align-items: stretch;
    }

    .base-info-stack,
    .service-content-stack,
    .issue-risk-stack {
      width: 100%;
      display: grid;
      gap: 8px;
    }

    .issue-risk-stack {
      gap: 6px;
    }

    .base-info-line,
    .service-content-line,
    .issue-risk-line {
      display: grid;
      grid-template-columns: 64px minmax(0, 1fr);
      align-items: center;
      gap: 6px;
      font-size: var(--fs-xs);
      color: var(--accent-deep);
    }

    .base-info-line span,
    .service-content-line span,
    .issue-risk-line span {
      white-space: nowrap;
    }

    .base-info-line input,
    .base-info-line select,
    .service-content-line input,
    .service-content-line select,
    .issue-risk-line textarea {
      width: 100%;
      padding: 8px 10px;
      font-size: var(--fs-xs);
    }

    .issue-risk-line {
      align-items: start;
    }

    .issue-risk-line textarea {
      min-height: 52px;
      padding: 8px 10px;
      resize: vertical;
      line-height: 1.45;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }

    .weekly-plan textarea {
      border-radius: 14px;
    }

    .mini-help {
      color: var(--muted);
      font-size: var(--fs-xs);
      line-height: 1.55;
      margin-top: 10px;
      padding: 10px 12px;
      border-radius: 14px;
      border: 1px dashed rgba(49, 102, 173, 0.12);
      background: rgba(241, 248, 255, 0.82);
    }

    .table-empty {
      padding: 20px;
      color: var(--muted);
      line-height: 1.7;
    }

    .row-action {
      display: flex;
      align-items: center;
      justify-content: center;
      padding-left: 4px;
      padding-right: 4px;
    }

    .mini-btn {
      padding: 4px 5px;
      min-width: 0;
      border-radius: 8px;
      font-size: 10px;
      line-height: 1;
    }

    .entry-head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      margin-bottom: 14px;
    }

    .entry-date {
      font-weight: 700;
      font-size: var(--fs-md);
    }

    .entry-card {
      width: 100%;
      text-align: left;
      padding: 18px;
      position: relative;
      overflow: hidden;
      background: linear-gradient(180deg, rgba(255,255,255,0.22), rgba(246,250,255,0.12));
      transition: transform 0.18s ease, box-shadow 0.18s ease, border-color 0.18s ease;
    }

    .entry-card::before {
      content: "";
      position: absolute;
      inset: 0 auto 0 0;
      width: 4px;
      background: linear-gradient(180deg, var(--accent), rgba(46, 119, 208, 0.08));
    }

    .entry-card:hover {
      transform: translateY(-2px);
      border-color: rgba(46, 119, 208, 0.22);
      box-shadow: 0 16px 30px rgba(46, 119, 208, 0.08);
    }

    .entry-badges {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
    }

    .badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 6px 10px;
      border-radius: 999px;
      font-size: var(--fs-xxs);
      background: var(--accent-soft);
      color: var(--accent-deep);
    }

    .entry-snippet {
      margin-top: 10px;
      color: var(--muted);
      font-size: var(--fs-sm);
      line-height: 1.65;
      white-space: pre-wrap;
      display: -webkit-box;
      -webkit-line-clamp: 4;
      line-clamp: 4;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }

    .entry-meta {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      margin-top: 12px;
      color: var(--muted);
      font-size: var(--fs-xxs);
    }

    .stat-card {
      padding: 16px;
      background:
        linear-gradient(180deg, rgba(255,255,255,0.22), rgba(246,250,255,0.12)),
        linear-gradient(135deg, rgba(46,119,208,0.04), transparent 72%);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.18), 0 10px 20px rgba(46, 119, 208, 0.03);
    }

    .stat-name {
      margin-bottom: 8px;
      font-size: var(--fs-xxs);
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: 0.06em;
    }

    .stat-value {
      font-size: var(--fs-lg);
      font-weight: 700;
      color: var(--accent-strong);
    }

    .empty {
      padding: 18px;
      border-radius: 20px;
      border: 1px dashed rgba(49, 102, 173, 0.18);
      background: linear-gradient(180deg, rgba(255,255,255,0.76), rgba(246,250,255,0.68));
      color: var(--muted);
      line-height: 1.7;
      font-size: var(--fs-sm);
    }

    body[data-theme="dark"] .hero-card::after {
      background: linear-gradient(140deg, rgba(104, 169, 255, 0.22), rgba(41, 67, 116, 0.08));
    }

    body[data-theme="dark"] .weekly-corner {
      background: linear-gradient(135deg, rgba(104, 169, 255, 0.18), rgba(24, 39, 63, 0.36));
    }

    body[data-theme="dark"] .weekly-head.workday,
    body[data-theme="dark"] .weekly-cell.workday {
      background: linear-gradient(180deg, rgba(29, 47, 75, 0.96), rgba(20, 32, 50, 0.94));
    }

    body[data-theme="dark"] .weekly-head.weekend,
    body[data-theme="dark"] .weekly-cell.weekend {
      background: linear-gradient(180deg, rgba(64, 49, 31, 0.9), rgba(43, 33, 22, 0.9));
      border-color: rgba(242, 191, 92, 0.18);
    }

    body[data-theme="dark"] .weekly-head.pending-head,
    body[data-theme="dark"] .weekly-pending {
      background: linear-gradient(180deg, rgba(28, 46, 74, 0.96), rgba(18, 31, 51, 0.94));
    }

    body[data-theme="dark"] .primary {
      background: linear-gradient(135deg, #4d93f7, #73b4ff);
      border-color: rgba(144, 194, 255, 0.18);
      color: #08131f;
    }

    body[data-theme="dark"] .page-theme-toggle {
      background: transparent;
      border-color: transparent;
      box-shadow: none;
    }

    body[data-theme="dark"] .background-settings-menu,
    body[data-theme="dark"] .background-settings-group {
      background:
        linear-gradient(180deg, rgba(24, 38, 60, 0.46), rgba(18, 29, 46, 0.24)),
        linear-gradient(135deg, rgba(104,169,255,0.04), transparent 72%);
      border-color: rgba(255,255,255,0.12);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.02);
    }

    body[data-theme="dark"] .visual-file-name {
      background: rgba(16, 25, 39, 0.84);
      border-color: rgba(128, 170, 231, 0.16);
      color: var(--muted);
    }

    body[data-theme="dark"] .theme-toggle {
      background: linear-gradient(180deg, rgba(31, 48, 75, 0.34), rgba(22, 35, 56, 0.18));
      border-color: rgba(255,255,255,0.12);
      color: var(--ink);
    }

    body[data-theme="dark"] .editor-workbench {
      background:
        linear-gradient(180deg, rgba(20, 31, 49, 0.36), rgba(17, 27, 42, 0.18)),
        linear-gradient(135deg, rgba(104,169,255,0.04), transparent 72%);
      border-color: rgba(128, 170, 231, 0.12);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.02), 0 14px 30px rgba(3, 8, 20, 0.16);
    }

    body[data-theme="dark"] input,
    body[data-theme="dark"] select,
    body[data-theme="dark"] textarea {
      background: linear-gradient(180deg, rgba(18, 29, 47, 0.24), rgba(14, 23, 37, 0.12));
      border-color: rgba(255,255,255,0.12);
      color: var(--ink);
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
    }

    body[data-theme="dark"] input::placeholder,
    body[data-theme="dark"] textarea::placeholder {
      color: rgba(152, 171, 201, 0.88);
    }

    body[data-theme="dark"] .item-row input,
    body[data-theme="dark"] .item-row select,
    body[data-theme="dark"] .item-row textarea,
    body[data-theme="dark"] .weekly-cell textarea,
    body[data-theme="dark"] .weekly-pending textarea {
      background: linear-gradient(180deg, rgba(15, 24, 39, 0.22), rgba(11, 18, 30, 0.12));
      border-color: rgba(255,255,255,0.1);
    }

    body[data-theme="dark"] .secondary {
      background: linear-gradient(180deg, rgba(31, 48, 75, 0.28), rgba(22, 35, 56, 0.14));
      border-color: rgba(255,255,255,0.12);
      color: var(--ink);
    }

    body[data-theme="dark"] .soft {
      background: linear-gradient(180deg, rgba(36, 64, 104, 0.3), rgba(25, 46, 76, 0.16));
      border-color: rgba(255,255,255,0.12);
      color: #d8e9ff;
    }

    body[data-theme="dark"] .danger {
      background: linear-gradient(180deg, rgba(79, 31, 38, 0.94), rgba(57, 22, 29, 0.92));
      border-color: rgba(255, 125, 136, 0.2);
      color: #ffd7db;
    }

    body[data-theme="dark"] .table-scroll {
      background: transparent;
    }

    body[data-theme="dark"] .toolbar,
    body[data-theme="dark"] .month-toolbar,
    body[data-theme="dark"] .week-toolbar,
    body[data-theme="dark"] .editor-actions,
    body[data-theme="dark"] .weekly-board-scroll,
    body[data-theme="dark"] .stat-card,
    body[data-theme="dark"] .empty {
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.03);
    }

    body[data-theme="dark"] .toolbar::after,
    body[data-theme="dark"] .entry-card::before {
      opacity: 0.9;
    }

    body[data-theme="dark"] .week-btn.weekend {
      background: linear-gradient(180deg, rgba(64, 49, 31, 0.9), rgba(43, 33, 22, 0.9));
      border-color: rgba(242, 191, 92, 0.18);
    }

    body[data-theme="dark"] .week-btn.weekend.active {
      background: linear-gradient(135deg, #c98837, #e0ad63);
      color: #fff8ef;
      border-color: rgba(242, 191, 92, 0.2);
      box-shadow: 0 10px 24px rgba(201, 136, 55, 0.26);
    }

    body[data-theme="dark"] .table-header {
      background: linear-gradient(180deg, rgba(32, 50, 79, 0.96), rgba(24, 39, 63, 0.94));
    }

    body[data-theme="dark"] .item-row {
      background: rgba(20, 31, 49, 0.84);
    }

    body[data-theme="dark"] .item-row:nth-child(even) {
      background: rgba(16, 26, 42, 0.9);
    }

    body[data-theme="dark"] .empty {
      background: rgba(19, 29, 45, 0.76);
    }

    @media (max-width: 980px) {
      .toolbar,
      .week-toolbar,
      .week-strip,
      .field-row,
      .month-toolbar,
      .stats-grid {
        grid-template-columns: 1fr;
      }

      .weekly-plan-head {
        align-items: flex-start;
        flex-direction: column;
      }

      .weekly-plan-actions {
        flex-wrap: wrap;
      }

      .page-theme-toggle {
        position: static;
        margin-bottom: 12px;
        align-items: stretch;
        gap: 10px;
      }

      .toolbar-date {
        width: 100%;
        justify-content: space-between;
      }

      .toolbar-date input {
        width: 100%;
        min-width: 0;
      }

      .editor-actions {
        align-items: stretch;
      }

      .hero {
        margin-top: 0;
      }

      body { padding: 16px 12px 28px; }
      .hero-card,
      .hero-side,
      .panel { padding: 18px; }

      .toolbar,
      .month-toolbar,
      .editor-actions,
      .editor-workbench,
      .background-settings-menu {
        padding: 14px;
      }

      .background-settings-menu {
        width: 100%;
      }

    }
</style>
</head>
<body>
  <div class="page-background" id="page-background" aria-hidden="true"></div>
  <main class="shell">
    <div class="page-theme-toggle">
      <button type="button" class="theme-toggle tiny-btn" id="theme-toggle">黑夜模式</button>
      <button type="button" class="theme-toggle tiny-btn background-settings-button" id="background-settings-button" aria-expanded="false" aria-controls="background-settings-menu">背景设置</button>
      <div class="background-settings-menu" id="background-settings-menu" hidden>
        <div class="background-settings-head">
          <h2 class="background-settings-title">背景与透明度</h2>
          <p class="background-settings-note">在这里设置本地背景图，并单独调整周计划区、每日编辑区、月度区域的透明度。</p>
        </div>
        <div class="background-settings-group">
          <div class="background-settings-group-title">页面背景图</div>
          <input id="background-image-input" type="file" accept="image/*" hidden>
          <div class="background-settings-actions">
            <button type="button" class="secondary" id="select-background-image">选择背景图</button>
            <button type="button" class="soft" id="clear-background-image">清除背景图</button>
          </div>
          <div class="visual-file-name" id="background-image-name">未设置背景图</div>
        </div>
        <div class="background-settings-group">
          <div class="visual-slider-row">
            <div class="visual-slider-top">
              <span>区域透明度</span>
              <span class="visual-slider-value" id="region-opacity-value">94%</span>
            </div>
            <input class="visual-slider" id="region-opacity-input" type="range" min="25" max="100" step="1" value="94">
          </div>
        </div>
      </div>
    </div>
    <section class="hero">
      <aside class="hero-card hero-side">
        <div class="weekly-plan" id="weekly-plan-box">
          <div class="weekly-plan-head">
            <div class="weekly-plan-meta">
              <div class="weekly-plan-subtitle" id="weekly-plan-range">每周工作安排：按周维护上午、下午安排，编辑后自动保存，并记录其他待定事项。</div>
            </div>
            <div class="weekly-plan-actions">
              <div class="weekly-plan-saved-at" id="weekly-plan-saved-at">最近保存：未保存</div>
              <button type="button" class="danger tiny-btn" id="clear-weekly-plan">清除本周安排</button>
            </div>
          </div>
            <div class="weekly-board-scroll">
            <div class="weekly-board">
              <div class="weekly-corner"></div>
              <div class="weekly-head workday">周一</div>
              <div class="weekly-head workday">周二</div>
              <div class="weekly-head workday">周三</div>
              <div class="weekly-head workday">周四</div>
              <div class="weekly-head workday">周五</div>
              <div class="weekly-head weekend">周六</div>
              <div class="weekly-head weekend">周日</div>
              <div class="weekly-head pending-head">其他待定安排</div>

              <div class="weekly-label">上午</div>
              <div class="weekly-cell workday"><textarea id="weekly-monday-am" placeholder="周一上午安排"></textarea></div>
              <div class="weekly-cell workday"><textarea id="weekly-tuesday-am" placeholder="周二上午安排"></textarea></div>
              <div class="weekly-cell workday"><textarea id="weekly-wednesday-am" placeholder="周三上午安排"></textarea></div>
              <div class="weekly-cell workday"><textarea id="weekly-thursday-am" placeholder="周四上午安排"></textarea></div>
              <div class="weekly-cell workday"><textarea id="weekly-friday-am" placeholder="周五上午安排"></textarea></div>
              <div class="weekly-cell weekend"><textarea id="weekly-saturday-am" placeholder="周六上午安排"></textarea></div>
              <div class="weekly-cell weekend"><textarea id="weekly-sunday-am" placeholder="周日上午安排"></textarea></div>
              <div class="weekly-pending"><textarea id="weekly-other-pending" placeholder="填写本周其他待定安排、临时事项或未定计划"></textarea></div>

              <div class="weekly-label">下午</div>
              <div class="weekly-cell workday"><textarea id="weekly-monday-pm" placeholder="周一下午安排"></textarea></div>
              <div class="weekly-cell workday"><textarea id="weekly-tuesday-pm" placeholder="周二下午安排"></textarea></div>
              <div class="weekly-cell workday"><textarea id="weekly-wednesday-pm" placeholder="周三下午安排"></textarea></div>
              <div class="weekly-cell workday"><textarea id="weekly-thursday-pm" placeholder="周四下午安排"></textarea></div>
              <div class="weekly-cell workday"><textarea id="weekly-friday-pm" placeholder="周五下午安排"></textarea></div>
              <div class="weekly-cell weekend"><textarea id="weekly-saturday-pm" placeholder="周六下午安排"></textarea></div>
              <div class="weekly-cell weekend"><textarea id="weekly-sunday-pm" placeholder="周日下午安排"></textarea></div>
            </div>
          </div>
        </div>
      </aside>
    </section>

    <section class="layout">
      <article class="panel" id="editor-panel">
        <div class="toolbar">
          <div class="toolbar-title">
            <h2 class="panel-title">每日计划编辑区：选择日期后，按列表填写当天的多个客户事项。</h2>
            <p class="panel-subtitle">像工作台一样集中维护日期、周切换、事项清单与保存动作，减少跳转和视觉干扰。</p>
          </div>
          <div class="toolbar-date">
            <label for="work-date">日期：</label>
            <input id="work-date" type="date" value="__INITIAL_DATE__" required>
          </div>
        </div>

        <div class="editor-workbench">
          <div class="week-range" id="week-range"></div>
          <div class="week-toolbar">
            <button type="button" class="secondary" id="prev-week">上一周</button>
            <div class="week-strip" id="week-strip"></div>
            <button type="button" class="secondary" id="next-week">下一周</button>
          </div>

          <div class="editor-list-head">
            <div>
              <h3 class="editor-list-title">每日事项清单</h3>
              <p class="editor-list-note">基础信息、服务内容、工作内容与遗留风险在同一工作台完成维护。</p>
            </div>
          </div>

          <div class="table-scroll">
            <div id="list-editor" class="list-editor"></div>
          </div>
          <div class="status" id="status"></div>

          <div class="editor-actions">
            <div class="actions">
              <button type="button" class="primary" id="save-entry">保存当天列表</button>
              <button type="button" class="secondary" id="export-daily-log">导出当日日志</button>
            </div>
            <div class="actions">
              <button type="button" class="soft" id="add-row">新增一行</button>
              <button type="button" class="secondary" id="reload-date">重新载入当天</button>
              <button type="button" class="secondary" id="clear-form">清空表单</button>
              <button type="button" class="danger" id="delete-entry">删除当天记录</button>
            </div>
          </div>
        </div>

        <div style="margin-top: 24px;">
          <div class="panel-header">
            <div>
              <h2 class="panel-title">最近记录</h2>
              <p class="panel-subtitle">点击任意一天，可快速回填当天的列表。</p>
            </div>
          </div>
          <div class="recent-list" id="recent-list">
            <div class="empty">正在载入最近记录...</div>
          </div>
        </div>
      </article>

      <section class="panel" id="month-panel">
        <div class="panel-header">
          <div>
            <h2 class="panel-title">按月查看与导出：查看当月事项数量、总工时，并导出 Excel。</h2>
          </div>
        </div>

        <div class="month-toolbar">
          <div class="field">
            <label for="month-picker">月份</label>
            <input id="month-picker" type="month" value="__INITIAL_MONTH__">
          </div>
          <button type="button" class="secondary" id="refresh-month">刷新月份</button>
          <button type="button" class="primary" id="export-month">导出 Excel</button>
        </div>

        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-name">当月日期数</div>
            <div class="stat-value" id="stat-days">0</div>
          </div>
          <div class="stat-card">
            <div class="stat-name">事项条数</div>
            <div class="stat-value" id="stat-items">0</div>
          </div>
          <div class="stat-card">
            <div class="stat-name">总工时</div>
            <div class="stat-value" id="stat-hours">0</div>
          </div>
        </div>

        <div class="month-list" id="month-list">
          <div class="empty">正在载入月份数据...</div>
        </div>
      </section>
    </section>
  </main>

  <script>
    const initialPageSettings = __INITIAL_SETTINGS__;
    const initialUiSettings = __INITIAL_UI_SETTINGS__;
    const itemTypeOptions = [
      "方案交流",
      "方案汇报",
      "POC1",
      "POC2",
      "交付",
      "服务",
      "基建"
    ];
    const serviceModeOptions = [
      "客户现场",
      "远程支持"
    ];
    const projectTypeOptions = [
      "A",
      "B+",
      "B",
      "C"
    ];
    const salesOptions = [
      "张泽恒",
      "秦瑞",
      "王晖",
      "王鑫泽"
    ];

    const dateInput = document.getElementById("work-date");
    const monthInput = document.getElementById("month-picker");
    const listEditor = document.getElementById("list-editor");
    const recentList = document.getElementById("recent-list");
    const monthList = document.getElementById("month-list");
    const statusEl = document.getElementById("status");
    const weekStrip = document.getElementById("week-strip");
    const weekRange = document.getElementById("week-range");
    const weeklyPlanRange = document.getElementById("weekly-plan-range");
    const prevWeekButton = document.getElementById("prev-week");
    const nextWeekButton = document.getElementById("next-week");
    const themeToggleButton = document.getElementById("theme-toggle");
    const backgroundSettingsButton = document.getElementById("background-settings-button");
    const backgroundSettingsMenu = document.getElementById("background-settings-menu");
    const weeklyPlanSavedAt = document.getElementById("weekly-plan-saved-at");
    const clearWeeklyPlanButton = document.getElementById("clear-weekly-plan");
    const weeklyPlanBox = document.getElementById("weekly-plan-box");
    const weeklyPlanPanel = weeklyPlanBox.closest(".hero-card");
    const weeklyBoardScroll = weeklyPlanBox.querySelector(".weekly-board-scroll");
    const editorPanel = document.getElementById("editor-panel");
    const monthPanel = document.getElementById("month-panel");
    const pageBackground = document.getElementById("page-background");
    const backgroundImageInput = document.getElementById("background-image-input");
    const selectBackgroundImageButton = document.getElementById("select-background-image");
    const clearBackgroundImageButton = document.getElementById("clear-background-image");
    const backgroundImageName = document.getElementById("background-image-name");
    const regionOpacityInput = document.getElementById("region-opacity-input");
    const regionOpacityValue = document.getElementById("region-opacity-value");

    const addRowButton = document.getElementById("add-row");
    const reloadButton = document.getElementById("reload-date");
    const clearButton = document.getElementById("clear-form");
    const deleteButton = document.getElementById("delete-entry");
    const saveButton = document.getElementById("save-entry");
    const exportDailyLogButton = document.getElementById("export-daily-log");
    const refreshMonthButton = document.getElementById("refresh-month");
    const exportMonthButton = document.getElementById("export-month");
    const THEME_STORAGE_KEY = "daily_planner_theme";
    const WEEKLY_PLAN_AUTOSAVE_DELAY_MS = 800;
    const VISUAL_SETTINGS_AUTOSAVE_DELAY_MS = 260;
    const MAX_BACKGROUND_IMAGE_SIZE_BYTES = 5 * 1024 * 1024;
    let currentWeeklyPlanWeekStart = "";
    let weeklyPlanAutosaveTimer = null;
    let visualSettingsAutosaveTimer = null;
    let weeklyPlanSaveSequence = 0;
    let isBackgroundSettingsOpen = false;
    let backgroundStretchFrame = 0;
    let currentUiSettings = normalizeUiSettings(initialUiSettings);
    const weeklyPlanSavedSnapshots = new Map();
    const weeklyPlanLatestRequestIds = new Map();
    const weeklyScheduleInputs = {
      weekly_monday_am: document.getElementById("weekly-monday-am"),
      weekly_monday_pm: document.getElementById("weekly-monday-pm"),
      weekly_tuesday_am: document.getElementById("weekly-tuesday-am"),
      weekly_tuesday_pm: document.getElementById("weekly-tuesday-pm"),
      weekly_wednesday_am: document.getElementById("weekly-wednesday-am"),
      weekly_wednesday_pm: document.getElementById("weekly-wednesday-pm"),
      weekly_thursday_am: document.getElementById("weekly-thursday-am"),
      weekly_thursday_pm: document.getElementById("weekly-thursday-pm"),
      weekly_friday_am: document.getElementById("weekly-friday-am"),
      weekly_friday_pm: document.getElementById("weekly-friday-pm"),
      weekly_saturday_am: document.getElementById("weekly-saturday-am"),
      weekly_saturday_pm: document.getElementById("weekly-saturday-pm"),
      weekly_sunday_am: document.getElementById("weekly-sunday-am"),
      weekly_sunday_pm: document.getElementById("weekly-sunday-pm"),
      weekly_other_pending: document.getElementById("weekly-other-pending")
    };

    function applyTheme(theme) {
      const nextTheme = theme === "dark" ? "dark" : "light";
      document.body.dataset.theme = nextTheme;
      themeToggleButton.textContent = nextTheme === "dark" ? "白天模式" : "黑夜模式";
      themeToggleButton.setAttribute("aria-label", nextTheme === "dark" ? "切换到白天模式" : "切换到黑夜模式");
      localStorage.setItem(THEME_STORAGE_KEY, nextTheme);
      applyVisualSettings(currentUiSettings);
    }

    function initTheme() {
      const savedTheme = localStorage.getItem(THEME_STORAGE_KEY);
      applyTheme(savedTheme || "light");
    }

    function setBackgroundSettingsOpen(isOpen) {
      isBackgroundSettingsOpen = Boolean(isOpen);
      backgroundSettingsMenu.hidden = !isBackgroundSettingsOpen;
      backgroundSettingsButton.setAttribute("aria-expanded", isBackgroundSettingsOpen ? "true" : "false");
    }

    function normalizeUiSettings(settings) {
      const source = settings && typeof settings === "object" ? settings : {};
      const normalizeOpacity = (value, fallback) => {
        const numeric = Number(value);
        if (!Number.isFinite(numeric)) {
          return fallback;
        }
        return Math.min(1, Math.max(0.25, Math.round(numeric * 100) / 100));
      };
      return {
        background_image: typeof source.background_image === "string" ? source.background_image : "",
        region_opacity: normalizeOpacity(
          source.region_opacity ?? source.weekly_region_opacity ?? source.editor_region_opacity ?? source.month_region_opacity,
          0.94
        )
      };
    }

    function formatOpacityPercent(value) {
      return `${Math.round(value * 100)}%`;
    }

    function buildBodyBackgroundImage(theme, backgroundImage) {
      const baseLayers = theme === "dark"
        ? [
            "radial-gradient(circle at 10% 8%, rgba(104, 169, 255, 0.16), transparent 24%)",
            "radial-gradient(circle at 88% 10%, rgba(104, 169, 255, 0.12), transparent 18%)",
            "linear-gradient(180deg, #162033 0%, #0f1726 42%, #0b1220 100%)"
          ]
        : [
            "radial-gradient(circle at 10% 8%, rgba(46, 119, 208, 0.14), transparent 24%)",
            "radial-gradient(circle at 88% 10%, rgba(86, 168, 255, 0.18), transparent 18%)",
            "linear-gradient(180deg, #f8fbff 0%, #eef5ff 42%, #e2edfb 100%)"
          ];
      if (!backgroundImage) {
        return baseLayers.join(", ");
      }
      const safeBackgroundImage = backgroundImage
        .replaceAll("\\\\", "\\\\\\\\")
        .replaceAll('"', '\\"');
      return [`url("${safeBackgroundImage}")`, ...baseLayers].join(", ");
    }

    function buildViewportFallback(theme) {
      if (theme === "dark") {
        return [
          "radial-gradient(circle at 16% 12%, rgba(104, 169, 255, 0.16), transparent 24%)",
          "radial-gradient(circle at 84% 90%, rgba(50, 92, 154, 0.2), transparent 28%)",
          "linear-gradient(180deg, #1a2740 0%, #0f1726 42%, #0b1220 100%)"
        ].join(", ");
      }
      return [
        "radial-gradient(circle at 14% 10%, rgba(107, 176, 255, 0.16), transparent 24%)",
        "radial-gradient(circle at 82% 92%, rgba(58, 122, 203, 0.12), transparent 26%)",
        "linear-gradient(180deg, #f9fcff 0%, #eef5ff 40%, #dce8f8 100%)"
      ].join(", ");
    }

    function buildRegionSurface(theme, opacity) {
      const start = opacity;
      const end = Math.max(0.16, opacity - 0.08);
      if (theme === "dark") {
        return `linear-gradient(180deg, rgba(20, 31, 49, ${start}), rgba(17, 27, 42, ${end}))`;
      }
      return `linear-gradient(180deg, rgba(255, 255, 255, ${start}), rgba(244, 249, 255, ${end}))`;
    }

    function updateBackgroundStretch() {
      backgroundStretchFrame = 0;
      const rawScrollTop = Number(window.scrollY ?? window.pageYOffset ?? document.documentElement.scrollTop ?? 0);
      const scrollTop = Number.isFinite(rawScrollTop) ? rawScrollTop : 0;
      const maxScroll = Math.max(0, document.documentElement.scrollHeight - window.innerHeight);
      const overscrollTop = Math.min(180, Math.max(0, -scrollTop));
      const overscrollBottom = Math.min(180, Math.max(0, scrollTop - maxScroll));
      const activeOverscroll = Math.max(overscrollTop, overscrollBottom);

      if (!activeOverscroll) {
        pageBackground.style.transformOrigin = "center top";
        pageBackground.style.transform = "translate3d(0, 0, 0) scale3d(1, 1, 1)";
        pageBackground.style.filter = "";
        return;
      }

      const stretchScale = 1 + activeOverscroll / 520;
      const shiftY = overscrollTop > 0 ? -overscrollTop * 0.18 : overscrollBottom * 0.18;
      pageBackground.style.transformOrigin = overscrollBottom > 0 ? "center bottom" : "center top";
      pageBackground.style.transform = `translate3d(0, ${shiftY.toFixed(2)}px, 0) scale3d(1.02, ${stretchScale.toFixed(4)}, 1)`;
      pageBackground.style.filter = `saturate(${(1 + activeOverscroll / 1000).toFixed(3)})`;
    }

    function scheduleBackgroundStretch() {
      if (backgroundStretchFrame) {
        return;
      }
      backgroundStretchFrame = window.requestAnimationFrame(updateBackgroundStretch);
    }

    function applyVisualSettings(settings) {
      currentUiSettings = normalizeUiSettings(settings);
      const theme = document.body.dataset.theme === "dark" ? "dark" : "light";
      document.documentElement.style.backgroundImage = buildViewportFallback(theme);
      document.documentElement.style.backgroundColor = theme === "dark" ? "#0b1220" : "#e2edfb";
      pageBackground.style.backgroundColor = theme === "dark" ? "#0b1220" : "#e2edfb";
      pageBackground.style.backgroundImage = buildBodyBackgroundImage(theme, currentUiSettings.background_image);
      if (currentUiSettings.background_image) {
        pageBackground.style.backgroundSize = "cover, cover, auto, auto";
        pageBackground.style.backgroundPosition = "center, center, center, center";
        pageBackground.style.backgroundRepeat = "no-repeat, no-repeat, no-repeat, no-repeat";
      } else {
        pageBackground.style.backgroundSize = "cover, auto, auto";
        pageBackground.style.backgroundPosition = "center, center, center";
        pageBackground.style.backgroundRepeat = "no-repeat, no-repeat, no-repeat";
      }
      scheduleBackgroundStretch();

      weeklyPlanPanel.style.background = buildRegionSurface(theme, Math.max(0.18, currentUiSettings.region_opacity - 0.04));
      weeklyPlanBox.style.background = buildRegionSurface(theme, currentUiSettings.region_opacity);
      weeklyBoardScroll.style.background = "";
      editorPanel.style.background = buildRegionSurface(theme, currentUiSettings.region_opacity);
      monthPanel.style.background = buildRegionSurface(theme, currentUiSettings.region_opacity);
      weeklyPlanBox.querySelectorAll(".weekly-head, .weekly-cell, .weekly-label, .weekly-pending").forEach((element) => {
        element.style.background = "";
      });
      weeklyPlanBox.querySelectorAll(".weekly-cell textarea, .weekly-pending textarea").forEach((element) => {
        element.style.background = "";
      });

      regionOpacityInput.value = String(Math.round(currentUiSettings.region_opacity * 100));
      regionOpacityValue.textContent = formatOpacityPercent(currentUiSettings.region_opacity);
      backgroundImageName.textContent = currentUiSettings.background_image ? "已设置本地背景图" : "未设置背景图";
      clearBackgroundImageButton.disabled = !currentUiSettings.background_image;
    }

    async function saveVisualSettings(showMessage = false) {
      try {
        const response = await fetch("/api/ui-settings", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(currentUiSettings)
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "保存视觉设置失败");
        }
        currentUiSettings = normalizeUiSettings(data.settings || currentUiSettings);
        applyVisualSettings(currentUiSettings);
        if (showMessage) {
          setStatus("视觉设置已保存。", "success");
        }
      } catch (error) {
        setStatus(error.message || "视觉设置保存失败。", "error");
      }
    }

    function scheduleVisualSettingsSave(showMessage = false) {
      if (visualSettingsAutosaveTimer) {
        clearTimeout(visualSettingsAutosaveTimer);
      }
      visualSettingsAutosaveTimer = window.setTimeout(() => {
        visualSettingsAutosaveTimer = null;
        saveVisualSettings(showMessage);
      }, VISUAL_SETTINGS_AUTOSAVE_DELAY_MS);
    }

    function updateOpacitySetting(value) {
      currentUiSettings = normalizeUiSettings({ ...currentUiSettings, region_opacity: Number(value) / 100 });
      applyVisualSettings(currentUiSettings);
      scheduleVisualSettingsSave();
    }

    function handleBackgroundImageSelection(file) {
      if (!file) {
        return;
      }
      if (!file.type.startsWith("image/")) {
        setStatus("请选择图片文件作为页面背景。", "warning");
        return;
      }
      if (file.size > MAX_BACKGROUND_IMAGE_SIZE_BYTES) {
        setStatus("背景图请控制在 5MB 以内。", "warning");
        return;
      }
      const reader = new FileReader();
      reader.onload = () => {
        currentUiSettings = normalizeUiSettings({ ...currentUiSettings, background_image: String(reader.result || "") });
        applyVisualSettings(currentUiSettings);
        scheduleVisualSettingsSave(true);
      };
      reader.onerror = () => {
        setStatus("读取背景图失败，请重试。", "error");
      };
      reader.readAsDataURL(file);
    }

    function setStatus(message, type = "") {
      statusEl.textContent = message;
      statusEl.className = "status" + (type ? " " + type : "");
    }

    function getWeekStartString(value) {
      if (!value) {
        return "";
      }
      return formatDate(getMonday(parseDateString(value)));
    }

    function updateWeeklyPlanRange(anchorDate) {
      if (!anchorDate) {
        weeklyPlanRange.textContent = "每周工作安排：按周维护上午、下午安排，编辑后自动保存，并记录其他待定事项。";
        return;
      }
      const monday = getMonday(parseDateString(anchorDate));
      const sunday = new Date(monday);
      sunday.setDate(monday.getDate() + 6);
      weeklyPlanRange.textContent = `每周工作安排：${formatDate(monday)} 至 ${formatDate(sunday)} · 按周维护上午、下午安排，编辑后自动保存，并记录其他待定事项。`;
    }

    function setWeeklyPlanSavedAtText(text) {
      weeklyPlanSavedAt.textContent = text;
    }

    function updateWeeklyPlanSavedAt(value) {
      setWeeklyPlanSavedAtText(value ? `最近保存：${value}` : "最近保存：未保存");
    }

    function parseDateString(value) {
      const [year, month, day] = value.split("-").map(Number);
      return new Date(year, month - 1, day);
    }

    function formatDate(dateValue) {
      const year = dateValue.getFullYear();
      const month = String(dateValue.getMonth() + 1).padStart(2, "0");
      const day = String(dateValue.getDate()).padStart(2, "0");
      return `${year}-${month}-${day}`;
    }

    function getMonday(dateValue) {
      const result = new Date(dateValue);
      const offset = (result.getDay() + 6) % 7;
      result.setDate(result.getDate() - offset);
      return result;
    }

    function getCurrentSettings() {
      const payload = {};
      Object.entries(weeklyScheduleInputs).forEach(([key, input]) => {
        payload[key] = input.value.trim();
      });
      return payload;
    }

    function applyPageSettings(settings) {
      Object.entries(weeklyScheduleInputs).forEach(([key, input]) => {
        input.value = settings[key] || "";
      });
    }

    function getWeeklyPlanSnapshot(weekStart, settings) {
      return JSON.stringify({
        week_start: weekStart || "",
        settings: settings || {}
      });
    }

    function rememberWeeklyPlanState(weekStart, settings, updatedAt) {
      if (!weekStart) {
        return;
      }
      weeklyPlanSavedSnapshots.set(weekStart, getWeeklyPlanSnapshot(weekStart, settings));
      if (currentWeeklyPlanWeekStart === weekStart) {
        updateWeeklyPlanSavedAt(updatedAt || "");
      }
    }

    function cancelWeeklyPlanAutosave() {
      if (weeklyPlanAutosaveTimer) {
        window.clearTimeout(weeklyPlanAutosaveTimer);
        weeklyPlanAutosaveTimer = null;
      }
    }

    async function savePageSettings(options = {}) {
      const weekStart = options.weekStart || currentWeeklyPlanWeekStart || getWeekStartString(dateInput.value);
      const settings = options.settings || getCurrentSettings();
      const silent = Boolean(options.silent);
      const force = Boolean(options.force);
      const payload = {
        week_start: weekStart,
        settings
      };
      if (!weekStart) {
        if (!silent) {
          setStatus("未找到当前周信息。", "warning");
        }
        return false;
      }
      const snapshot = getWeeklyPlanSnapshot(weekStart, settings);
      if (!force && snapshot === (weeklyPlanSavedSnapshots.get(weekStart) || "")) {
        if (!silent) {
          setStatus("每周工作安排已是最新。", "success");
        }
        return true;
      }
      const requestId = ++weeklyPlanSaveSequence;
      weeklyPlanLatestRequestIds.set(weekStart, requestId);
      if (silent && currentWeeklyPlanWeekStart === weekStart) {
        setWeeklyPlanSavedAtText("自动保存中...");
      }
      try {
        const response = await fetch("/api/weekly-plan", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "保存每周工作安排失败");
        }
        const savedWeekStart = data.week_start || weekStart;
        const savedSettings = data.settings || {};
        if (weeklyPlanLatestRequestIds.get(savedWeekStart) !== requestId) {
          return true;
        }
        rememberWeeklyPlanState(savedWeekStart, savedSettings, data.updated_at || "");
        if (currentWeeklyPlanWeekStart === savedWeekStart) {
          applyPageSettings(savedSettings);
          if (!silent) {
            setStatus("每周工作安排已保存。", "success");
          }
        }
        return true;
      } catch (error) {
        if (currentWeeklyPlanWeekStart === weekStart) {
          setWeeklyPlanSavedAtText("自动保存失败，请稍后重试");
        }
        setStatus(error.message || "保存每周工作安排失败。", "error");
        return false;
      }
    }

    function scheduleWeeklyPlanAutosave() {
      const weekStart = currentWeeklyPlanWeekStart || getWeekStartString(dateInput.value);
      if (!weekStart) {
        return;
      }
      const settings = getCurrentSettings();
      if (getWeeklyPlanSnapshot(weekStart, settings) === (weeklyPlanSavedSnapshots.get(weekStart) || "")) {
        cancelWeeklyPlanAutosave();
        return;
      }
      cancelWeeklyPlanAutosave();
      setWeeklyPlanSavedAtText("自动保存中...");
      weeklyPlanAutosaveTimer = window.setTimeout(() => {
        weeklyPlanAutosaveTimer = null;
        savePageSettings({
          weekStart,
          settings,
          silent: true
        });
      }, WEEKLY_PLAN_AUTOSAVE_DELAY_MS);
    }

    async function clearWeeklyPlan() {
      const weekStart = currentWeeklyPlanWeekStart || getWeekStartString(dateInput.value);
      if (!weekStart) {
        setStatus("未找到当前周信息。", "warning");
        return;
      }
      if (!window.confirm(`确认清除 ${weekStart} 这一周的全部工作安排吗？`)) {
        return;
      }
      cancelWeeklyPlanAutosave();
      try {
        const response = await fetch("/api/weekly-plan", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            week_start: weekStart,
            settings: {}
          })
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "清除本周安排失败");
        }
        currentWeeklyPlanWeekStart = data.week_start || weekStart;
        applyPageSettings(data.settings || {});
        rememberWeeklyPlanState(currentWeeklyPlanWeekStart, data.settings || {}, data.updated_at || "");
        setStatus("本周工作安排已清除。", "success");
      } catch (error) {
        setStatus(error.message || "清除本周安排失败。", "error");
      }
    }

    async function loadWeeklyPlan(anchorDate, showMessage = false) {
      if (!anchorDate) {
        return;
      }
      const weekStart = getWeekStartString(anchorDate);
      currentWeeklyPlanWeekStart = weekStart;
      updateWeeklyPlanRange(anchorDate);
      try {
        const response = await fetch(`/api/weekly-plan?date=${encodeURIComponent(anchorDate)}`);
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "读取每周工作安排失败");
        }
        currentWeeklyPlanWeekStart = data.week_start || weekStart;
        applyPageSettings(data.settings || {});
        rememberWeeklyPlanState(currentWeeklyPlanWeekStart, data.settings || {}, data.updated_at || "");
        if (showMessage) {
          setStatus(`已读取 ${currentWeeklyPlanWeekStart} 所在周的工作安排。`, "success");
        }
      } catch (error) {
        applyPageSettings({});
        weeklyPlanSavedSnapshots.delete(weekStart);
        updateWeeklyPlanSavedAt("");
        if (showMessage) {
          setStatus(error.message || "读取每周工作安排失败。", "error");
        }
      }
    }

    function makeBlankItem() {
      return {
        customer_name: "",
        project_type: "",
        sales: "",
        item_type: "",
        service_mode: "",
        work_hours: "",
        work_content: "",
        pending_issues: "",
        risk: ""
      };
    }

    function syncMonthFromDate() {
      if (dateInput.value) {
        monthInput.value = dateInput.value.slice(0, 7);
      }
    }

    function renderWeekButtons(anchorDateString = dateInput.value) {
      if (!anchorDateString) {
        return;
      }

      const weekdays = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"];
      const monday = getMonday(parseDateString(anchorDateString));
      const sunday = new Date(monday);
      sunday.setDate(monday.getDate() + 6);

      weekRange.textContent = `${formatDate(monday)} 至 ${formatDate(sunday)}`;
      weekStrip.innerHTML = "";

      weekdays.forEach((label, index) => {
        const day = new Date(monday);
        day.setDate(monday.getDate() + index);
        const value = formatDate(day);
        const button = document.createElement("button");
        button.type = "button";
        const isWeekend = index >= 5;
        button.className = "week-btn" + (isWeekend ? " weekend" : "") + (value === dateInput.value ? " active" : "");
        button.innerHTML = `
          <span class="week-btn-name">${label}</span>
          <span class="week-btn-date">${value.slice(5)}</span>
        `;
        button.addEventListener("click", () => {
          dateInput.value = value;
          syncMonthFromDate();
          renderWeekButtons(value);
          loadDateEntry(value);
          refreshMonthEntries();
        });
        weekStrip.appendChild(button);
      });
    }

    function shiftWeek(offsetDays) {
      const current = dateInput.value ? parseDateString(dateInput.value) : new Date();
      current.setDate(current.getDate() + offsetDays);
      const nextDate = formatDate(current);
      dateInput.value = nextDate;
      syncMonthFromDate();
      renderWeekButtons(nextDate);
      loadWeeklyPlan(nextDate, true);
      loadDateEntry(nextDate);
      refreshMonthEntries();
    }

    function rowTemplate(item = makeBlankItem(), index = 0) {
      const row = document.createElement("div");
      row.className = "item-row";
      const projectType = item.project_type || "";
      const hasCustomProjectType = projectType && !projectTypeOptions.includes(projectType);
      const projectTypeHtml = projectTypeOptions.map((option) => {
        const selected = option === projectType ? "selected" : "";
        return `<option value="${escapeHtml(option)}" ${selected}>${escapeHtml(option)}</option>`;
      }).join("");
      const sales = item.sales || "";
      const hasCustomSales = sales && !salesOptions.includes(sales);
      const salesHtml = salesOptions.map((option) => {
        const selected = option === sales ? "selected" : "";
        return `<option value="${escapeHtml(option)}" ${selected}>${escapeHtml(option)}</option>`;
      }).join("");
      const itemType = item.item_type || "";
      const hasCustomType = itemType && !itemTypeOptions.includes(itemType);
      const optionsHtml = itemTypeOptions.map((option) => {
        const selected = option === itemType ? "selected" : "";
        return `<option value="${escapeHtml(option)}" ${selected}>${escapeHtml(option)}</option>`;
      }).join("");
      const serviceMode = item.service_mode || "";
      const hasCustomServiceMode = serviceMode && !serviceModeOptions.includes(serviceMode);
      const serviceModeHtml = serviceModeOptions.map((option) => {
        const selected = option === serviceMode ? "selected" : "";
        return `<option value="${escapeHtml(option)}" ${selected}>${escapeHtml(option)}</option>`;
      }).join("");
      row.innerHTML = `
        <div class="base-info-cell">
          <div class="base-info-stack">
            <label class="base-info-line">
              <span>客户名称：</span>
              <input type="text" data-field="customer_name" value="${escapeHtml(item.customer_name || "")}" placeholder="请输入客户名称">
            </label>
            <label class="base-info-line">
              <span>项目类型：</span>
              <select data-field="project_type">
                <option value="">请选择项目类型</option>
                ${projectTypeHtml}
                ${hasCustomProjectType ? `<option value="${escapeHtml(projectType)}" selected>${escapeHtml(projectType)}</option>` : ""}
              </select>
            </label>
            <label class="base-info-line">
              <span>销售：</span>
              <select data-field="sales">
                <option value="">请选择销售</option>
                ${salesHtml}
                ${hasCustomSales ? `<option value="${escapeHtml(sales)}" selected>${escapeHtml(sales)}</option>` : ""}
              </select>
            </label>
          </div>
        </div>
        <div class="service-content-cell">
          <div class="service-content-stack">
            <label class="service-content-line">
              <span>类型：</span>
              <select data-field="item_type">
                <option value="">请选择类型</option>
                ${optionsHtml}
                ${hasCustomType ? `<option value="${escapeHtml(itemType)}" selected>${escapeHtml(itemType)}</option>` : ""}
              </select>
            </label>
            <label class="service-content-line">
              <span>服务方式：</span>
              <select data-field="service_mode">
                <option value="">请选择服务方式</option>
                ${serviceModeHtml}
                ${hasCustomServiceMode ? `<option value="${escapeHtml(serviceMode)}" selected>${escapeHtml(serviceMode)}</option>` : ""}
              </select>
            </label>
            <label class="service-content-line">
              <span>工时：</span>
              <input type="number" data-field="work_hours" min="0" step="0.5" value="${escapeHtml(String(item.work_hours ?? ""))}" placeholder="请输入工时">
            </label>
          </div>
        </div>
        <div><textarea data-field="work_content" placeholder="工作内容">${escapeHtml(item.work_content || "")}</textarea></div>
        <div class="issue-risk-cell">
          <div class="issue-risk-stack">
            <label class="issue-risk-line">
              <span>遗留事项</span>
              <textarea data-field="pending_issues" placeholder="请输入遗留事项">${escapeHtml(item.pending_issues || "")}</textarea>
            </label>
            <label class="issue-risk-line">
              <span>存在风险</span>
              <textarea data-field="risk" placeholder="请输入存在风险">${escapeHtml(item.risk || "")}</textarea>
            </label>
          </div>
        </div>
        <div class="row-action"><button type="button" class="danger mini-btn remove-row">删除</button></div>
      `;
      return row;
    }

    function escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;");
    }

    function renderItems(items) {
      listEditor.innerHTML = "";
      const header = document.createElement("div");
      header.className = "table-editor";
      header.innerHTML = `
        <div class="table-header">
          <div>基础信息</div>
          <div>服务内容</div>
          <div>工作内容</div>
          <div>遗留&amp;风险</div>
          <div>操作</div>
        </div>
      `;

      const body = document.createElement("div");
      body.className = "table-body";
      const source = items && items.length ? items : [makeBlankItem()];
      source.forEach((item, index) => {
        body.appendChild(rowTemplate(item, index));
      });
      header.appendChild(body);
      listEditor.appendChild(header);
      attachRemoveHandlers();
    }

    function attachRemoveHandlers() {
      listEditor.querySelectorAll(".remove-row").forEach((button) => {
        button.onclick = () => {
          const rows = [...listEditor.querySelectorAll(".item-row")];
          if (rows.length === 1) {
            renderItems([makeBlankItem()]);
            setStatus("至少保留一行，已重置为空白事项。", "warning");
            return;
          }
          button.closest(".item-row").remove();
        };
      });
    }

    function collectItems() {
      return [...listEditor.querySelectorAll(".item-row")].map((card) => {
        const item = {};
        card.querySelectorAll("[data-field]").forEach((input) => {
          item[input.dataset.field] = input.value.trim();
        });
        return item;
      });
    }

    function validateItems(items) {
      for (const item of items) {
        const value = item.work_hours;
        if (!value) {
          continue;
        }
        const hours = Number(value);
        const halfStep = Math.round(hours * 2);
        if (!Number.isFinite(hours) || hours < 0 || Math.abs(hours * 2 - halfStep) > 1e-9) {
          throw new Error("工时仅支持输入大于等于 0 的整数或 0.5。");
        }
      }
    }

    function summarizeEntry(entry) {
      if (!entry.items.length) {
        return "暂无事项";
      }
      const names = entry.items.slice(0, 2).map((item) => item.customer_name || "未填客户").join("、");
      const more = entry.items.length > 2 ? ` 等 ${entry.items.length} 项` : "";
      return `${names}${more}`;
    }

    function createEntryCard(entry, tipText) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = "entry-card";

      const head = document.createElement("div");
      head.className = "entry-head";

      const dateEl = document.createElement("div");
      dateEl.className = "entry-date";
      dateEl.textContent = entry.work_date;

      const badges = document.createElement("div");
      badges.className = "entry-badges";
      badges.innerHTML = `
        <span class="badge">${entry.item_count} 条事项</span>
        <span class="badge">${entry.total_hours} 小时</span>
      `;

      head.appendChild(dateEl);
      head.appendChild(badges);

      const snippet = document.createElement("div");
      snippet.className = "entry-snippet";
      snippet.textContent = summarizeEntry(entry);

      const meta = document.createElement("div");
      meta.className = "entry-meta";
      const updatedEl = document.createElement("span");
      updatedEl.textContent = `更新于 ${entry.updated_at}`;
      const tipEl = document.createElement("span");
      tipEl.textContent = tipText;
      meta.appendChild(updatedEl);
      meta.appendChild(tipEl);

      button.appendChild(head);
      button.appendChild(snippet);
      button.appendChild(meta);

      button.addEventListener("click", () => {
        fillEditor(entry);
        setStatus("已载入所选日期的列表记录。", "success");
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
      return button;
    }

    function fillEditor(entry) {
      dateInput.value = entry.work_date;
      syncMonthFromDate();
      renderWeekButtons(entry.work_date);
      loadWeeklyPlan(entry.work_date);
      renderItems(entry.items || [makeBlankItem()]);
    }

    function clearEditor(keepDate = true) {
      const currentDate = dateInput.value;
      renderItems([makeBlankItem()]);
      if (keepDate) {
        dateInput.value = currentDate;
      }
    }

    async function loadDateEntry(targetDate, showMessage = true) {
      if (!targetDate) {
        return;
      }
      try {
        const response = await fetch(`/api/entry?date=${encodeURIComponent(targetDate)}`);
        const payload = await response.json();
        if (payload.entry) {
          fillEditor(payload.entry);
          if (showMessage) {
            setStatus("已读取当天已保存的列表。", "success");
          }
        } else {
          clearEditor(true);
          dateInput.value = targetDate;
          if (showMessage) {
            setStatus("这一天还没有保存记录。", "warning");
          }
        }
      } catch (error) {
        setStatus("读取当天记录失败。", "error");
      }
    }

    async function refreshRecentEntries() {
      try {
        const response = await fetch("/api/entries");
        const payload = await response.json();
        recentList.innerHTML = "";
        if (!payload.entries.length) {
          recentList.innerHTML = '<div class="empty">还没有任何记录，先保存一份当天列表吧。</div>';
          return;
        }
        payload.entries.forEach((entry) => {
          recentList.appendChild(createEntryCard(entry, "点击回填"));
        });
      } catch (error) {
        recentList.innerHTML = '<div class="empty">最近记录加载失败。</div>';
      }
    }

    async function refreshMonthEntries(showMessage = false) {
      const month = monthInput.value;
      if (!month) {
        monthList.innerHTML = '<div class="empty">请先选择月份。</div>';
        return;
      }

      try {
        const response = await fetch(`/api/month?month=${encodeURIComponent(month)}`);
        const payload = await response.json();
        document.getElementById("stat-days").textContent = payload.stats.total_days;
        document.getElementById("stat-items").textContent = payload.stats.total_items;
        document.getElementById("stat-hours").textContent = payload.stats.total_hours;

        monthList.innerHTML = "";
        if (!payload.entries.length) {
          monthList.innerHTML = '<div class="empty">这个月份还没有保存任何记录。</div>';
        } else {
          payload.entries.forEach((entry) => {
            monthList.appendChild(createEntryCard(entry, "点击查看"));
          });
        }

        if (showMessage) {
          setStatus(`已刷新 ${month} 的月度数据。`, "success");
        }
      } catch (error) {
        monthList.innerHTML = '<div class="empty">月份数据加载失败。</div>';
        setStatus("月份数据读取失败。", "error");
      }
    }

    async function saveEntry() {
      const items = collectItems();
      try {
        validateItems(items);
      } catch (error) {
        setStatus(error.message || "工时格式不正确。", "error");
        return;
      }
      const payload = {
        work_date: dateInput.value,
        items
      };
      setStatus("正在保存...");
      try {
        const response = await fetch("/api/entry", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "保存失败");
        }
        fillEditor(data.entry);
        setStatus("已保存到本地数据库。", "success");
        refreshRecentEntries();
        refreshMonthEntries();
      } catch (error) {
        setStatus(error.message || "保存失败。", "error");
      }
    }

    async function deleteEntry() {
      const targetDate = dateInput.value;
      if (!targetDate) {
        setStatus("请先选择日期。", "warning");
        return;
      }
      if (!window.confirm(`确认删除 ${targetDate} 的整天记录吗？`)) {
        return;
      }
      try {
        const response = await fetch(`/api/entry?date=${encodeURIComponent(targetDate)}`, { method: "DELETE" });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || "删除失败");
        }
        clearEditor(true);
        dateInput.value = targetDate;
        setStatus("当天记录已删除。", "success");
        refreshRecentEntries();
        refreshMonthEntries();
      } catch (error) {
        setStatus(error.message || "删除失败。", "error");
      }
    }

    addRowButton.addEventListener("click", () => {
      const table = listEditor.querySelector(".table-editor");
      if (!table) {
        renderItems([makeBlankItem()]);
        return;
      }
      const body = table.querySelector(".table-body") || table;
      body.appendChild(rowTemplate(makeBlankItem(), listEditor.querySelectorAll(".item-row").length));
      attachRemoveHandlers();
    });
    reloadButton.addEventListener("click", () => loadDateEntry(dateInput.value));
    clearButton.addEventListener("click", () => {
      clearEditor(true);
      setStatus("表单已清空。", "warning");
    });
    deleteButton.addEventListener("click", deleteEntry);
    saveButton.addEventListener("click", saveEntry);
    exportDailyLogButton.addEventListener("click", () => {
      const targetDate = dateInput.value;
      if (!targetDate) {
        setStatus("请先选择要导出的日期。", "warning");
        return;
      }
      window.location.href = `/api/export-log?date=${encodeURIComponent(targetDate)}`;
      setStatus(`正在生成 ${targetDate} 的工作日志，请稍候。`, "success");
    });
    clearWeeklyPlanButton.addEventListener("click", clearWeeklyPlan);
    Object.values(weeklyScheduleInputs).forEach((input) => {
      input.addEventListener("input", scheduleWeeklyPlanAutosave);
    });
    refreshMonthButton.addEventListener("click", () => refreshMonthEntries(true));
    exportMonthButton.addEventListener("click", () => {
      const month = monthInput.value;
      if (!month) {
        setStatus("请先选择要导出的月份。", "warning");
        return;
      }
      window.location.href = `/api/export?month=${encodeURIComponent(month)}`;
      setStatus(`正在导出 ${month} 的 Excel 文件。`, "success");
    });
    dateInput.addEventListener("change", () => {
      syncMonthFromDate();
      renderWeekButtons(dateInput.value);
      loadWeeklyPlan(dateInput.value);
      loadDateEntry(dateInput.value);
      refreshMonthEntries();
    });
    monthInput.addEventListener("change", () => refreshMonthEntries(true));
    prevWeekButton.addEventListener("click", () => shiftWeek(-7));
    nextWeekButton.addEventListener("click", () => shiftWeek(7));
    themeToggleButton.addEventListener("click", () => {
      const nextTheme = document.body.dataset.theme === "dark" ? "light" : "dark";
      applyTheme(nextTheme);
    });
    backgroundSettingsButton.addEventListener("click", (event) => {
      event.stopPropagation();
      setBackgroundSettingsOpen(!isBackgroundSettingsOpen);
    });
    backgroundSettingsMenu.addEventListener("click", (event) => {
      event.stopPropagation();
    });
    selectBackgroundImageButton.addEventListener("click", () => backgroundImageInput.click());
    backgroundImageInput.addEventListener("change", (event) => {
      const [file] = event.target.files || [];
      handleBackgroundImageSelection(file);
      backgroundImageInput.value = "";
    });
    clearBackgroundImageButton.addEventListener("click", () => {
      if (!currentUiSettings.background_image) {
        return;
      }
      currentUiSettings = normalizeUiSettings({ ...currentUiSettings, background_image: "" });
      applyVisualSettings(currentUiSettings);
      scheduleVisualSettingsSave(true);
    });
    regionOpacityInput.addEventListener("input", (event) => updateOpacitySetting(event.target.value));
    document.addEventListener("click", () => {
      if (isBackgroundSettingsOpen) {
        setBackgroundSettingsOpen(false);
      }
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && isBackgroundSettingsOpen) {
        setBackgroundSettingsOpen(false);
      }
    });
    window.addEventListener("scroll", scheduleBackgroundStretch, { passive: true });
    window.addEventListener("resize", scheduleBackgroundStretch, { passive: true });
    window.addEventListener("touchmove", scheduleBackgroundStretch, { passive: true });
    window.addEventListener("touchend", scheduleBackgroundStretch, { passive: true });

    initTheme();
    applyPageSettings(initialPageSettings);
    applyVisualSettings(initialUiSettings);
    scheduleBackgroundStretch();
    renderItems([makeBlankItem()]);
    renderWeekButtons(dateInput.value);
    loadWeeklyPlan(dateInput.value);
    refreshRecentEntries();
    refreshMonthEntries();
    loadDateEntry(dateInput.value, false);
  </script>
</body>
</html>
"""


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS daily_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                work_date TEXT NOT NULL UNIQUE,
                plan_content TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                items_json TEXT NOT NULL DEFAULT '[]'
            )
            """
        )
        columns = {
            row[1] for row in connection.execute("PRAGMA table_info(daily_entries)").fetchall()
        }
        if "items_json" not in columns:
            connection.execute(
                "ALTER TABLE daily_entries ADD COLUMN items_json TEXT NOT NULL DEFAULT '[]'"
            )
            columns.add("items_json")
        if "progress_content" in columns:
            connection.executescript(
                """
                CREATE TABLE daily_entries_v2 (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    work_date TEXT NOT NULL UNIQUE,
                    plan_content TEXT NOT NULL DEFAULT '',
                    notes TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    items_json TEXT NOT NULL DEFAULT '[]'
                );
                INSERT INTO daily_entries_v2 (
                    id, work_date, plan_content, notes, created_at, updated_at, items_json
                )
                SELECT id, work_date, plan_content, notes, created_at, updated_at, items_json
                FROM daily_entries;
                DROP TABLE daily_entries;
                ALTER TABLE daily_entries_v2 RENAME TO daily_entries;
                """
            )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS app_settings (
                setting_key TEXT PRIMARY KEY,
                setting_value TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        existing_keys = {
            row["setting_key"]
            for row in connection.execute("SELECT setting_key FROM app_settings").fetchall()
        }
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for key, value in DEFAULT_PAGE_SETTINGS.items():
            if key not in existing_keys:
                connection.execute(
                    """
                    INSERT INTO app_settings (setting_key, setting_value, updated_at)
                    VALUES (?, ?, ?)
                    """,
                    (key, value, timestamp),
                )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS weekly_plans (
                week_start TEXT PRIMARY KEY,
                settings_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        existing_weekly_rows = connection.execute(
            "SELECT COUNT(*) AS row_count FROM weekly_plans"
        ).fetchone()["row_count"]
        if existing_weekly_rows == 0:
            legacy_rows = connection.execute(
                "SELECT setting_key, setting_value FROM app_settings WHERE setting_key LIKE 'weekly_%'"
            ).fetchall()
            legacy_settings = DEFAULT_PAGE_SETTINGS.copy()
            has_legacy_content = False
            for row in legacy_rows:
                key = row["setting_key"]
                if key in legacy_settings:
                    value = str(row["setting_value"] or "").strip()
                    legacy_settings[key] = value
                    has_legacy_content = has_legacy_content or bool(value)
            if has_legacy_content:
                current_week_start = get_week_start(date.today().isoformat())
                connection.execute(
                    """
                    INSERT OR REPLACE INTO weekly_plans (week_start, settings_json, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        current_week_start,
                        json.dumps(legacy_settings, ensure_ascii=False),
                        timestamp,
                        timestamp,
                    ),
                )

def get_week_start(value: str) -> str:
    target = validate_date(value)
    target_date = datetime.strptime(target, "%Y-%m-%d")
    monday = target_date - timedelta(days=target_date.weekday())
    return monday.strftime("%Y-%m-%d")


def normalize_weekly_plan_settings(payload: dict | None) -> dict:
    source = payload if isinstance(payload, dict) else {}
    settings = {}
    for key in WEEKLY_PLAN_KEYS:
        settings[key] = str(source.get(key, DEFAULT_PAGE_SETTINGS[key])).strip()
    return settings


def get_weekly_plan_settings(anchor_date: str) -> tuple[str, dict, str]:
    week_start = get_week_start(anchor_date)
    with get_connection() as connection:
        row = connection.execute(
            "SELECT settings_json, updated_at FROM weekly_plans WHERE week_start = ?",
            (week_start,),
        ).fetchone()
    if not row:
        return week_start, DEFAULT_PAGE_SETTINGS.copy(), ""
    try:
        loaded = json.loads(row["settings_json"] or "{}")
    except json.JSONDecodeError:
        loaded = {}
    return week_start, normalize_weekly_plan_settings(loaded), str(row["updated_at"] or "")


def save_weekly_plan_settings(week_start: str, payload: dict | None) -> tuple[str, dict, str]:
    normalized_week_start = get_week_start(week_start)
    settings = normalize_weekly_plan_settings(payload)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as connection:
        existing = connection.execute(
            "SELECT created_at FROM weekly_plans WHERE week_start = ?",
            (normalized_week_start,),
        ).fetchone()
        created_at = existing["created_at"] if existing else timestamp
        connection.execute(
            """
            INSERT INTO weekly_plans (week_start, settings_json, created_at, updated_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(week_start) DO UPDATE SET
                settings_json = excluded.settings_json,
                updated_at = excluded.updated_at
            """,
            (
                normalized_week_start,
                json.dumps(settings, ensure_ascii=False),
                created_at,
                timestamp,
            ),
        )
    return normalized_week_start, settings, timestamp


def normalize_ui_settings(payload: dict | None) -> dict:
    source = payload if isinstance(payload, dict) else {}
    background_image = str(source.get("background_image", DEFAULT_UI_SETTINGS["background_image"])).strip()
    if background_image and not background_image.startswith("data:image/"):
        raise ValueError("背景图必须是本地图片生成的数据内容。")
    if len(background_image.encode("utf-8")) > 8 * 1024 * 1024:
        raise ValueError("背景图数据过大，请选择 5MB 左右以内的图片。")

    def normalize_opacity(value: object, fallback: float) -> float:
        try:
            value = float(value)
        except (TypeError, ValueError):
            value = float(fallback)
        value = max(0.25, min(1.0, value))
        return round(value, 2)

    legacy_values = [
        source.get("region_opacity"),
        source.get("weekly_region_opacity"),
        source.get("editor_region_opacity"),
        source.get("month_region_opacity"),
    ]
    opacity_source = next((value for value in legacy_values if value not in (None, "")), DEFAULT_UI_SETTINGS["region_opacity"])

    return {
        "background_image": background_image,
        "region_opacity": normalize_opacity(opacity_source, DEFAULT_UI_SETTINGS["region_opacity"]),
    }


def get_ui_settings() -> tuple[dict, str]:
    with get_connection() as connection:
        row = connection.execute(
            "SELECT setting_value, updated_at FROM app_settings WHERE setting_key = ?",
            ("ui_settings_json",),
        ).fetchone()
    if not row:
        return DEFAULT_UI_SETTINGS.copy(), ""
    try:
        loaded = json.loads(row["setting_value"] or "{}")
    except json.JSONDecodeError:
        loaded = {}
    return normalize_ui_settings(loaded), str(row["updated_at"] or "")


def save_ui_settings(payload: dict | None) -> tuple[dict, str]:
    settings = normalize_ui_settings(payload)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO app_settings (setting_key, setting_value, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(setting_key) DO UPDATE SET
                setting_value = excluded.setting_value,
                updated_at = excluded.updated_at
            """,
            ("ui_settings_json", json.dumps(settings, ensure_ascii=False), timestamp),
        )
    return settings, timestamp


def validate_date(value: str) -> str:
    datetime.strptime(value, "%Y-%m-%d")
    return value


def validate_month(value: str) -> str:
    datetime.strptime(value, "%Y-%m")
    return value


def normalize_item(raw_item: dict) -> dict:
    return {
        "customer_name": str(raw_item.get("customer_name", "")).strip(),
        "project_type": str(raw_item.get("project_type", "")).strip(),
        "sales": str(raw_item.get("sales", "")).strip(),
        "item_type": str(raw_item.get("item_type", "")).strip(),
        "service_mode": str(raw_item.get("service_mode", "")).strip(),
        "work_hours": format_hours(raw_item.get("work_hours", "")),
        "work_content": str(raw_item.get("work_content", "")).strip(),
        "pending_issues": str(raw_item.get("pending_issues", raw_item.get("notes", ""))).strip(),
        "risk": str(raw_item.get("risk", "")).strip(),
    }


def format_hours(value: object) -> str:
    if value in (None, ""):
        return ""
    number = float(value)
    if number < 0:
        raise ValueError("工时不能小于 0。")
    doubled = round(number * 2)
    if abs(number * 2 - doubled) > 1e-9:
        raise ValueError("工时仅支持输入整数或 0.5。")
    if number.is_integer():
        return str(int(number))
    return (f"{number:.2f}").rstrip("0").rstrip(".")


def parse_items(items_json: str, fallback_row: sqlite3.Row | None = None) -> list[dict]:
    try:
        items = json.loads(items_json or "[]")
    except json.JSONDecodeError:
        items = []

    if isinstance(items, list) and items:
        return [normalize_item(item if isinstance(item, dict) else {}) for item in items]

    if fallback_row is not None:
        plan_content = str(fallback_row["plan_content"] or "").strip()
        notes = str(fallback_row["notes"] or "").strip()
        if plan_content or notes:
            return [
                {
                    "customer_name": "旧记录",
                    "project_type": "",
                    "sales": "",
                    "item_type": "历史数据",
                    "service_mode": "",
                    "work_hours": "",
                    "work_content": plan_content,
                    "pending_issues": notes,
                    "risk": "",
                }
            ]

    return []


def total_hours(items: list[dict]) -> str:
    total = 0.0
    for item in items:
        value = item.get("work_hours", "")
        if value not in (None, ""):
            total += float(value)
    if total.is_integer():
        return str(int(total))
    return (f"{total:.2f}").rstrip("0").rstrip(".")


def normalize_entry(row: sqlite3.Row | None) -> dict | None:
    if row is None:
        return None
    items = parse_items(row["items_json"], row)
    return {
        "work_date": row["work_date"],
        "items": items,
        "item_count": len(items),
        "total_hours": total_hours(items),
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def fetch_entry(work_date: str) -> dict | None:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT work_date, plan_content, notes, created_at, updated_at, items_json
            FROM daily_entries
            WHERE work_date = ?
            """,
            (work_date,),
        ).fetchone()
    return normalize_entry(row)


def fetch_recent_entries(limit: int = 12) -> list[dict]:
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT work_date, plan_content, notes, created_at, updated_at, items_json
            FROM daily_entries
            ORDER BY work_date DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [normalize_entry(row) for row in rows]


def fetch_month_entries(month: str) -> list[dict]:
    month = validate_month(month)
    month_start = f"{month}-01"
    if month.endswith("-12"):
        next_month = f"{int(month[:4]) + 1}-01"
    else:
        year, month_number = month.split("-")
        next_month = f"{year}-{int(month_number) + 1:02d}"
    next_month_start = f"{next_month}-01"

    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT work_date, plan_content, notes, created_at, updated_at, items_json
            FROM daily_entries
            WHERE work_date >= ? AND work_date < ?
            ORDER BY work_date DESC
            """,
            (month_start, next_month_start),
        ).fetchall()
    return [normalize_entry(row) for row in rows]


def build_month_stats(entries: list[dict]) -> dict:
    item_count = sum(entry["item_count"] for entry in entries)
    total = sum((float(entry["total_hours"] or 0) for entry in entries), 0.0)
    if total.is_integer():
        hours = str(int(total))
    else:
        hours = (f"{total:.2f}").rstrip("0").rstrip(".")
    return {
        "total_days": len(entries),
        "total_items": item_count,
        "total_hours": hours,
    }


def normalize_items_payload(items: object) -> list[dict]:
    if not isinstance(items, list):
        raise ValueError("事项列表格式不正确。")

    normalized: list[dict] = []
    for raw_item in items:
        if not isinstance(raw_item, dict):
            continue
        item = normalize_item(raw_item)
        if not any(item.values()):
            continue
        if not item["customer_name"]:
            raise ValueError("每条事项都需要填写客户名称。")
        if not item["work_content"]:
            raise ValueError("每条事项都需要填写工作内容。")
        normalized.append(item)

    if not normalized:
        raise ValueError("请至少填写一条有效事项。")
    return normalized


def upsert_entry(payload: dict) -> dict:
    work_date = validate_date(str(payload.get("work_date", "")).strip())
    items = normalize_items_payload(payload.get("items", []))
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    items_json = json.dumps(items, ensure_ascii=False)

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO daily_entries (
                work_date, plan_content, notes, created_at, updated_at, items_json
            )
            VALUES (?, '', '', ?, ?, ?)
            ON CONFLICT(work_date) DO UPDATE SET
                items_json = excluded.items_json,
                updated_at = excluded.updated_at
            """,
            (work_date, timestamp, timestamp, items_json),
        )
    return fetch_entry(work_date)


def delete_entry(work_date: str) -> bool:
    work_date = validate_date(work_date)
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM daily_entries WHERE work_date = ?", (work_date,))
    return cursor.rowcount > 0


def xml_cell(reference: str, value: str) -> str:
    safe_value = escape(value or "")
    return (
        f'<c r="{reference}" t="inlineStr">'
        f'<is><t xml:space="preserve">{safe_value}</t></is>'
        f'</c>'
    )


# Build a small XLSX file without extra dependencies.
def build_excel_file(entries: list[dict], month: str) -> bytes:
    headers = [
        "日期",
        "客户名称",
        "项目类型",
        "销售",
        "类型",
        "服务方式",
        "工时",
        "工作内容",
        "遗留事项",
        "存在风险",
        "创建时间",
        "更新时间",
    ]
    rows = [headers]
    for entry in reversed(entries):
        for item in entry["items"]:
            rows.append(
                [
                    entry["work_date"],
                    item["customer_name"],
                    item["project_type"],
                    item["sales"],
                    item["item_type"],
                    item["service_mode"],
                    item["work_hours"],
                    item["work_content"],
                    item["pending_issues"],
                    item["risk"],
                    entry["created_at"],
                    entry["updated_at"],
                ]
            )

    sheet_rows = []
    for row_index, row in enumerate(rows, start=1):
        cells = []
        for col_index, value in enumerate(row, start=1):
            column_name = ""
            current = col_index
            while current:
                current, remainder = divmod(current - 1, 26)
                column_name = chr(65 + remainder) + column_name
            cells.append(xml_cell(f"{column_name}{row_index}", value))
        sheet_rows.append(f'<row r="{row_index}">{"".join(cells)}</row>')

    worksheet_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <sheetViews><sheetView workbookViewId="0"/></sheetViews>
  <sheetFormatPr defaultRowHeight="20"/>
  <cols>
    <col min="1" max="1" width="14" customWidth="1"/>
    <col min="2" max="4" width="18" customWidth="1"/>
    <col min="5" max="5" width="12" customWidth="1"/>
    <col min="6" max="8" width="34" customWidth="1"/>
    <col min="9" max="11" width="22" customWidth="1"/>
  </cols>
  <sheetData>{''.join(sheet_rows)}</sheetData>
</worksheet>
"""

    workbook_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"
          xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">
  <sheets><sheet name="月度工作台账" sheetId="1" r:id="rId1"/></sheets>
</workbook>
"""

    workbook_rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
</Relationships>
"""

    root_rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
"""

    content_types_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>
  <Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>
  <Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>
"""

    styles_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">
  <fonts count="1"><font><sz val="11"/><name val="Calibri"/></font></fonts>
  <fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills>
  <borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>
  <cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>
  <cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>
  <cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles>
</styleSheet>
"""

    now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    core_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
                   xmlns:dc="http://purl.org/dc/elements/1.1/"
                   xmlns:dcterms="http://purl.org/dc/terms/"
                   xmlns:dcmitype="http://purl.org/dc/dcmitype/"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>{escape(month)} 工作台账导出</dc:title>
  <dc:creator>Codex Daily Planner</dc:creator>
  <cp:lastModifiedBy>Codex Daily Planner</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{now_iso}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{now_iso}</dcterms:modified>
</cp:coreProperties>
"""

    app_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
            xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Microsoft Excel</Application>
</Properties>
"""

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types_xml)
        archive.writestr("_rels/.rels", root_rels_xml)
        archive.writestr("docProps/core.xml", core_xml)
        archive.writestr("docProps/app.xml", app_xml)
        archive.writestr("xl/workbook.xml", workbook_xml)
        archive.writestr("xl/_rels/workbook.xml.rels", workbook_rels_xml)
        archive.writestr("xl/styles.xml", styles_xml)
        archive.writestr("xl/worksheets/sheet1.xml", worksheet_xml)
    return buffer.getvalue()


def build_daily_log_context(work_date: str) -> dict:
    target_date = validate_date(work_date)
    today_entry = fetch_entry(target_date)
    if not today_entry:
        raise ValueError("该日期没有可导出的记录。")

    tomorrow_date = (datetime.strptime(target_date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    tomorrow_entry = fetch_entry(tomorrow_date)
    tomorrow_week_start, tomorrow_weekly_settings, tomorrow_weekly_updated_at = get_weekly_plan_settings(tomorrow_date)
    return {
        "work_date": target_date,
        "today": enrich_entry_for_log(today_entry),
        "tomorrow_date": tomorrow_date,
        "tomorrow": enrich_entry_for_log(tomorrow_entry),
        "tomorrow_weekly_plan": build_weekly_day_plan_for_log(
            tomorrow_date,
            tomorrow_week_start,
            tomorrow_weekly_settings,
            tomorrow_weekly_updated_at,
        ),
    }


def classify_service_type_for_log(item_type: str) -> str:
    normalized = str(item_type or "").strip()
    if not normalized:
        return ""

    lowered = normalized.lower()
    if "交付" in normalized:
        return "交付客户"
    if "服务" in normalized:
        return "服务客户"
    if "poc" in lowered:
        return "POC客户"
    if "方案" in normalized:
        return "方案类客户"
    if "基建" in normalized:
        return "基建类工作"
    return f"{normalized}类事项"


def enrich_entry_for_log(entry: dict | None) -> dict | None:
    if not entry:
        return None

    items: list[dict] = []
    for item in entry.get("items", []):
        enriched_item = dict(item)
        enriched_item["service_type_label"] = classify_service_type_for_log(enriched_item.get("item_type", ""))
        items.append(enriched_item)

    enriched_entry = dict(entry)
    enriched_entry["items"] = items
    return enriched_entry


def build_weekly_day_plan_for_log(
    target_date: str,
    week_start: str,
    settings: dict | None,
    updated_at: str,
) -> dict:
    normalized_settings = normalize_weekly_plan_settings(settings)
    target = datetime.strptime(validate_date(target_date), "%Y-%m-%d")
    day_keys = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    day_key = day_keys[target.weekday()]
    return {
        "week_start": week_start,
        "target_date": target_date,
        "day_name": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][target.weekday()],
        "am": normalized_settings.get(f"weekly_{day_key}_am", ""),
        "pm": normalized_settings.get(f"weekly_{day_key}_pm", ""),
        "other_pending": normalized_settings.get("weekly_other_pending", ""),
        "updated_at": updated_at,
    }


def build_codex_log_prompt(context: dict) -> str:
    return f"""你是一个资深的售前、售后工程师，这是你今天所做的工作，你要根据今天的工作按照1、今日工作、2：明日计划、3：风险和需要协助、4：思考和其他输出日报。

请基于下面的 JSON 数据，生成一份简洁、专业、适合直接发送的中文工作日志文档。

硬性要求：
1. 只输出最终日志正文，不要解释，不要加前言。
2. 必须严格使用以下四个标题：
1、今日工作：
2、明日计划：
3、风险和需要协助：
4、思考和其他：
3. 你需要整体浏览当日工作内容，先理解后再归纳总结，当日所有工作均需一条条总结列出来，不要遗漏。
4. “今日工作”必须优先依据当天记录生成，整体描述采用书面化表达；如果原始内容口语化，需要改写成书面语。
5. “明日计划”必须综合参考三部分信息：`tomorrow.items` 中第二天已填写的工作安排、`tomorrow_weekly_plan` 中第二天在每周工作安排里填写的上午/下午/其他待定内容，以及当天遗留事项和未完成内容；优先级依次为第二天已填写的工作安排、每周工作安排、当天遗留事项。
6. “风险和需要协助”需要结合当天工作、遗留事项和风险信息进行分析，归纳可能存在的风险、依赖项、需要协助的事项；没有则写“暂无”。
7. “思考和其他”保持简洁，可补充经验总结、后续关注点；没有则写“暂无”。
8. “今日工作”和“明日计划”中的每一条事项，都按照“客户名称+服务类型归属+冒号+具体内容”的形式梳理，例如“捷泰交付：......”“盛和POC：......”“赛力斯服务：......”。其中服务类型归属要根据 item_type / service_type_label 归纳为交付、POC、服务、方案、基建等简洁表述，不要漏掉。
9. 每条内容都要围绕真实工作本身展开，整体表达要专业、书面、克制，避免口语化描述。
10. “明日计划”在参考 tomorrow_weekly_plan 时，只提炼其中的实际工作安排本身，不要写出“按周计划”“每周工作安排显示”“周计划中提到”等字眼。
11. 日报内容中不要机械罗列项目类型、销售、工时字段，也不要直接照搬 JSON 字段名；但客户名称、服务类型归属、工作内容、遗留事项、风险等有效信息需要体现在合适的位置。
12. 不要凭空编造客户、事项、结果，也不要自行添加原始数据中未涉及的目标、结论、动作或背景；仅允许做少量明确可解释的整理、改写与归纳。
13. 除四个一级标题外，正文条目一律使用阿拉伯数字序号格式，如“1. ...”“2. ...”“3. ...”，不要使用“-”“*”等符号作为标签。
14. 如果“明日计划”同时存在第二天已填写的工作安排和每周工作安排内容，需要做去重整合后输出，避免重复表述。
15. 语言要自然、正式、适合工作日报场景，尽量用条目列出。

数据如下：
{json.dumps(context, ensure_ascii=False, indent=2)}
"""


def build_word_document(content: str, title: str) -> bytes:
    def build_paragraph_xml(line: str) -> str:
        normalized_line = line.replace("\t", "    ")
        if not normalized_line.strip():
            return "<w:p/>"

        text = escape(normalized_line)
        preserve_space = ' xml:space="preserve"' if normalized_line != normalized_line.strip() or "  " in normalized_line else ""
        is_heading = normalized_line.startswith(
            ("1、今日工作：", "2、明日计划：", "3、风险和需要协助：", "4、思考和其他：")
        )
        run_props = "<w:rPr><w:b/><w:sz w:val=\"28\"/></w:rPr>" if is_heading else "<w:rPr><w:sz w:val=\"24\"/></w:rPr>"
        return f"<w:p><w:r>{run_props}<w:t{preserve_space}>{text}</w:t></w:r></w:p>"

    paragraphs_xml = "".join(build_paragraph_xml(line) for line in content.splitlines())
    created_at = datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
    safe_title = escape(title)
    content_types_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
</Types>
"""
    rels_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>
"""
    app_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"
            xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes">
  <Application>Codex Daily Planner</Application>
</Properties>
"""
    core_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"
                   xmlns:dc="http://purl.org/dc/elements/1.1/"
                   xmlns:dcterms="http://purl.org/dc/terms/"
                   xmlns:dcmitype="http://purl.org/dc/dcmitype/"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>{safe_title}</dc:title>
  <dc:creator>Codex Daily Planner</dc:creator>
  <cp:lastModifiedBy>Codex Daily Planner</cp:lastModifiedBy>
  <dcterms:created xsi:type="dcterms:W3CDTF">{created_at}</dcterms:created>
  <dcterms:modified xsi:type="dcterms:W3CDTF">{created_at}</dcterms:modified>
</cp:coreProperties>
"""
    styles_xml = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults>
    <w:rPrDefault>
      <w:rPr>
        <w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:eastAsia="Microsoft YaHei" w:cs="Calibri"/>
        <w:sz w:val="24"/>
        <w:lang w:val="zh-CN" w:eastAsia="zh-CN"/>
      </w:rPr>
    </w:rPrDefault>
  </w:docDefaults>
</w:styles>
"""
    document_xml = f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body>
    {paragraphs_xml}
    <w:sectPr>
      <w:pgSz w:w="11906" w:h="16838"/>
      <w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/>
    </w:sectPr>
  </w:body>
</w:document>
"""

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types_xml)
        archive.writestr("_rels/.rels", rels_xml)
        archive.writestr("docProps/app.xml", app_xml)
        archive.writestr("docProps/core.xml", core_xml)
        archive.writestr("word/document.xml", document_xml)
        archive.writestr("word/styles.xml", styles_xml)
    return buffer.getvalue()


def generate_daily_log_via_codex(work_date: str) -> bytes:
    context = build_daily_log_context(work_date)
    if not CODEX_BIN or not Path(CODEX_BIN).exists():
        raise RuntimeError("未找到 codex 命令，无法生成日志文档。")
    if not NODE_BIN or not Path(NODE_BIN).exists():
        raise RuntimeError("未找到 node 命令，无法调用 codex 生成日志文档。")

    prompt = build_codex_log_prompt(context)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as output_file:
        output_path = output_file.name

    command = [
        NODE_BIN,
        CODEX_BIN,
        "exec",
        "--skip-git-repo-check",
        "-C",
        str(BASE_DIR),
        "--sandbox",
        "read-only",
        "--output-last-message",
        output_path,
        prompt,
    ]

    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
            env={**os.environ, "PATH": f"/opt/homebrew/bin:{os.environ.get('PATH', '/usr/bin:/bin:/usr/sbin:/sbin')}"},
        )
        if completed.returncode != 0:
            error_text = (completed.stderr or completed.stdout or "").strip()
            raise RuntimeError(error_text or "codex 生成日志失败。")

        content = Path(output_path).read_text(encoding="utf-8").strip()
        if not content:
            raise RuntimeError("codex 没有返回日志内容。")
        return build_word_document(content, f"{work_date} 工作日志")
    finally:
        try:
            Path(output_path).unlink(missing_ok=True)
        except OSError:
            pass


def build_daily_log_docx_filename(work_date: str) -> str:
    normalized_date = validate_date(work_date).replace("-", "")
    return f"{normalized_date}日志.docx"


def render_index_html() -> str:
    _, weekly_settings, _ = get_weekly_plan_settings(date.today().isoformat())
    ui_settings, _ = get_ui_settings()
    html = INDEX_HTML.replace("__INITIAL_DATE__", date.today().isoformat())
    html = html.replace("__INITIAL_MONTH__", date.today().strftime("%Y-%m"))
    html = html.replace(
        "__INITIAL_SETTINGS__",
        json.dumps(weekly_settings, ensure_ascii=False),
    )
    html = html.replace(
        "__INITIAL_UI_SETTINGS__",
        json.dumps(ui_settings, ensure_ascii=False),
    )
    return html


class DailyPlannerHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self._send_html(render_index_html())
            return

        if parsed.path == "/api/entry":
            query = parse_qs(parsed.query)
            requested_date = query.get("date", [""])[0]
            try:
                self._send_json({"entry": fetch_entry(validate_date(requested_date))})
            except ValueError:
                self._send_json({"error": "日期格式必须是 YYYY-MM-DD。"}, status=HTTPStatus.BAD_REQUEST)
            return

        if parsed.path == "/api/entries":
            self._send_json({"entries": fetch_recent_entries()})
            return

        if parsed.path == "/api/settings":
            week_start, settings, updated_at = get_weekly_plan_settings(date.today().isoformat())
            self._send_json({"week_start": week_start, "settings": settings, "updated_at": updated_at})
            return

        if parsed.path == "/api/ui-settings":
            settings, updated_at = get_ui_settings()
            self._send_json({"settings": settings, "updated_at": updated_at})
            return

        if parsed.path == "/api/weekly-plan":
            query = parse_qs(parsed.query)
            requested_date = query.get("date", [""])[0] or date.today().isoformat()
            try:
                week_start, settings, updated_at = get_weekly_plan_settings(requested_date)
                self._send_json({"week_start": week_start, "settings": settings, "updated_at": updated_at})
            except ValueError:
                self._send_json({"error": "日期格式必须是 YYYY-MM-DD。"}, status=HTTPStatus.BAD_REQUEST)
            return

        if parsed.path == "/api/month":
            query = parse_qs(parsed.query)
            target_month = query.get("month", [""])[0]
            try:
                entries = fetch_month_entries(target_month)
                self._send_json(
                    {
                        "month": validate_month(target_month),
                        "entries": entries,
                        "stats": build_month_stats(entries),
                    }
                )
            except ValueError:
                self._send_json({"error": "月份格式必须是 YYYY-MM。"}, status=HTTPStatus.BAD_REQUEST)
            return

        if parsed.path == "/api/export":
            query = parse_qs(parsed.query)
            target_month = query.get("month", [""])[0]
            try:
                month = validate_month(target_month)
                entries = fetch_month_entries(month)
                filename = f"daily-planner-{month}.xlsx"
                self._send_file(
                    build_excel_file(entries, month),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    filename,
                )
            except ValueError:
                self._send_json({"error": "月份格式必须是 YYYY-MM。"}, status=HTTPStatus.BAD_REQUEST)
            return

        if parsed.path == "/api/export-log":
            query = parse_qs(parsed.query)
            requested_date = query.get("date", [""])[0]
            try:
                work_date = validate_date(requested_date)
                content = generate_daily_log_via_codex(work_date)
                filename = build_daily_log_docx_filename(work_date)
                (BASE_DIR / filename).write_bytes(content)
                self._send_file(
                    content,
                    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    filename,
                )
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            except RuntimeError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)
            return

        self._send_json({"error": "未找到对应接口。"}, status=HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        if self.path == "/api/settings":
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_payload = self.rfile.read(content_length)
                payload = json.loads(raw_payload.decode("utf-8"))
                week_start = str(payload.get("week_start", date.today().isoformat())).strip() or date.today().isoformat()
                saved_week_start, settings, updated_at = save_weekly_plan_settings(week_start, payload)
                self._send_json({"week_start": saved_week_start, "settings": settings, "updated_at": updated_at})
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            except json.JSONDecodeError:
                self._send_json({"error": "请求体必须是合法 JSON。"}, status=HTTPStatus.BAD_REQUEST)
            return

        if self.path == "/api/weekly-plan":
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_payload = self.rfile.read(content_length)
                payload = json.loads(raw_payload.decode("utf-8"))
                week_start = str(payload.get("week_start", date.today().isoformat())).strip() or date.today().isoformat()
                settings_payload = payload.get("settings", payload)
                saved_week_start, settings, updated_at = save_weekly_plan_settings(week_start, settings_payload)
                self._send_json({"week_start": saved_week_start, "settings": settings, "updated_at": updated_at})
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            except json.JSONDecodeError:
                self._send_json({"error": "请求体必须是合法 JSON。"}, status=HTTPStatus.BAD_REQUEST)
            return

        if self.path == "/api/ui-settings":
            try:
                content_length = int(self.headers.get("Content-Length", "0"))
                raw_payload = self.rfile.read(content_length)
                payload = json.loads(raw_payload.decode("utf-8"))
                settings, updated_at = save_ui_settings(payload)
                self._send_json({"settings": settings, "updated_at": updated_at})
            except ValueError as error:
                self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
            except json.JSONDecodeError:
                self._send_json({"error": "请求体必须是合法 JSON。"}, status=HTTPStatus.BAD_REQUEST)
            return

        if self.path != "/api/entry":
            self._send_json({"error": "未找到对应接口。"}, status=HTTPStatus.NOT_FOUND)
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_payload = self.rfile.read(content_length)
            payload = json.loads(raw_payload.decode("utf-8"))
            self._send_json({"entry": upsert_entry(payload)}, status=HTTPStatus.CREATED)
        except json.JSONDecodeError:
            self._send_json({"error": "请求体必须是合法 JSON。"}, status=HTTPStatus.BAD_REQUEST)
        except ValueError as error:
            self._send_json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path != "/api/entry":
            self._send_json({"error": "未找到对应接口。"}, status=HTTPStatus.NOT_FOUND)
            return
        query = parse_qs(parsed.query)
        requested_date = query.get("date", [""])[0]
        try:
            removed = delete_entry(requested_date)
            if not removed:
                self._send_json({"error": "该日期没有可删除的记录。"}, status=HTTPStatus.NOT_FOUND)
                return
            self._send_json({"ok": True, "date": requested_date})
        except ValueError:
            self._send_json({"error": "日期格式必须是 YYYY-MM-DD。"}, status=HTTPStatus.BAD_REQUEST)

    def log_message(self, format: str, *args) -> None:
        return

    def _send_html(self, html: str, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload: dict, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, content: bytes, content_type: str, filename: str) -> None:
        fallback_name = filename.encode("ascii", errors="ignore").decode("ascii") or "download.bin"
        encoded_name = quote(filename)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Disposition", f"attachment; filename=\"{fallback_name}\"; filename*=UTF-8''{encoded_name}")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def run() -> None:
    init_db()
    server = ThreadingHTTPServer((HOST, PORT), DailyPlannerHandler)
    print(f"Daily Planner running at http://{HOST}:{PORT}")
    print(f"Database file: {DB_PATH}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\\nServer stopped.")
    finally:
        server.server_close()


if __name__ == "__main__":
    run()
