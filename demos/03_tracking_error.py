#   Beta + 跟踪误差批量计算演示
#
#   功能扩展：
#   - 保留02_demo的全部功能（Beta、波动率、相关系数）
#   - 新增跟踪误差 (Tracking Error) 指标
#
#   理论基础：
#   - Beta: 系统性风险敞口 β = Cov(R_p, R_b) / Var(R_b)
#   - 跟踪误差: 主动风险 TE = σ(R_p - R_b)
#   - 风险分解: σ²_p = β²σ²_b + TE²

import sys
from pathlib import Path
# 将项目根目录添加到模块搜索路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
from src.data_source import ChinaStockAdapter
from src.tracking_error import calculate_tracking_error


def calculate_beta(asset_returns: np.ndarray, market_returns: np.ndarray) -> float:
    """
    计算资产的Beta系数

    公式: β = Cov(r_asset, r_market) / Var(r_market)

    Args:
        asset_returns: 资产日收益率数组
        market_returns: 市场基准日收益率数组

    Returns:
        float: Beta系数
    """
    covariance = np.cov(asset_returns, market_returns)[0, 1]
    market_variance = np.var(market_returns, ddof=1)
    return covariance / market_variance


def align_returns(asset_ret: pd.Series, market_ret: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    """
    对齐两个收益率序列的交易日

    处理停牌、不同交易日历等问题

    Args:
        asset_ret: 资产收益率序列
        market_ret: 市场收益率序列

    Returns:
        (asset_array, market_array): 对齐后的numpy数组
    """
    # 取交集日期
    common_dates = asset_ret.index.intersection(market_ret.index)

    asset_aligned = asset_ret.loc[common_dates].values
    market_aligned = market_ret.loc[common_dates].values

    # 移除任何残留的NaN/Inf
    mask = np.isfinite(asset_aligned) & np.isfinite(market_aligned)

    return asset_aligned[mask], market_aligned[mask]


def calculate_stock_metrics(adapter: ChinaStockAdapter,
                             stock_code: str,
                             stock_name: str,
                             benchmark_code: str = '000300',
                             period: int = 250) -> dict:
    """
    计算单支股票的Beta、跟踪误差及相关指标

    Args:
        adapter: 数据适配器
        stock_code: 股票代码
        stock_name: 股票名称
        benchmark_code: 基准指数代码
        period: 计算窗口

    Returns:
        dict: 包含beta、跟踪误差、波动率、相关系数等指标，失败时返回error字段
    """
    try:
        # 获取收益率（多取50条防止停牌）
        asset_returns = adapter.fetch_returns(stock_code, limit=period + 50)
        market_returns = adapter.fetch_returns(benchmark_code, limit=period + 50)

        # 对齐交易日
        asset_arr, market_arr = align_returns(asset_returns, market_returns)

        # 检查数据充足性（至少需要100个交易日）
        if len(asset_arr) < 100:
            return {
                'code': stock_code,
                'name': stock_name,
                'error': f'数据不足({len(asset_arr)}条)'
            }

        # 取最近period个点
        actual_period = min(len(asset_arr), period)
        asset_arr = asset_arr[-actual_period:]
        market_arr = market_arr[-actual_period:]

        # 计算指标
        beta = calculate_beta(asset_arr, market_arr)
        volatility = np.std(asset_arr, ddof=1) * np.sqrt(252) * 100  # 年化波动率%
        correlation = np.corrcoef(asset_arr, market_arr)[0, 1]
        tracking_error = calculate_tracking_error(asset_arr, market_arr, annualized=True)

        return {
            'code': stock_code,
            'name': stock_name,
            'beta': beta,
            'volatility': volatility,
            'correlation': correlation,
            'tracking_error': tracking_error,
            'data_points': len(asset_arr)
        }

    except Exception as e:
        return {
            'code': stock_code,
            'name': stock_name,
            'error': str(e)[:30]  # 截断错误信息
        }


def format_table(results: list[dict]) -> str:
    """
    将结果格式化为纯文本对齐表格

    Args:
        results: 计算结果列表

    Returns:
        str: 格式化后的表格字符串
    """
    # 分离成功和失败的结果
    success = [r for r in results if 'beta' in r]
    failed = [r for r in results if 'error' in r]

    # 按Beta降序排序
    success.sort(key=lambda x: x['beta'], reverse=True)

    # 构建表格
    lines = []
    lines.append('=' * 100)
    lines.append('Beta + 跟踪误差批量计算结果 (相对沪深300)')
    lines.append('=' * 100)

    # 表头
    lines.append(
        f"{'排名':<4} {'代码':<10} {'名称':<10} {'Beta':<8} "
        f"{'年化波动率':>11} {'跟踪误差':>11} {'相关系数':<10} {'数据点':<8}"
    )
    lines.append('-' * 100)

    # 成功的结果
    for i, r in enumerate(success, 1):
        lines.append(
            f"{i:<4} "
            f"{r['code']:<10} "
            f"{r['name']:<10} "
            f"{r['beta']:<8.4f} "
            f"{r['volatility']:>10.2f}% "
            f"{r['tracking_error']:>10.2f}% "
            f"{r['correlation']:<10.4f} "
            f"{r['data_points']:<8}"
        )

    # 失败的结果
    if failed:
        lines.append('')
        lines.append('计算失败:')
        lines.append('-' * 100)
        for r in failed:
            lines.append(f"  {r['code']:<10} {r['name']:<10} {r['error']}")

    lines.append('=' * 100)

    # 统计摘要
    if success:
        avg_beta = sum(r['beta'] for r in success) / len(success)
        max_beta = max(r['beta'] for r in success)
        min_beta = min(r['beta'] for r in success)
        avg_te = sum(r['tracking_error'] for r in success) / len(success)
        max_te = max(r['tracking_error'] for r in success)
        min_te = min(r['tracking_error'] for r in success)

        lines.append(f"成功: {len(success)}支  失败: {len(failed)}支")
        lines.append(f"Beta范围: [{min_beta:.4f}, {max_beta:.4f}]  平均: {avg_beta:.4f}")
        lines.append(f"跟踪误差范围: [{min_te:.2f}%, {max_te:.2f}%]  平均: {avg_te:.2f}%")

    lines.append('=' * 100)

    return '\n'.join(lines)


def main():
    """批量计算股票的Beta系数和跟踪误差"""

    # 硬编码股票列表（代码, 名称）
    STOCK_LIST = [
        ('600519', '贵州茅台'),
        ('600036', '招商银行'),
        ('601318', '中国平安'),
        ('600276', '恒瑞医药'),
        ('600887', '伊利股份'),
        ('601012', '隆基绿能'),
        ('600848', '上海临港'),
        ('601888', '中国中免'),
        ('000858', '五粮液'),
        ('000333', '美的集团'),
        ('002594', '比亚迪'),
        ('002475', '立讯精密'),
        ('000001', '平安银行'),
        ('002415', '海康威视'),
        ('300750', '宁德时代'),
        ('600900', '长江电力'),
        ('601166', '兴业银行'),
        ('600009', '上海机场'),
        ('601398', '工商银行'),
        ('600030', '中信证券'),
        ('688981', '中芯国际'),
        ('688041', '海光信息'),
        ('000002', '万科A'),
        ('601127', '赛力斯'),
        ('9988', '阿里巴巴'),
    ]

    adapter = ChinaStockAdapter()
    benchmark = '000300'  # 沪深300
    period = 250

    print('Beta + 跟踪误差批量计算工具')
    print(f'基准指数: 沪深300')
    print(f'计算窗口: {period}个交易日')
    print(f'股票数量: {len(STOCK_LIST)}支')
    print('=' * 100)
    print('开始计算...\n')

    results = []
    for i, (code, name) in enumerate(STOCK_LIST, 1):
        print(f'[{i}/{len(STOCK_LIST)}] 计算 {code} {name}...', end=' ')
        result = calculate_stock_metrics(adapter, code, name, benchmark, period)
        results.append(result)

        if 'error' in result:
            print(f'❌ {result["error"]}')
        else:
            print(f'✓ Beta={result["beta"]:.4f} TE={result["tracking_error"]:.2f}%')

    # 输出表格
    print('\n')
    print(format_table(results))


if __name__ == "__main__":
    main()
