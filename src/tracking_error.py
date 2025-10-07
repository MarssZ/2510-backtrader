"""跟踪误差计算工具

基于《主动投资组合管理》理论：
- 跟踪误差 (TE) 衡量组合相对基准的主动风险
- 公式: TE = σ(R_portfolio - R_benchmark)
- 区别于总风险，跟踪误差只关注超额收益的波动性
"""
import numpy as np


def calculate_tracking_error(asset_returns: np.ndarray,
                              benchmark_returns: np.ndarray,
                              annualized: bool = True) -> float:
    """
    计算跟踪误差 (Tracking Error)

    跟踪误差是超额收益序列的标准差，反映组合偏离基准的剧烈程度。
    这是LP(投资人)关注的"主动风险"，不同于FM(基金经理)关注的"总风险"。

    Args:
        asset_returns: 资产日收益率数组（已对齐）
        benchmark_returns: 基准日收益率数组（已对齐）
        annualized: 是否年化（默认True，乘以√252转换为年化百分比）

    Returns:
        float: 跟踪误差
            - 如annualized=True: 返回年化百分比值（如15.23表示15.23%）
            - 如annualized=False: 返回日度标准差（如0.012表示1.2%日波动）

    Examples:
        >>> asset_ret = np.array([0.01, -0.02, 0.015, -0.005])
        >>> bench_ret = np.array([0.008, -0.015, 0.012, -0.003])
        >>> calculate_tracking_error(asset_ret, bench_ret, annualized=False)
        0.00387...  # 日度跟踪误差约0.387%
    """
    # 核心计算：超额收益的标准差
    excess_returns = asset_returns - benchmark_returns
    te = np.std(excess_returns, ddof=1)

    if annualized:
        te = te * np.sqrt(252) * 100  # 年化并转为百分比

    return te
