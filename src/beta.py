"""Beta系数计算工具

Beta系数是现代投资组合理论(MPT)的核心概念，衡量资产相对市场的系统性风险敞口。

理论基础：
- β = 1: 资产与市场同步波动（如沪深300指数基金）
- β > 1: 资产波动放大市场波动（高风险高收益，如科技股）
- β < 1: 资产波动小于市场波动（防御性资产，如公用事业）
- β = 0: 资产与市场无关（如无风险国债）

公式推导：
    β = Cov(R_asset, R_market) / Var(R_market)

其中：
- Cov(R_a, R_m): 资产收益率与市场收益率的协方差
- Var(R_m): 市场收益率的方差
"""
import numpy as np


def calculate_beta(asset_returns: np.ndarray,
                   market_returns: np.ndarray) -> float:
    """
    计算资产的Beta系数

    这是CAPM模型的核心参数，表示资产收益率对市场收益率的敏感度。

    Args:
        asset_returns: 资产日收益率数组（已对齐）
        market_returns: 市场基准日收益率数组（已对齐）

    Returns:
        float: Beta系数
            - β ≈ 1.0: 与市场同步
            - β > 1.0: 高波动性（进攻型）
            - β < 1.0: 低波动性（防御型）

    Examples:
        >>> asset_ret = np.array([0.01, -0.02, 0.015, -0.005, 0.008])
        >>> market_ret = np.array([0.008, -0.015, 0.012, -0.003, 0.006])
        >>> beta = calculate_beta(asset_ret, market_ret)
        >>> 0.8 < beta < 1.2  # 通常股票beta在此范围
        True

    Notes:
        - 使用ddof=1计算样本方差（无偏估计）
        - 协方差矩阵的[0,1]元素即为Cov(asset, market)
        - 假设收益率已经过对齐和NaN清理
    """
    # 核心计算：3行，零分支
    covariance = np.cov(asset_returns, market_returns)[0, 1]
    market_variance = np.var(market_returns, ddof=1)
    return covariance / market_variance
