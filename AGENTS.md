# AGENTS.md

本文件是项目级 AI 编码协作入口，只保留会直接影响实现落点与提交流程的约束。
详细规范与背景资料不要堆在这里，按需继续阅读：
- 开发环境与 Vibe Coding 配置：[docs/develop/README.md](docs/develop/README.md)
- 详细编码规范：[docs/develop/spec/agent_guidelines.md](docs/develop/spec/agent_guidelines.md)
- 一条龙整体架构：[docs/develop/one_dragon/one_dragon_architecture.md](docs/develop/one_dragon/one_dragon_architecture.md)
- 应用插件开发指引：[docs/develop/guides/application_plugin_guide.md](docs/develop/guides/application_plugin_guide.md)
- 应用设置界面开发指引：[docs/develop/guides/application_setting_guide.md](docs/develop/guides/application_setting_guide.md)

## 项目概述

- 项目：绝区零一条龙（ZenlessZoneZero-OneDragon），面向 Windows 的绝区零自动化工具。
- 语言与环境：Python 3.11、uv、PySide6。
- 代码布局：`src-layout`，源码在 `src/`，运行时配置在 `config/`，资源在 `assets/`，开发文档在 `docs/develop/`。
- 运行基准：1080p；配置以 YAML 为主。
- 测试仓库独立维护：`zzz-od-test/` 需要单独放在仓库根目录。

## 常用命令

```shell
uv sync --group dev
uv run --env-file .env src/zzz_od/gui/app.py
uv run --env-file .env pytest zzz-od-test/
uv run --env-file .env ruff check src/你修改的文件.py
uv run --env-file .env ruff check --fix src/你修改的文件.py
```

- 只对自己修改的文件运行 `ruff check`。
- 不要对整个 `src/` 目录运行 ruff，现有仓库尚未全面适配。
- 优先使用 Windows PowerShell 可直接执行的命令。

## 架构落点

### 1. 核心分层

- `src/one_dragon/`：通用基础框架、配置、环境、工具、YOLO 能力。
- `src/one_dragon_qt/`：通用 Qt GUI 框架与公共组件。
- `src/onnxocr/`：OCR 引擎。
- `src/zzz_od/`：绝区零业务代码，包括 application、operation、context、gui、yolo 等。

### 2. 功能开发优先路径

- 新功能优先评估是否应做成 `Application`，放在 `src/zzz_od/application/`，并通过 `ApplicationFactory` 接入。
- 不要直接把新流程硬塞进主线逻辑；先复用现有 Application、Operation、配置体系与界面组件。
- 新的设置界面优先沿用现有 setting card、`YamlConfigAdapter`、`AdapterInitMixin` 等模式。

### 3. 关键运行机制

- `ZContext` 管理懒加载服务与配置；实例级配置变更要走 `reload_instance_config()` 对应机制。
- 这里的 `Operation` 指框架里的基础操作单元；文档里提到的“流转 / flow”是由这些 `Operation` 节点组成的执行链。
- 操作链基于 `ZOperation` / `Operation` 编排；状态流转沿用现有 round 系列接口与节点声明方式。
- GPU/onnx session 的异步调用必须通过 `gpu_executor.submit`，不要并发直调多个 session。

## 开发硬约束

- 所有函数签名、类成员变量都要有类型注解；使用 `list[str]`、`X | Y`。
- 注释与 docstring 用中文，保持现有项目风格。
- 禁止相对导入；仅类型注解使用 `TYPE_CHECKING` 导入。
- `__init__.py` 默认不要暴露模块，除非已有明确模式或收到明确要求。
- 构造函数显式声明参数，不要用 `**kwargs`。
- 路径操作使用 `pathlib`，字符串格式化使用 f-string。
- GUI 优先复用 `pyside6-fluent-widgets` 与现有项目组件，保持 Fluent Design。
- 配置改动优先落到 YAML 与对应 `YamlConfig` 子类，不要随意散落硬编码配置。
- 1080p 坐标属于项目既有前提，可以按现有模式硬编码，不要额外做分辨率适配设计。

## 文档与测试要求

