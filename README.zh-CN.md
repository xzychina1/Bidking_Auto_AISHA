# BidKing Fresh Bot

<p align="center">
  <img src="docs/assets/bidking-banner.svg" alt="BidKing Fresh Bot banner" width="100%" />
</p>

<p align="center">
  Windows 上的 BidKing OCR 自动化助手，用 GUI 管理配置、识别界面状态、计算建议出价，并执行窗口点击与回合流程。
</p>

<p align="center">
  <a href="README.md">English</a> |
  <a href="README.zh-CN.md">中文</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/platform-Windows%2010%2F11-0078D4" alt="Windows badge" />
  <img src="https://img.shields.io/badge/python-3.11%20%7C%203.12-3776AB" alt="Python badge" />
  <img src="https://img.shields.io/badge/license-MIT-16A085" alt="MIT badge" />
  <img src="https://img.shields.io/badge/gui-Tkinter-4B8BBE" alt="Tkinter badge" />
</p>

## 目录

- [项目简介](#项目简介)
- [这个项目为什么存在](#这个项目为什么存在)
- [来源说明](#来源说明)
- [核心功能](#核心功能)
- [架构图](#架构图)
- [项目结构](#项目结构)
- [运行环境](#运行环境)
- [安装](#安装)
- [如何与游戏一起运行](#如何与游戏一起运行)
- [使用全流程演示](#使用全流程演示)
- [FAQ](#faq)
- [致谢](#致谢)
- [许可证](#许可证)

## 项目简介

BidKing Fresh Bot 是一个面向 Windows 桌面端《竞拍之王 / BidKing》的 OCR 识别与自动化工具。它读取拍卖界面、决定出价、并驱动鼠标键盘，让一整局拍卖在你不盯屏幕的情况下自动跑完。所有操作都集中在一个 Tkinter GUI 里：你选好地图、模式、角色和激进度，按下 **开启**，剩下的逐回合出价循环就交给程序。

## 这个项目为什么存在

它不是"又一个脚本"。它存在的理由，是补上两个上游项目各自留下的那一半。

- [bidking-bot](https://github.com/sarkozyfan/bidking-bot) 解决了**点击**这一半——输入自动化循环——但你得手改 JSON、在命令行里跑脚本来配置它。
- [bidking_shadow](https://github.com/zxTinF/bidking_shadow) 解决了**估值**这一半——读游戏日志、用掉落表给战利品定价——但它是一堆独立的 CSV 和脚本，和实时出价循环是脱节的。

两者都默认"有一个开发者坐在命令行前"，谁都没给你一个能**真正打一局**的入口。本仓库把这两半拼到一起，并补上让它们变成"可用产品"的那一层：

- **所有参数都在一个 GUI 里。** 地图、模式、角色、激进度、道具回合、出价上限、安全开关、shadow 估值，全是下拉框和勾选框——想玩，不用再手改 `config.json`。
- **估值直接接进实时循环。** 一个桥接层把 bidking_shadow 的单件估值直接喂给"马上要输入的那个出价"，而不是停留在离线计算。
- **分辨率无关。** 每一个点击点和截图区域都按 1920×1080 参考分辨率存储，运行时会**自动缩放**到你的真实窗口大小，所以窗口不是参考尺寸也能用。
- **可打包成 EXE。** `build_exe.ps1` 会生成一个单文件，内置 Python 和 OCR 模型，能在没有开发环境的 Windows 上直接运行。
- **一个手动计算器页**，可以脱离实时运行单独验证价格模型。

一句话：它把两个面向开发者的脚本，变成了玩家可以打开即用、从头跑到尾的东西。

## 来源说明

本仓库是对上面两个上游开源项目的整合与二次开发：

- [Bidking_bot](https://github.com/sarkozyfan/bidking-bot)
- [Bidking_shadow](https://github.com/zxTinF/bidking_shadow)

其中一部分功能、数据和思路来自上游项目，另一些部分则是本仓库新增的原创实现，例如 GUI、shadow 估值桥接、流程衔接、配置整合、分辨率缩放和文档整理。这样写的目的，是明确区分"整合引用"和"本仓库原创"的部分，避免让人误以为这里是完全从零独立实现的项目。

## 核心功能

- 整窗 OCR 轮询，识别当前回合、结束提示和大厅状态
- 把中央信息区解析成结构化的拍卖事实（回合、品类、价格线索）
- 根据可配置的单格价格、品类权重和激进度计算建议出价
- GUI 中直接切换地图、轮数、角色、模式和风险偏好——无需手改 JSON
- 支持道具使用回合、出价硬顶、可选安全开关和防黏递增
- 处理"对局结束"、"奖励继续"、"竞拍大厅"、"首页竞拍按钮"等过渡界面
- 启动时把游戏窗口拉到前台并可选居中，减少识别和输入失败
- 提供手动计算器页，便于单独验证价格模型

## 架构图

每条箭头都标注了**它传递的是什么**，组件也按所属泳道分组。（可编辑源文件：[docs/architecture/](docs/architecture)。）

**Context & Container 视图** —— 操作者驱动 GUI；运行时截图并 OCR 屏幕，把识别出的文字变成估值决策，再通过鼠标控制器作用到游戏上。

<img src="docs/architecture/context-container.png" alt="Context 与 Container 视图:操作者驱动 GUI,运行时截图并 OCR、经 Strategy & Valuation 决策,再通过 Mouse Controller 作用到 Game Client" width="100%" />

**Component & Sequence 视图** —— 同一条流程在组件粒度上的展开：GUI 触发截图与识别，OCR 引擎和图像匹配把价格输入交给估值器，策略引擎套用上限和阈值，鼠标控制器执行动作，日志组件则持久化配置与结果。

<img src="docs/architecture/components-sequence.png" alt="Component 与 Sequence 视图:GUI、OCR Engine、Image Matcher、Estimator、Strategy Engine、Mouse Controller、Logger & Config 按泳道分组" width="100%" />

可以理解为五步：**截图**窗口 → 对中央信息区做 **OCR + 解析** → 给这件拍品**估值** → 套用**激进度/上限** → 用鼠标键盘**执行**，循环直到达到设定的重复次数。

## 项目结构

```text
bidking-bot/
  README.md
  README.zh-CN.md
  README.en.md
  requirements.txt
  manual_bidking_advisor.py        # 价格模型 + 手动顾问
  bidking_fresh_bot/
    bidking_gui.py                 # Tkinter GUI（你实际运行的入口）
    fresh_bidking_bot.py           # 机器人循环 / 状态机
    bidking_shadow_bridge.py       # 把 shadow 估值接进循环
    config.json                    # 坐标、计时、模式、上限
    price_config.json              # 单格价格 + 品类权重
    start.ps1                      # 无界面跑机器人循环
    build_exe.ps1                  # 打包单文件 EXE
  bidking_maa_test/
    window_backend.py              # Win32 截图 + 坐标缩放
    central_info_parser.py         # OCR 文本 -> 结构化事实
    analyze_screenshot.py          # 在截图上叠加 ROI 框
    roi_config.json
  bidking_shadow/
    getlog/
    item_prices.csv
  docs/
    assets/
      bidking-banner.svg
      demos/                       # 全流程演示 GIF
```

## 运行环境

- Windows 10 或 Windows 11
- Python 3.11 或 Python 3.12
- 以**窗口化**方式运行的 BidKing 游戏
- 1920×1080 的游戏窗口最贴合默认坐标；其它尺寸会从该参考自动缩放

主要第三方依赖（来自 [requirements.txt](requirements.txt)）：Pillow、numpy、opencv-python、pyautogui、rapidocr-onnxruntime、onnxruntime、psutil、pyinstaller。

## 安装

创建虚拟环境并安装依赖：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r .\requirements.txt
```

如果 PowerShell 限制了脚本执行，可仅对当前会话临时放行：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

## 如何与游戏一起运行

机器人驱动的是**真实的**游戏窗口，所以运行期间 BidKing 必须一直开着。

1. 以**窗口化**模式启动 BidKing，最好是 1920×1080。
2. 机器人通过标题关键字 `"BidKing"` 找到窗口（`config.json` 里的 `window.title_keyword`）。如果有多个窗口匹配，把 `window.hwnd` 设成你要的那一个。
3. 按下 **开启** 时，它会把该窗口拉到前台，并默认居中（`window.center_on_start`），让输入和截图对齐。**运行期间不要移动或遮挡该窗口。**

### 打包 EXE 之后怎么用

`build_exe.ps1` 会生成一个单文件：

```powershell
cd .\bidking_fresh_bot
powershell -ExecutionPolicy Bypass -File .\build_exe.ps1
# 输出：bidking_fresh_bot\dist\BidKingFreshBot_release.exe
```

这个 EXE 内置了 Python、OCR 模型、`config.json` 和 `price_config.json`，因此可以在**没有安装 Python** 的 Windows 上直接运行。用法：

1. 启动 BidKing（窗口化）。
2. 双击 `BidKingFreshBot_release.exe`，会打开**完全相同的 GUI**——和 `python bidking_gui.py` 行为一致。
3. 在 GUI 里选好设置，点击 **开启**。

如果想改 EXE 自带的默认配置，编辑 `config.json` / `price_config.json` 后重新打包即可。

### 其它启动方式

```powershell
# 无界面跑机器人循环，使用 config.json
powershell -ExecutionPolicy Bypass -File .\bidking_fresh_bot\start.ps1
```

## 使用全流程演示

下面是一次真实的端到端运行长什么样——同一次连续会话录下来的，覆盖：启动 → 出价 → 对局结束。

### 第 0 步 —— 让助手和游戏并排打开

```powershell
cd .\bidking_fresh_bot
python .\bidking_gui.py
```

<img src="docs/assets/demos/01-launch-and-lobby.gif" alt="助手与处于竞拍大厅的游戏并排运行" width="100%" />

*左边是从源码运行的助手，右边是停在竞拍大厅的游戏。绿色的 **竞拍** 按钮就是机器人进入房间要点的入口。*

### 第 1 步 —— 在 "自动化" 标签页里配置本次运行

点击开启之前，先设置：

- **地图** —— 你要刷的地图，例如 `1. 快递盲盒堆`。
- **模式** —— `标准模式`，或 `快递跑刀`（会自动把地图锁定为快递盲盒堆，并按 `物品总数 × 单件价格` 出价）。
- **角色** —— 目前为 `爱莎`。
- **重复次数** —— 停止前要跑几局。
- **6. 拍卖激进度** —— `保守`（最低价）、`均衡`（平均价）、`激进`（平均价 +25%），或 `自定义` 配一个倍率（例如 `-0.2` = 平均价 80%，`0.8` = 平均价 180%）。
- **5. 道具使用回合** —— 勾选哪些回合自动使用最左边的道具。
- **4. 爱莎逻辑与安全** 里的可选项：**安全开关** 限制单回合相对上一回合的最大上浮，**防黏递增** 强制平稳的线性增长。出价**硬顶**默认 3,000,000。

### 第 2 步 —— 按下 开启

机器人会接管游戏窗口、居中，并开始轮询——从这一刻起，它会自己跑完 大厅 → 回合 → 出价 → 对局结束 的循环。

### 第 3 步 —— 第 1 轮：识别中央信息区并给拍品定价

<img src="docs/assets/demos/02-round1-read-center.gif" alt="第 1 轮 —— 识别中央信息区" width="100%" />

*第 1 轮。机器人对中央信息区做 OCR（角色 **艾莎** 和拍卖条件），解析成事实，在碰 **出价** 按钮之前先算出建议出价。*

### 第 4 步 —— 出价已提交

<img src="docs/assets/demos/03-bid-submitted.gif" alt="出价已提交 —— 已出价 vs 预估最低价" width="100%" />

*出价完成。底部显示 **已出价**，右侧显示 **当前预估最低价**——也就是价格模型对标的那个数。*

### 第 5 步 —— 中间回合：按品类估值

<img src="docs/assets/demos/04-category-valuation.gif" alt="带品类均价弹窗的中间回合" width="100%" />

*稍后的一个回合。竞拍信息弹窗给出某一品类的均价（这里金色品质均价 = 41270）。顾问会套用你的品类权重，每回合重新定价。*

### 第 6 步 —— 第 4 轮：决定性的竞争回合

<img src="docs/assets/demos/05-round4-compete.gif" alt="第 4 轮 —— 与其他玩家竞价" width="100%" />

*第 4 轮 —— 通常决定归属的一轮。左侧不断叠加对手的出价；机器人的出价（**已出价 144653**）被设定为高过预估最低价（50,757），同时不超过 3,000,000 上限。*

### 第 7 步 —— 对局结束：结算并继续

<img src="docs/assets/demos/06-match-end.gif" alt="对局结束 —— 结算界面与自动继续" width="100%" />

***对局结束**。机器人处理结算界面、点击继续，然后要么开始下一局，要么在达到 **重复次数** 后退出。*

### 关于出价上限

建议出价默认封顶 3,000,000，防止模型在极端情况下生成过高出价。可在 [bidking_fresh_bot/config.json](bidking_fresh_bot/config.json) 看到：

```json
"automation": {
  "bid_cap_price": 3000000
}
```

驱动所有决策的两个文件是 [bidking_fresh_bot/config.json](bidking_fresh_bot/config.json)（坐标、计时、模式、上限）和 [bidking_fresh_bot/price_config.json](bidking_fresh_bot/price_config.json)（单格价格和品类权重）。

## FAQ

### 为什么 GUI 启动后不会自己开始运行？

GUI 只是配置和启动入口。先检查参数，再点击 **开启** 才会开始循环。

### 为什么程序识别不到回合？

通常是捕获了错误的窗口，或者游戏界面和默认区域不一致。先检查窗口标题、分辨率和缩放。坐标会从 1920×1080 参考自动缩放，但如果点击位置不对，可以运行 `python fresh_bidking_bot.py --print-clicks` 查看每个点击实际落点，再去 `config.json` 改对应的项。

### 为什么建议出价有时偏低或偏高？

建议出价受价格模型、品类权重、风险偏好、安全限制和 3,000,000 上限影响。可在手动计算器页检查输入是否完整。

### 为什么我改了 JSON 但行为没变？

请确认你改的是正在运行的进程实际使用的那一份文件。最稳妥的方式是通过 GUI 修改后再重启。打包好的 EXE 用的是打包时内置的 `config.json`——要改它的默认值需要重新打包。

### 为什么程序会跳过某些回合？

某些回合可能已被处理过，或被去抖动逻辑、安全开关、结束提示检测拦截。日志区会写出原因（例如 `round X already handled; waiting` 或 `bid skipped: ...`）。

### 我必须用 1920×1080 吗？

不必。默认坐标是为 1920×1080 调的，但坐标会自动缩放到其它尺寸。差异很大的布局可能仍需在 `config.json` 里微调坐标。

## 致谢

感谢以下开源项目和思路来源：

- bidking_shadow: https://github.com/zxTinF/bidking_shadow
- bidking-bot: https://github.com/sarkozyfan/bidking-bot

本项目在此基础上整合了 GUI、OCR、价格建议和自动化流程。

## 许可证

本项目使用 MIT License 开源，详见 [LICENSE](LICENSE)。
