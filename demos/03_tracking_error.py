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
from src.beta import calculate_beta
from src.tracking_error import calculate_tracking_error
from src.utils import align_returns


def calculate_stock_metrics(returns_data: dict[str, pd.Series],
                             stock_code: str,
                             stock_name: str,
                             benchmark_code: str = '000300') -> dict:
    """
    计算单支股票的Beta、跟踪误差及相关指标

    Args:
        returns_data: 批量获取的收益率数据 {代码: Series}
        stock_code: 股票代码
        stock_name: 股票名称
        benchmark_code: 基准指数代码

    Returns:
        dict: 包含beta、跟踪误差、波动率、相关系数等指标，失败时返回error字段
    """
    # 检查数据存在性
    if stock_code not in returns_data or benchmark_code not in returns_data:
        return {
            'code': stock_code,
            'name': stock_name,
            'error': '数据获取失败'
        }

    asset_returns = returns_data[stock_code]
    market_returns = returns_data[benchmark_code]

    # 对齐交易日
    asset_arr, market_arr = align_returns(asset_returns, market_returns)

    # 检查数据充足性（至少需要100个交易日）
    if len(asset_arr) < 100:
        return {
            'code': stock_code,
            'name': stock_name,
            'error': f'数据不足({len(asset_arr)}条)'
        }

    # 计算指标（直接用对齐后的全部数据）
    beta = calculate_beta(asset_arr, market_arr)
    volatility = np.std(asset_arr, ddof=1) * np.sqrt(252) * 100  # 资产年化波动率%
    market_volatility = np.std(market_arr, ddof=1) * np.sqrt(252) * 100  # 基准年化波动率%
    correlation = np.corrcoef(asset_arr, market_arr)[0, 1]
    tracking_error = calculate_tracking_error(asset_arr, market_arr, annualized=True)

    # 风险分解：总风险² = 系统性风险² + 残差风险²
    systematic_risk = abs(beta) * market_volatility  # 系统性风险
    residual_risk = np.sqrt(max(0, volatility**2 - systematic_risk**2))  # 残差风险
    residual_ratio = (residual_risk / volatility) * 100  # 残差占比（0-100%）

    return {
        'code': stock_code,
        'name': stock_name,
        'beta': beta,
        'volatility': volatility,
        'market_volatility': market_volatility,
        'systematic_risk': systematic_risk,
        'residual_risk': residual_risk,
        'residual_ratio': residual_ratio,
        'tracking_error': tracking_error,
        'correlation': correlation,
        'data_points': len(asset_arr)
    }


def format_table(results: list[dict], start_date: str, end_date: str, actual_days: int) -> str:
    """
    将结果格式化为纯文本对齐表格

    Args:
        results: 计算结果列表
        start_date: 数据起始日期
        end_date: 数据结束日期
        actual_days: 实际交易日数量

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
    lines.append(f'数据范围: {start_date} ~ {end_date} (实际{actual_days}个交易日)')
    lines.append('=' * 100)

    # 表头
    lines.append(
        f"{'排名':>4} {'代码':>8} {'名称':<8} {'Beta':>6} "
        f"{'资产波动':>10} {'基准波动':>10} {'系统风险':>10} "
        f"{'残差风险':>10} {'残差占比':>8} {'跟踪误差':>10} "
        f"{'相关系数':>8} {'数据点':>6}"
    )
    lines.append('-' * 110)

    # 成功的结果
    for i, r in enumerate(success, 1):
        lines.append(
            f"{i:>4} "
            f"{r['code']:>8} "
            f"{r['name']:<8} "
            f"{r['beta']:>6.2f} "
            f"{r['volatility']:>9.2f}% "
            f"{r['market_volatility']:>9.2f}% "
            f"{r['systematic_risk']:>9.2f}% "
            f"{r['residual_risk']:>9.2f}% "
            f"{r['residual_ratio']:>7.1f}% "
            f"{r['tracking_error']:>9.2f}% "
            f"{r['correlation']:>8.4f} "
            f"{r['data_points']:>6}"
        )

    # 失败的结果
    if failed:
        lines.append('')
        lines.append('计算失败:')
        lines.append('-' * 110)
        for r in failed:
            lines.append(f"  {r['code']:<10} {r['name']:<10} {r['error']}")

    lines.append('=' * 100)

    # 统计摘要
    if success:
        avg_beta = sum(r['beta'] for r in success) / len(success)
        max_beta = max(r['beta'] for r in success)
        min_beta = min(r['beta'] for r in success)
        avg_vol = sum(r['volatility'] for r in success) / len(success)
        avg_market_vol = sum(r['market_volatility'] for r in success) / len(success)
        avg_sys = sum(r['systematic_risk'] for r in success) / len(success)
        avg_res = sum(r['residual_risk'] for r in success) / len(success)
        avg_res_ratio = sum(r['residual_ratio'] for r in success) / len(success)
        avg_te = sum(r['tracking_error'] for r in success) / len(success)
        max_te = max(r['tracking_error'] for r in success)
        min_te = min(r['tracking_error'] for r in success)

        lines.append(f"成功: {len(success)}支  失败: {len(failed)}支")
        lines.append(f"Beta范围: [{min_beta:.2f}, {max_beta:.2f}]  平均: {avg_beta:.2f}")
        lines.append(f"平均资产波动: {avg_vol:.2f}%  平均基准波动: {avg_market_vol:.2f}%")
        lines.append(f"平均系统风险: {avg_sys:.2f}%  平均残差风险: {avg_res:.2f}%")
        lines.append(f"平均残差占比: {avg_res_ratio:.1f}%")
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

    # 数据日期范围（1年）
    start_date = '20241007'
    end_date = '20251007'

    print('Beta + 跟踪误差批量计算工具')
    print(f'基准指数: 沪深300')
    print(f'数据范围: {start_date} ~ {end_date}')
    print(f'股票数量: {len(STOCK_LIST)}支')
    print('=' * 100)

    # 批量获取所有股票+基准的收益率（2-3次API调用：A股1批+港股1批+指数1个）
    all_symbols = [code for code, _ in STOCK_LIST] + [benchmark]
    print(f'批量获取 {len(all_symbols)} 只股票数据...', end=' ')
    returns_data = adapter.fetch_returns_batch(all_symbols, start_date, end_date)

    # 统计实际交易日数量（取基准的长度作为参考）
    actual_days = len(returns_data.get(benchmark, [])) if benchmark in returns_data else 0
    print(f'✓ 成功获取 {len(returns_data)} 只（实际{actual_days}个交易日）\n')

    print('开始计算...\n')

    results = []
    for i, (code, name) in enumerate(STOCK_LIST, 1):
        print(f'[{i}/{len(STOCK_LIST)}] 计算 {code} {name}...', end=' ')
        result = calculate_stock_metrics(returns_data, code, name, benchmark)
        results.append(result)

        if 'error' in result:
            print(f'❌ {result["error"]}')
        else:
            print(f'✓ Beta={result["beta"]:.4f} TE={result["tracking_error"]:.2f}%')

    # 输出表格
    print('\n')
    print(format_table(results, start_date, end_date, actual_days))


if __name__ == "__main__":
    main()
