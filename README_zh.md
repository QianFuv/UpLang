# UpLang

[![PyPI](https://img.shields.io/pypi/v/UpLang)](https://badge.fury.io/py/uplang)
[![Python](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2FQianFuv%2FUpLang%2Frefs%2Fheads%2Fmain%2Fpyproject.toml)](https://www.python.org/downloads/)
[![License](https://img.shields.io/github/license/QianFuv/UpLang)](https://opensource.org/licenses/MIT)
[![Downloads](https://img.shields.io/pypi/dm/uplang?color=light-green)](https://pypi.org/project/uplang/)

**UpLang** 是一个强大的命令行工具，专为简化 Minecraft Java 版模组包的本地化工作流程而设计。它自动化了管理多个模组翻译文件的复杂过程，确保英文和中文语言文件之间的完美同步，同时保持翻译完整性和键值排序。

## 🌐 语言

[English](README.md) | **简体中文**

## 🚀 核心特性

- **🔍 智能模组检测**: 自动扫描和跟踪新增、更新和删除的模组
- **🔄 智能同步**: 保持翻译顺序的同时添加缺失键值并移除过时键值
- **🛡️ 强健错误处理**: 高级JSON解析，具备多重回退策略处理格式错误的文件
- **📊 进度跟踪**: 丰富的控制台界面，提供实时进度指示器
- **🌐 跨平台支持**: 在Windows、macOS和Linux上无缝运行
- **⚡ 增量更新**: 大型模组包的高效差异处理
- **🎯 顺序保持**: 维护语言文件中的原始键值排序
- **📚 专业文档**: 全面的文档字符串和代码注释
- **🔧 依赖注入**: 具有可测试组件的清洁架构

## 📋 系统要求

- **Python**: 3.11 或更高版本
- **操作系统**: Windows、macOS 或 Linux
- **Minecraft**: Java版（Forge/Fabric模组）

## 🛠️ 安装

### 方式一: 从PyPI安装（推荐）

从PyPI直接安装UpLang是最简单的方式：

```bash
# 安装UpLang
pip install uplang

# 验证安装
uplang --help
```

### 方式二: 开发环境安装

用于贡献或开发目的：

```bash
# 克隆仓库
git clone https://github.com/QianFuv/UpLang.git
cd UpLang

# 使用uv（推荐用于开发）
pip install uv
uv sync
uv pip install -e .

# 或直接使用pip
pip install -e .
```

## 📖 使用方法

### 初始设置

对于新项目或设置新资源包时：

```bash
uplang init <模组目录> <资源包目录>
```

**示例:**
```bash
uplang init "~/.minecraft/mods" "./我的资源包"
```

**功能说明:**
- 🔍 扫描模组目录中的所有JAR文件
- 📂 创建必要的 `assets/<模组id>/lang/` 结构
- 📄 从每个模组中提取 `en_us.json`
- 🔄 复制或创建 `zh_cn.json` 文件
- ⚙️ 执行初始同步
- 💾 保存项目状态以供未来比较

### 更新翻译

当您添加、更新或删除模组时：

```bash
uplang check <模组目录> <资源包目录>
```

**示例:**
```bash
uplang check "~/.minecraft/mods" "./我的资源包"
```

**功能说明:**
- 📊 将当前状态与上次扫描进行比较
- 🆕 识别新增、更新和删除的模组
- 🔄 将新翻译键合并到现有文件中
- 🧹 移除过时的键值
- ✅ 同步所有语言文件
- 💾 更新项目状态

## 📁 输出结构

运行UpLang后，您的资源包将具有以下结构：

```
我的资源包/
├── assets/
│   ├── 模组一/
│   │   └── lang/
│   │       ├── en_us.json
│   │       └── zh_cn.json
│   ├── 模组二/
│   │   └── lang/
│   │       ├── en_us.json
│   │       └── zh_cn.json
│   └── ...
├── pack.mcmeta（如果存在）
├── .uplang_state.json（项目状态）
└── uplang_*.log（操作日志）
```

## 🧪 测试

运行综合测试套件以验证一切正常工作：

```bash
# 运行所有测试
PYTHONPATH=src python -m pytest tests/ -v

# 生成覆盖率报告
PYTHONPATH=src python -m pytest tests/ --cov=uplang --cov-report=html

# 运行特定测试模块
PYTHONPATH=src python -m pytest tests/test_json_utils.py -v    # JSON处理测试
PYTHONPATH=src python -m pytest tests/test_models.py -v        # 数据模型测试
PYTHONPATH=src python -m pytest tests/test_utils.py -v         # 工具函数测试

# 如果使用uv开发环境
uv run pytest tests/ -v
```

测试套件包括：
- **数据模型测试**: 模组对象、比较结果和同步统计的综合验证
- **JSON处理**: 具备编码回退、格式错误JSON恢复和顺序保持的强健解析
- **工具函数**: 文件名清理、模组ID创建和路径处理
- **错误处理**: 边缘情况、无效输入和优雅恢复策略
- **Unicode支持**: 国际字符、表情符号和编码边缘情况
- **顺序保持**: 确保JSON键值排序在操作期间得到维护

### 当前测试覆盖范围

- ✅ **数据模型**: 模组元数据、比较结果、同步统计
- ✅ **JSON处理**: 多编码支持、格式错误JSON恢复、OrderedDict保持
- ✅ **工具函数**: 安全文件名处理、模组ID生成、字符串操作
- ✅ **错误处理**: 异常层次结构和上下文保持
- ✅ **Unicode处理**: 国际字符支持和编码回退

## 🔧 高级特性

### 强健的JSON处理

UpLang处理真实世界的边缘情况：
- **多种编码**: UTF-8、UTF-8-sig、Latin1、CP1252
- **格式错误的JSON**: 尾随逗号、未引用的键、注释
- **编码问题**: UTF-8 BOM、代理字符
- **恢复策略**: 多重解析回退

### 翻译保护

- **现有翻译** 在同步期间始终得到保留
- **键值排序** 遵循英文语言文件结构
- **增量更新** 仅处理已更改的文件以提高效率
- **原子操作** 确保数据完整性

### 代码质量标准

- **全面文档**: 所有模块、类和方法都包含详细的文档字符串
- **类型安全**: 整个代码库的完整类型注解
- **错误处理**: 具有上下文信息的分层异常系统
- **清洁架构**: 依赖注入和关注点分离
- **专业标准**: 行业级别的代码组织和文档

### 日志和监控

- **详细日志** 保存到带时间戳的文件
- **进度指示器** 用于长时间运行的操作
- **错误报告** 带有上下文和建议解决方案
- **状态跟踪** 用于调试和审计

## 🤝 贡献

我们欢迎贡献！请查看我们的[贡献指南](CONTRIBUTING.md)了解详情：
- 🐛 报告错误
- 💡 建议功能
- 🔧 设置开发环境
- 📝 代码风格指南
- ✅ 测试要求

## 📄 许可证

该项目根据MIT许可证授权 - 有关详细信息，请参阅[LICENSE](LICENSE)文件。

## 🙏 致谢

- 使用[Rich](https://github.com/Textualize/rich)构建美观的控制台输出
- 使用[uv](https://github.com/astral-sh/uv)进行快速依赖管理
- 受Minecraft模组社区本地化需求的启发

## 📞 支持

- 🐛 **问题**: [GitHub Issues](https://github.com/QianFuv/UpLang/issues)
- 💬 **讨论**: [GitHub Discussions](https://github.com/QianFuv/UpLang/discussions)
- 📧 **联系**: [项目维护者](https://github.com/QianFuv)

---

<div align="center">
  <strong>用❤️为Minecraft模组社区制作</strong>
</div>