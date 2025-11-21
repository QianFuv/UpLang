# UpLang

一个用于更新 Minecraft Java Edition 整合包语言文件的命令行工具。

## 1. 安装

### 1.1 要求

- Python >= 3.13
- pip 或 uv 包管理器

### 1.2 使用 pip 安装

```bash
pip install uplang
```

### 1.3 使用 uv 安装

```bash
uv add uplang
```

### 1.4 从源代码安装

```bash
git clone https://github.com/QianFuv/UpLang
cd UpLang
uv pip install -e .
```

## 2. 主要命令

### 2.1 同步语言文件

将 mods 目录中的语言文件同步到资源包:

```bash
uplang sync <mods目录> <资源包目录>
```

选项:
- `--dry-run` - 模拟运行,不修改文件
- `--force` - 忽略缓存,处理所有 mod
- `-p, --parallel <数量>` - 并行工作线程数(默认: 4)

### 2.2 检查差异

检查差异而不进行同步:

```bash
uplang check <mods目录> <资源包目录>
```

### 2.3 列出 mod 信息

列出所有 mod 及其语言文件:

```bash
uplang list <mods目录>
```

### 2.4 提取语言文件

从单个 mod JAR 文件提取语言文件:

```bash
uplang extract <mod文件.jar> <输出目录>
```

### 2.5 显示详细差异

显示单个 mod 的详细差异:

```bash
uplang diff <mod文件.jar> <资源包目录>
```

### 2.6 清理孤立文件

删除不存在的 mod 的语言文件:

```bash
uplang clean <mods目录> <资源包目录>
```

选项:
- `-y, --yes` - 跳过确认,直接删除

### 2.7 翻译统计

显示翻译统计信息:

```bash
uplang stats <资源包目录>
```

### 2.8 格式化 JSON

修复 JSON 格式并同步键顺序:

```bash
uplang format <资源包目录>
```

选项:
- `--dry-run` - 检查而不修改文件
- `--check` - 仅检查问题,不修复

### 2.9 缓存管理

清除缓存以强制完全同步:

```bash
uplang cache clear <资源包目录>
```

### 2.10 全局选项

所有命令都支持以下全局选项:

- `-v, --verbose` - 启用详细输出
- `-q, --quiet` - 静默模式(仅显示错误)
- `--no-color` - 禁用彩色输出
- `--log-file <路径>` - 指定日志文件路径
- `--version` - 显示版本信息
- `--help` - 显示帮助信息
