# BidKing Fresh Bot

<p align="center">
  <img src="docs/assets/bidking-banner.svg" alt="BidKing Fresh Bot banner" width="100%" />
</p>

<p align="center">
  Windows OCR automation and bid assistant for BidKing.
</p>

<p align="center">
  <a href="README.en.md">English</a> |
  <a href="README.zh-CN.md">中文</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/platform-Windows%2010%2F11-0078D4" alt="Windows badge" />
  <img src="https://img.shields.io/badge/python-3.11%20%7C%203.12-3776AB" alt="Python badge" />
  <img src="https://img.shields.io/badge/license-MIT-16A085" alt="MIT badge" />
  <img src="https://img.shields.io/badge/gui-Tkinter-4B8BBE" alt="Tkinter badge" />
</p>

## Language Versions

- [English README](README.en.md)
- [中文 README](README.zh-CN.md)

## What this project is

BidKing Fresh Bot is an OCR-based automation tool for the Windows desktop game BidKing. It reads the game state, computes suggested bids, and drives the GUI automation loop from a Tkinter interface.

It exists to fuse two upstream projects — one that *clicks* ([bidking-bot](https://github.com/sarkozyfan/bidking-bot)) and one that *values loot* ([bidking_shadow](https://github.com/zxTinF/bidking_shadow)) — behind a single GUI and a packaged EXE, so a player can run a whole match end to end without editing JSON or wiring scripts together.

If you want the full project documentation, switch to one of the language-specific versions above.

## Provenance

This repository is an integration and adaptation of two upstream open-source projects: [Bidking_bot](https://github.com/sarkozyfan/bidking-bot) and [Bidking_shadow](https://github.com/zxTinF/bidking_shadow).

The codebase also contains original work, including the GUI layer, workflow integration, configuration handling, and project-level documentation. Some components are derived from or adapted from the upstream projects, while others are newly written for this repository.

## Quick Links

- [Why this project exists](README.en.md#why-this-project-exists)
- [Running it next to the game (and after building the EXE)](README.en.md#running-it-next-to-the-game)
- [Usage walkthrough — one full run, with demos](README.en.md#usage-walkthrough-one-full-run)
- [Calibrating for your screen](README.en.md#calibrating-for-your-screen)
- [Architecture](README.en.md#architecture) · [FAQ](README.en.md#faq)
- 中文：[使用全流程演示](README.zh-CN.md#使用全流程演示) · [项目简介](README.zh-CN.md#项目简介)

## Notes

- The repository includes the BidKing Shadow code under [bidking_shadow/](bidking_shadow), so no separate external installation is required for the default workflow.
- The default suggested-bid cap is 3,000,000.
- The walkthrough GIFs are embedded inline in the language-specific READMEs, each at the step it illustrates.