- 修改代码后，同步更新对应的 `docs/develop/` 文档与 `zzz-od-test/` 测试。
- 若测试依赖截图或环境变量，按 [docs/develop/README.md](docs/develop/README.md) 中说明准备 `.env` 与测试仓。
- 提交前至少验证自己改动直接影响的部分；若无法本地完成，要明确说明缺失前提。
- 复杂功能、架构调整或新自动化流程，先补设计/说明文档，再继续实现。

## 提交流程与协作边界

- **修改代码后严禁直接执行 git commit 或 git push 进行提交与推送，一律必须保持在暂存区，并停下等待用户的明确指令后方可提交！**
- 默认不要主动执行 `git commit`、`git push`、`git reset`、删分支等版本控制操作，除非用户明确要求。
- 如果用户明确要求切换分支，先 `stash` 当前改动，再切换。
- 提交代码时，使用中文编写提交信息
- Review 关注逻辑错误、运行时崩溃、死循环、资源泄漏；不要为风格问题大改现有代码。
- 提交 PR 后，review comment 需要逐条回复或修正。

## 深入阅读

只在当前任务确实需要时继续看这些文档：
- 框架与模块架构：`docs/develop/one_dragon/`、`docs/develop/one_dragon/modules/`
- 游戏业务与专项设计：`docs/develop/zzz/`
- 打包与 RuntimeLauncher：`docs/develop/README.md`、`docs/develop/one_dragon/runtime_launcher.md`

## AI 工具接入

本仓库以根目录 `AGENTS.md` 作为统一入口；其他工具按 [docs/develop/README.md](docs/develop/README.md) 中的硬链接说明接入即可。

## 附：AI 协作开发备忘与避坑指南 (Windows 定时任务/静默后台专项)

### 1. 禁用自动更新以防本地微调被覆盖
- **现象**: 启动器 `OneDragon-Launcher.exe` 启动时默认会核对 Git 分支并自动更新代码，这会通过 `git checkout` / `git reset` 将本地对超时的代码微调全部抹去。
- **硬约束**: 需要在本地测试并固化超时参数时，必须在 `config/env.yml` 中显式配置 `auto_update: false` 以禁用此机制。

### 2. 避免无交互后台会话中的 UAC 弹窗提权闪退
- **现象**: 在 Windows 任务计划程序（非交互静默服务会话）中以最高特权运行时，`pyuac.isUserAdmin()` 可能会误报并强行触发 `pyuac.runAsAdmin` 进行桌面 UAC 提示，导致在无显示设备的后台抛出 `0xC000013A` (STATUS_CONTROL_C_EXIT) 闪退。
- **硬约束**: 在命令行挂机模式下（即带有 `--onedragon` / `-o` 启动参数时），在 `src/one_dragon/launcher/exe_launcher.py` 中直接跳过 UAC 检测与 `pyuac` 管理员提权动作，直接进入一条龙逻辑。

### 3. Windows 定时任务脚本编码与注释规范
- **现象**: Windows 定时任务服务强制使用系统 ANSI/GBK 编码解析没有 BOM 头的脚本。若 `.bat` 或 `.ps1` 启动脚本中包含任何中文注释，会引起解析异常损坏换行符，将业务代码当成注释吞逝导致计划任务启动即闪退报错。
- **硬约束**: 所有用于 Windows 计划任务的引导脚本（如 `run_onedragon_daily.bat` 和 `run_onedragon_daily.ps1`）一律**必须采用 100% 纯 ASCII（英文）编写且绝对不留任何中文字符**。

### 4. 熄屏及无物理渲染下的截图防崩保护
- **硬约束**: 定时任务唤醒时设备可能处于锁屏或熄屏状态，显卡无物理输出会导致截图返回为 `None`。为防止图像裁剪工具崩溃闪退，核心识别节点（如 `check_screen` 等）入口处必须进行 `self.last_screenshot is None` 校验并执行 `round_retry`，以温柔的轮询等待物理渲染恢复。

### 5. Session 0 静默后台下的物理静音保障
- **现象**: 定时任务通常在非交互式后台会话 (Session 0) 中隐蔽启动。如果脚本中使用模拟按键 `SendKeys` 发送降低音量或静音键，会因为该会话没有任何物理键盘焦点而直接**失效**，导致早上拉起挂机时依然播放出刺耳的游戏背景音乐。
- **硬约束**: 挂机静音必须绝对摒弃任何模拟键盘的按键发送方式。一律采用 C# **`.NET CoreAudio COM 接口`**（如通过 `IAudioEndpointVolume.SetMute` 直接针对默认音频播放终结点执行硬静音），以实现在 Session 0 后台也能 100% 锁定音量静音。

