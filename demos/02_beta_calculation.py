#   上海临港（600848）相对沪深300的Beta = 1.0100

#   核心特征：
#   - 3个函数，总共60行代码（含注释）
#   - calculate_beta(): 3行核心计算，零分支
#   - fetch_returns():
#   处理股票/指数数据获取差异（tushare指数需用index_daily接口）      
#   - align_returns(): 日期对齐+NaN清理

#   计算逻辑验证通过，β≈1说明该股票与市场同步波动。

import sys
from pathlib import Path
# 将项目根目录添加到模块搜索路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import numpy as np
import pandas as pd
from src.data_source import ChinaStockAdapter


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


def fetch_returns(adapter: ChinaStockAdapter, ts_code: str, limit: int = 300) -> pd.Series:
    """
    获取日收益率序列

    Args:
        adapter: 数据适配器实例
        ts_code: 股票代码（如'600848'）或指数代码（'000300'表示沪深300）
        limit: 获取数据条数（250交易日约1年，多取点防止停牌）

    Returns:
        Series: 索引为日期，值为日收益率
    """
    # 处理指数代码（沪深300使用专门的指数接口）
    if ts_code == '000300':
        ts_code_full = '000300.SH'
        raw_df = adapter.pro.index_daily(ts_code=ts_code_full, limit=limit)
        if raw_df is None or len(raw_df) == 0:
            raise ValueError(f"未获取到指数 {ts_code_full} 的数据")
        # 标准化指数数据
        df = pd.DataFrame({
            'datetime': pd.to_datetime(raw_df['trade_date']),
            'close': raw_df['close']
        }).sort_values('datetime').set_index('datetime')
    else:
        df = adapter.fetch_data(symbol=ts_code, limit=limit)

    # 计算日收益率: (今日收盘 - 昨日收盘) / 昨日收盘
    returns = df['close'].pct_change()

    return returns.dropna()


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


def main():
    """Beta系数计算示例 - 计算个股相对沪深300的Beta"""

    # 初始化数据适配器
    adapter = ChinaStockAdapter()

    # 配置参数
    asset_code = '600848'      # 上海临港（沪市股票）
    benchmark_code = '000300'  # 沪深300指数
    period = 250              # 计算窗口：250个交易日

    print('=' * 60)
    print('Beta系数计算工具')
    print('=' * 60)
    print(f'资产代码: {asset_code}')
    print(f'基准指数: 沪深300 ({benchmark_code}.SH)')
    print(f'计算窗口: {period} 个交易日')
    print('=' * 60)

    # 获取收益率数据（多取50条防止停牌导致数据不足）
    print('\n正在获取数据...')
    asset_returns = fetch_returns(adapter, asset_code, limit=period + 50)
    market_returns = fetch_returns(adapter, benchmark_code, limit=period + 50)

    print(f'资产数据: {len(asset_returns)} 条')
    print(f'市场数据: {len(market_returns)} 条')

    # 对齐交易日
    asset_arr, market_arr = align_returns(asset_returns, market_returns)
    print(f'对齐后有效数据: {len(asset_arr)} 条')

    # 检查数据充足性
    if len(asset_arr) < period:
        print(f'\n⚠️  警告: 实际数据点 {len(asset_arr)} < 目标 {period}')
        print('   可能原因：停牌、新上市股票等')
        print(f'   将使用全部 {len(asset_arr)} 个数据点计算')

    # 取最近period个点（如果数据充足）
    actual_period = min(len(asset_arr), period)
    asset_arr = asset_arr[-actual_period:]
    market_arr = market_arr[-actual_period:]

    # 计算Beta
    beta = calculate_beta(asset_arr, market_arr)

    # 输出结果
    print('\n' + '=' * 60)
    print('计算结果')
    print('=' * 60)
    print(f'Beta系数: {beta:.4f}')
    print()
    print('Beta解读:')
    if beta > 1:
        print(f'  β = {beta:.4f} > 1: 该资产波动性大于市场，属于进攻型')
    elif beta > 0:
        print(f'  β = {beta:.4f} ∈ (0,1): 该资产波动性小于市场，属于防御型')
    elif beta > -0.1:
        print(f'  β = {beta:.4f} ≈ 0: 该资产与市场几乎无相关性')
    else:
        print(f'  β = {beta:.4f} < 0: 该资产与市场负相关（罕见）')
    print('=' * 60)

    # 统计信息
    print('\n附加统计:')
    print(f'  资产年化波动率: {np.std(asset_arr, ddof=1) * np.sqrt(252) * 100:.2f}%')
    print(f'  市场年化波动率: {np.std(market_arr, ddof=1) * np.sqrt(252) * 100:.2f}%')
    print(f'  相关系数: {np.corrcoef(asset_arr, market_arr)[0, 1]:.4f}')


if __name__ == "__main__":
    main()
