# UpLang

**UpLang** 是一个专为 Minecraft Java 版整合包开发者和汉化者设计的命令行工具，旨在帮助高效地提取、管理和更新 Mod 的本地化语言文件（主要是 `en_us` 和 `zh_cn`）。

如果在制作整合包的过程中，你苦恼于各个 Mod 频繁更新导致的语言键值（Key）变动，或者希望能更方便地维护一个集成的汉化资源包，那么 UpLang 将是你的得力助手。

## 🌟 主要功能

- 📦 **语言文件提取 (`init`)**：从一堆指定的 Mod `.jar` 文件中快速提取 `en_us.json` 和 `zh_cn.json` 到目标资源包目录。
- 🔄 **智能差异同步 (`update`)**：在 Mod 升级后，自动比对新旧 `en_us` 的差异（新增、修改、删除的键），并将这些变动智能同步到你的资源包中，确保汉化文件与最新 Mod 保持一致，避免汉化失效。
- 📥 **翻译便捷导入 (`import`)**：支持从其他的本地资源包目录或 `.zip` 压缩包中批量导入既有的 `zh_cn` 汉化成果，覆盖尚未翻译或过时的词条。
- 🛠️ **强大的 JSON 容错解析**：内置兼容性极强的 JSON 解析器，可完美处理带有注释（`//`, `#`）、多余逗号、花括号不匹配以及各种非 `UTF-8` 编码的非标准 Minecraft 语言文件。
- ⚡ **多线程极速处理**：支持指定并发参数 (`--workers`)，快速扫描和解析数以百计的 Mod。

## 📥 安装

要求环境：**Python >= 3.12**。

你可以通过 `pip` 或者 `uv` 安装：

```bash
# 使用 pip (已发布至 PyPI)
pip install uplang

# 推荐：使用 uv 运行（无需全局安装）
uv tool install uplang
# 或者
uvx uplang [COMMAND]
```

## 🚀 使用指南

UpLang 的核心在于维护一个整合了各个 Mod 语言文件的**资源包（Resource Pack）**的 `assets` 目录。

### 1. 初始化提取 (`init`)

第一次使用时，将整合包内的所有 Mod 语言文件一键提取到你的资源包 `assets` 目录下：

```bash
uplang init <MODS文件夹路径> <资源包ASSETS夹路径> [--workers 线程数]
```

**示例：**

```bash
uplang init .minecraft/mods .minecraft/resourcepacks/MyTranslationPack/assets --workers 8
```

这一步会在 `assets/` 目录下按 `{mod_id}/lang/{locale}.json` 的结构生成原文件。

### 2. 同步更新与维护 (`update`)

当你更新了整合包里的某些 Mod 后，原有的汉化可能会因为键名（Key）改变、新物品加入而失效。此时可使用 `update` 指令：

```bash
uplang update <MODS文件夹路径> <资源包ASSETS夹路径> [--workers 线程数]
```

UpLang 会自动解析 `.jar` 中最新的 `en_us` 文件，与资源包中旧的 `en_us` 进行比对，然后自动：

- **删除** 已被 Mod 作者弃用的冗余语言键。
- **添加** Mod 新增物品/内容的语言键。
- **更新** 原版英文已发生实质变更的词条。
  并将这些差异安全地同步到对应的 `zh_cn.json` 文件中，方便汉化者跟进。

### 3. 导入现成汉化 (`import`)

如果找到了社区里的汉化资源包或 `.zip`，你可以直接将其中的 `zh_cn` 映射合并到你的现有工作区：

```bash
uplang import <当前的ASSETS夹路径> <导入来源的资源包路径或ZIP>
```

**示例（导入资源包夹）：**

```bash
uplang import ./pack/assets ./other_translation_pack/assets
```

**示例（导入 ZIP 汉化包）：**

```bash
uplang import ./pack/assets community_translations.zip
```

UpLang 会自动寻找匹配的 `mod_id`，并智能替换资源包里尚未翻译的英文词条。

## ⚙️ 进阶特性

- **UTF-8 CJK 保护**：在处理语言读写时，UpLang 严格保障 CJK（中日韩）字符以及 Unicode 代理对（Surrogates）、私用区（Private-use）字符的安全传输和转义，确保生成的内容随时能被 MC 引擎正常读取。

## 📄 许可

本项目采用开源许可，详情请参阅 `LICENSE` 文件。
