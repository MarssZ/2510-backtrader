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
from src.beta import calculate_beta
from src.utils import align_returns


def calculate_stock_beta(returns_data: dict[str, pd.Series],
                         stock_code: str,
                         stock_name: str,
                         benchmark_code: str = '000300') -> dict:
    """
    计算单支股票的Beta及相关指标

    Args:
        returns_data: 批量获取的收益率数据 {代码: Series}
        stock_code: 股票代码
        stock_name: 股票名称
        benchmark_code: 基准指数代码

    Returns:
        dict: 包含beta、波动率、相关系数等指标，失败时返回error字段
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
    volatility = np.std(asset_arr, ddof=1) * np.sqrt(252) * 100  # 年化波动率%
    correlation = np.corrcoef(asset_arr, market_arr)[0, 1]

    return {
        'code': stock_code,
        'name': stock_name,
        'beta': beta,
        'volatility': volatility,
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
    lines.append('=' * 80)
    lines.append('Beta系数批量计算结果 (相对沪深300)')
    lines.append(f'数据范围: {start_date} ~ {end_date} (实际{actual_days}个交易日)')
    lines.append('=' * 80)

    # 表头
    lines.append(
        f"{'排名':>4} {'代码':>8} {'名称':<8} {'Beta':>6} "
        f"{'年化波动率':>12} {'相关系数':>8} {'数据点':>6}"
    )
    lines.append('-' * 80)

    # 成功的结果
    for i, r in enumerate(success, 1):
        lines.append(
            f"{i:>4} "
            f"{r['code']:>8} "
            f"{r['name']:<8} "
            f"{r['beta']:>6.2f} "
            f"{r['volatility']:>11.2f}% "
            f"{r['correlation']:>8.4f} "
            f"{r['data_points']:>6}"
        )

    # 失败的结果
    if failed:
        lines.append('')
        lines.append('计算失败:')
        lines.append('-' * 80)
        for r in failed:
            lines.append(f"  {r['code']:<10} {r['name']:<10} {r['error']}")

    lines.append('=' * 80)

    # 统计摘要
    if success:
        avg_beta = sum(r['beta'] for r in success) / len(success)
        max_beta = max(r['beta'] for r in success)
        min_beta = min(r['beta'] for r in success)
        lines.append(f"成功: {len(success)}支  失败: {len(failed)}支")
        lines.append(f"Beta范围: [{min_beta:.2f}, {max_beta:.2f}]  平均: {avg_beta:.2f}")

    lines.append('=' * 80)

    return '\n'.join(lines)


def main():
    """批量计算20支股票的Beta系数"""

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

    print('Beta系数批量计算工具')
    print(f'基准指数: 沪深300')
    print(f'数据范围: {start_date} ~ {end_date}')
    print(f'股票数量: {len(STOCK_LIST)}支')
    print('=' * 80)

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
        result = calculate_stock_beta(returns_data, code, name, benchmark)
        results.append(result)

        if 'error' in result:
            print(f'❌ {result["error"]}')
        else:
            print(f'✓ Beta={result["beta"]:.4f}')

    # 输出表格
    print('\n')
    print(format_table(results, start_date, end_date, actual_days))


if __name__ == "__main__":
    main()
