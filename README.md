# Backtrader 学习项目

使用 backtrader 探索量化交易策略的 demo 集合。

## 项目结构

```
├── demos/                          # 所有示例代码
│   ├── 01_sma_crossover.py        # 双均线交叉策略（A股真实数据）
│   └── ...                        # 更多 demo 持续添加
├── src/                           # 共享代码
│   └── data_source.py            # A股数据获取（Tushare）
├── .env                          # 配置文件（需自行创建）
├── .env.example                  # 配置模板
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
uv sync
```

### 2. 配置 Tushare Token

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件，填入你的 Tushare token
# 获取方式：访问 https://tushare.pro/ 注册
```

### 3. 运行 Demo

```bash
# 运行第一个 demo：双均线策略（可从任何目录运行）
uv run python demos/01_sma_crossover.py
```

## Demo 列表

| 编号 | 名称 | 说明 | 状态 |
|------|------|------|------|
| 01 | SMA Crossover | 5日/20日均线交叉策略 | ✅ |
| 02 | TBD | 待添加 | ⏳ |

## 开发约定

- **编号规则**：demo 按学习顺序编号（01, 02, 03...）
- **独立运行**：每个 demo 可独立执行，可从任何目录运行
- **代码共享**：通用代码放在 `src/` 下
- **渐进增长**：需要时再抽取共享代码，避免过度设计
- **路径修复**：每个 demo 开头需包含以下代码以导入 src 模块：
  ```python
  import sys
  from pathlib import Path
  sys.path.insert(0, str(Path(__file__).parent.parent))
  ```

## 技术栈

- Python 3.12
- backtrader - 量化回测框架
- tushare - A股数据获取
- uv - 依赖管理