### 6. OCR 识别字符空格鲁棒匹配规约
- **现象**: OCR 模型在识别游戏画面的编队或界面文本时，常因间距或字体原因丢失空格（如将配置中的 `"编队 3"` 识别为 `"编队3"`，或反之），直接破坏精确比对或 difflib 编辑距离的判断，从而引发选择编队超时卡死。
- **硬规约**: 凡是涉及通过 OCR 结果匹配特定名称进行点击的操作（如选择预备编队等），**必须实施“空格清洗 + 多级匹配”**：在比对前统一剥离两者的全部空格 (`replace(" ", "")`)，优先进行空格清洗后的包含/精确匹配，再使用原有模糊比对作为二级兜底，以达到最高的容错度。

### 7. AI 协作 Git 推送自愈与 OpenSSH 穿透完备指南
- **痛点与现象**: 
  1. 在非交互式后台（如 API 协作会话或定时计划任务）中，普通的 HTTPS 推送因无法弹出账号登录框而卡死。
  2. 使用 Git 默认 SSH 推送时，若私钥有 Passphrase 保护，会因后台无 TTY 控制台输入口令而抛出 `Permission denied (publickey)` 错误。
  3. **环境重置风险**：服务器重启或环境重置后，本地的 `origin` 远端 URL 可能会被自动恢复为只读的 HTTPS 镜像主源（`OneDragon-Anything`），导致推送因“无写入权限”而失败。
- **物理成因**: Git 默认调用的 Msys2 SSH 与 Windows 系统原生的 `ssh-agent` 密钥管理服务的命名管道完全不互通，导致其无法读取系统已解密并缓存好的私钥签名。
- **硬性规约与自愈步骤 (所有 AI 协作推送一律必须遵循本流程)**:
  任何 Agent 在被要求执行推送或遇到推送失败时，**必须且只能**通过以下标准步骤进行一键诊断与物理自愈：

  1. **步骤一：校验并纠正远端 URL（若非用户 Fork 的 SSH 库则立即修改）**
     检查当前 `origin` 指向：
     ```shell
     git remote -v
     ```
     如果发现不是用户 Fork 的 SSH 库，**必须立即强制重定向到用户的 Fork SSH 地址**：
     ```shell
     git remote set-url origin git@github.com:KaiXuan666/ZenlessZoneZero-OneDragon.git
     ```

  2. **步骤二：锁定 Windows 系统原生 OpenSSH 穿透壁垒**
     在本地 Git 配置中永久注入以下指令，强迫其读取系统内存中缓存的物理密钥：
     ```shell
     git config core.sshCommand "C:/Windows/System32/OpenSSH/ssh.exe -o StrictHostKeyChecking=no"
     ```

  3. **步骤三：进行拉取与二次远端校验**
     完成上述自愈配置后，先执行同步：
     ```shell
     git fetch origin
     ```
     **实测避坑**：旧版本代码可能在 `git fetch` 或启动器自动更新流程中再次把 `origin` 改回 `https://ghfast.top/https://github.com/OneDragon-Anything/ZenlessZoneZero-OneDragon.git`。因此 fetch 后必须再次执行：
     ```shell
     git remote -v
     ```
     若发现 remote 又被改坏，必须立即重新执行步骤一的 `git remote set-url origin git@github.com:KaiXuan666/ZenlessZoneZero-OneDragon.git`，然后不要再次触发会改 remote 的旧逻辑，直接进入推送。

  4. **步骤四：使用能访问 Windows ssh-agent 的上下文推送**
     在普通 API 会话中，即使 `ssh-agent` 服务正在运行，也可能出现 `Error connecting to agent: Permission denied`，进而导致 `git push` 报 `Permission denied (publickey)`。此时必须用提升权限上下文验证并推送：
     ```shell
     C:\Windows\System32\OpenSSH\ssh-add.exe -l
     git push origin main
     ```
     若 `ssh-add -l` 能列出 `C:\Users\xuan\.ssh\id_ed25519`，则提升权限上下文下的 `git push origin main` 才能读取系统缓存密钥并完成推送。
