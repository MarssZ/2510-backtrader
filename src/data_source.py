"""A股数据获取模块"""
import pandas as pd
import tushare as ts
from pathlib import Path


class ChinaStockAdapter:
    """A股数据适配器 - 使用 Tushare Pro API"""

    def __init__(self):
        self._setup_token()
        self.pro = ts.pro_api()

    def _setup_token(self):
        """从.env文件读取 tushare token"""
        env_file = Path(__file__).parent.parent / '.env'
        if not env_file.exists():
            raise FileNotFoundError(
                "未找到 .env 文件，请在项目根目录创建 .env 文件并设置 TUSHARE_TOKEN\n"
                "参考 .env.example"
            )

        with open(env_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('TUSHARE_TOKEN='):
                    token = line.strip().split('=', 1)[1]
                    ts.set_token(token)
                    return

        raise ValueError("在 .env 文件中未找到 TUSHARE_TOKEN 配置")

    def fetch_data(self, symbol: str, limit: int = 700) -> pd.DataFrame:
        """
        获取A股日线数据

        Args:
            symbol: 股票代码 (如: '600848' 或 '600848.SH')
            limit: 获取数据条数，默认700条

        Returns:
            以 datetime 为索引的 DataFrame，包含 OHLCV 数据
        """
        # 处理股票代码格式：自动添加 .SH 或 .SZ 后缀
        if '.' not in symbol:
            if symbol.startswith('6'):
                ts_symbol = f"{symbol}.SH"  # 沪市
            elif symbol.startswith(('0', '3')):
                ts_symbol = f"{symbol}.SZ"  # 深市
            else:
                ts_symbol = f"{symbol}.SH"  # 默认沪市
        else:
            ts_symbol = symbol

        # 获取数据
        df = self.pro.daily(ts_code=ts_symbol, limit=limit)

        if df is None or len(df) == 0:
            raise ValueError(f"未获取到股票 {ts_symbol} 的数据")

        return self._normalize_data(df)

    def _normalize_data(self, raw_data: pd.DataFrame) -> pd.DataFrame:
        """
        将 tushare 数据转换为 backtrader 需要的格式

        Tushare 字段: ts_code, trade_date, open, high, low, close, vol, amount
        Backtrader 需要: datetime(索引) + open, high, low, close, volume
        """
        result = pd.DataFrame({
            'datetime': pd.to_datetime(raw_data['trade_date']),
            'open': raw_data['open'],
            'high': raw_data['high'],
            'low': raw_data['low'],
            'close': raw_data['close'],
            'volume': raw_data['vol'],
        })

        # 按时间升序排列（从旧到新）
        result = result.sort_values('datetime')

        # 设置 datetime 为索引（backtrader 要求）
        result.set_index('datetime', inplace=True)

        return result
