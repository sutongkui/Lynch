
import streamlit as st
import yfinance as yf
import pandas as pd

import pandas as pd
import matplotlib.pyplot as plt

# plt中文展示
from pylab import mpl
mpl.rcParams['font.sans-serif'] = ['SimHei']  # 指定默认字体
mpl.rcParams['axes.unicode_minus'] = False  # 解决保存图像是负号'-'显示为方块的问题


def calculate_macd(data, fast_period=12, slow_period=26, signal_period=9):
    """
    计算MACD指标
    返回包含MACD、信号线和柱状图的DataFrame
    """
    data['EMA12'] = data['Close'].ewm(span=fast_period, adjust=False).mean()
    data['EMA26'] = data['Close'].ewm(span=slow_period, adjust=False).mean()
    data['MACD'] = data['EMA12'] - data['EMA26']
    data['Signal'] = data['MACD'].ewm(span=signal_period, adjust=False).mean()
    data['Histogram'] = data['MACD'] - data['Signal']
    return data


def main():
    st.title("美股智能筛选器")
    
    # 筛选条件
    st.sidebar.header("筛选条件")
    min_market_cap = st.sidebar.number_input("最小市值(亿美元)", min_value=0, value=20)
    filter_zhangdie = st.sidebar.checkbox("筛选过去250天涨跌幅为正的股票", value=True)
    min_current_price = st.sidebar.number_input("最小当前股价(美元)", min_value=0, value=10)
    
    # 用户输入股票代码
    stock_codes = st.text_input("请输入美股股票代码，用逗号分隔", "AAPL").split(",")
    stock_list = [code.strip() for code in stock_codes if code.strip()]
    
    # 添加提交按钮
    if st.button("提交"):
        if not stock_list:
            st.warning("请输入至少一个股票代码")
            return
        
        # 获取数据并筛选
        results = []
        for ticker in stock_list:
            try:
                stock = yf.Ticker(ticker)
                info = stock.info
                market_cap = info.get('marketCap', 0) / 1e8  # 转换为亿美元
                
                if market_cap >= min_market_cap:
                    hist = stock.history(period="250d")
                    if len(hist) > 0:
                        start_price = hist['Close'].iloc[0]
                        end_price = hist['Close'].iloc[-1]
                        change = (end_price - start_price) / start_price
                        
                        # 添加当前股价检查
                        current_price = info.get('currentPrice', 0)

                        # 计算macd
                        hist = stock.history(period="1y")
                        hist = calculate_macd(hist)
                        
                        # 生成买卖信号
                        last_row = hist.iloc[-1]
                        prev_row = hist.iloc[-2]
                        
                        buy_signal = (prev_row['MACD'] < prev_row['Signal']) and (last_row['MACD'] > last_row['Signal'])
                        sell_signal = (prev_row['MACD'] > prev_row['Signal']) and (last_row['MACD'] < last_row['Signal'])
                        
                        signal = "买入" if buy_signal else ("卖出" if sell_signal else "持有")
                        
                        if current_price >= min_current_price and (not filter_zhangdie or change > 0):
                            results.append({
                                '代码': ticker,
                                '名称': info.get('shortName', ''),
                                '市值(亿美元)': round(market_cap, 2),
                                '250天涨跌幅': f"{change*100:.2f}%",
                                '当前股价(美元)': round(current_price, 2),
                                'MACD': round(last_row['MACD'], 2),
                                '信号线': round(last_row['Signal'], 2),
                                '柱状图': round(last_row['Histogram'], 2),
                                '信号': signal
                            })

                            plt.figure(figsize=(10, 6))
                            plt.plot(hist.index, hist['MACD'], label='MACD')
                            plt.plot(hist.index, hist['Signal'], label='信号线')
                            plt.bar(hist.index, hist['Histogram'], label='柱状图', color='gray', alpha=0.3)
                            plt.title(f'{ticker} MACD指标')
                            plt.legend()
                            st.pyplot(plt)
                            plt.close()
                    

            except Exception as e:
                st.error(f"获取 {ticker} 数据时出错: {e}")
                continue
        
        # 显示结果
        if results:
            df = pd.DataFrame(results)
            st.dataframe(df)
        else:
            st.warning("没有找到符合条件的股票")

if __name__ == "__main__":
    main()