# Supply Chain Price Dashboard
[Dashboard Link](https://supplydashboard-ehua5uwxbqgc5q4fwp3zwg.streamlit.app)

## Summary
This project is an interactive data dashboard built in Python using Streamlit, Plotly, and Pandas. It tracks key commodity prices, crude oil, natural gas, and diesel, to displays trends, rolling averages, outlier detection, and predictive modeling. The dashboard fetches realtime price data from the U.S. Energy Information Administration (EIA) API, and provides an interactive interface for analysis.

## Features
**Automatic data updates:**  
- Fetches the most current commodity prices from the EIA API.

**Interactive visualizations:**  
- Plotly graphs with hover tooltips, zoom, and pan.
- Latest price and rolling averages directly annotated in the legend.

**Statistical insights:**  
- Sidebar displays metrics like current year highs/lows, mean, standard deviation.
- Identifies and highlights outliers beyond the 5th and 95th percentiles.

**Styled data tables:**  
- Highlights max and min prices in the latest entries.
- Shows embedded bars to compare prices visually.

**Polynomial regression prediction:**  
- Fits a regression model on historical data to forecast near-term price movement.

##
Data provided by the **U.S. Energy Information Administration (EIA)** Open Data API.
