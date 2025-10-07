"""通用工具函数"""
import numpy as np
import pandas as pd


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
