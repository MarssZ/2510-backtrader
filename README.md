# Backtrader 学习项目

使用 backtrader 探索量化交易策略的 demo 集合。

## 项目结构

```
src/
├── data_source.py     # 数据获取（A股/指数/港股，Tushare Pro批量接口）
├── beta.py            # Beta系数计算
├── tracking_error.py  # 跟踪误差计算
└── utils.py           # 通用工具（收益率对齐等）

demos/
├── 01_sma_crossover.py        # 双均线交叉策略
├── 02_beta_calculation.py     # Beta系数批量计算
└── 03_tracking_error.py       # Beta + 跟踪误差 + 风险分解

.env                   # 配置文件（需自行创建）
.env.example           # 配置模板
README.md
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
# 双均线策略
uv run python demos/01_sma_crossover.py

# Beta批量计算
uv run python demos/02_beta_calculation.py

# 风险分解分析
uv run python demos/03_tracking_error.py
```

## Demo 列表

| 编号 | 名称 | 说明 | 核心指标 |
|------|------|------|----------|
| 01 | SMA Crossover | 5日/20日均线交叉策略 | 回测收益、夏普比率 |
| 02 | Beta Calculation | 25支股票Beta批量计算 | Beta、波动率、相关系数 |
| 03 | Tracking Error | Beta + 跟踪误差 + 风险分解 | 系统风险、残差风险、跟踪误差 |

## 数据源

- **Tushare Pro API** (需注册token: https://tushare.pro/)
- **日期范围**: 固定时间段 (默认 20241007-20251007，约1年)
- **批量获取**: 减少API调用 (25只股票 → 2-3次请求)
- **支持市场**: A股、港股、指数

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
- Tushare Pro - A股/港股数据
- numpy/pandas - 数据分析
- uv - 依赖管理
