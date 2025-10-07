import sys
from pathlib import Path
# 将项目根目录添加到模块搜索路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import backtrader as bt
from src.data_source import ChinaStockAdapter


class SmaStrategy(bt.Strategy):
    """双均线交叉策略：5日均线上穿20日均线做多，下穿做空"""

    def __init__(self):
        # 创建两条均线
        sma5 = bt.indicators.SMA(self.data.close, period=5)
        sma20 = bt.indicators.SMA(self.data.close, period=20)
        # 交叉信号：正值=金叉，负值=死叉
        self.crossover = bt.indicators.CrossOver(sma5, sma20)

    def next(self):
        if not self.position:  # 没有持仓
            if self.crossover[0] > 0:  # 金叉
                self.buy()
                print(f'买入: {self.data.datetime.date(0)} 价格={self.data.close[0]:.2f}')
        else:  # 有持仓
            if self.crossover[0] < 0:  # 死叉
                self.sell()
                print(f'卖出: {self.data.datetime.date(0)} 价格={self.data.close[0]:.2f}')


def main():
    # 获取A股真实数据
    adapter = ChinaStockAdapter()
    df = adapter.fetch_data(symbol='600848', limit=1500)  # 上海临港

    print(f'获取数据: {len(df)} 条')
    print(f'时间范围: {df.index[0].date()} 至 {df.index[-1].date()}')

    # 创建Cerebro引擎
    cerebro = bt.Cerebro()
    cerebro.addstrategy(SmaStrategy)

    # 添加数据
    data = bt.feeds.PandasData(dataname=df)
    cerebro.adddata(data)

    # 设置初始资金
    cerebro.broker.setcash(100000.0)

    # 运行回测
    print('=' * 50)
    print(f'起始资金: {cerebro.broker.getvalue():.2f}')
    print('=' * 50)
    cerebro.run()
    print('=' * 50)
    print(f'最终资金: {cerebro.broker.getvalue():.2f}')
    print(f'收益率: {(cerebro.broker.getvalue() / 100000 - 1) * 100:.2f}%')
    print('=' * 50)


if __name__ == "__main__":
    main()
