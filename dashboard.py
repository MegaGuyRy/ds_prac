import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Load API key from file
#API_KEY = st.secrets["API_KEY"]
with open("api_key.txt") as f:
    API_KEY = f.read().strip()

# Commodity dictionary
COMMODITIES = {
    "WTI Crude Oil": "seriesid/PET.RWTC.D",
    "Brent Crude Oil": "seriesid/PET.RBRTE.D",
    "Henry Hub Natural Gas": "seriesid/NG.RNGWHHD.D",
    "NY Petroleum": "petroleum/pri/spt/data",
    #"Heating Oil": "PET.EMD_EPD2D_PTE_NUS_DPG.D",
    #"Diesel": "PET.EMD_EPD2DXL0_PTE_NUS_DPG.D",
    #"U.S. Gasoline Avg": "PET.EMD_EPMR_PTE_NUS_DPG.D"
}

# Select box on dashboard
option = st.selectbox(
    "Choose commodity data to display",
    list(COMMODITIES.keys())
)
series_id = COMMODITIES[option]

# Build URL
if option in ["WTI Crude Oil", "Brent Crude Oil", "Henry Hub Natural Gas"]:
    url = f"https://api.eia.gov/v2/{series_id}?api_key={API_KEY}"
elif option == "NY Petroleum":
    facets = ("frequency=daily&data[]=value"
              "&facets[duoarea][]=Y35NY"
              "&facets[process][]=PF4"
              "&facets[product][]=EPMRU"
              "&facets[series][]=EER_EPMRU_PF4_Y35NY_DPG")
    url = f"https://api.eia.gov/v2/{series_id}?api_key={API_KEY}&{facets}"

# Fetch data
response = requests.get(url)
data_json = response.json()

# Check for error
if "error" in data_json:
    st.error(f"API error: {data_json['error']}")
    st.stop()
else:
    data = data_json["response"]["data"]
    df = pd.DataFrame(data)

# Reorganize dataframe
df = df[["period", "value", "units"]].copy()
df["period"] = pd.to_datetime(df["period"])
df.rename(columns={"period": "Date", "value": "Price", "units": "Unit"}, inplace=True)
df = df.sort_values("Date")

# If NY Petroleum, convert and round Price to nearest tenth
if option == "NY Petroleum":
    df["Price"] = pd.to_numeric(df["Price"], errors="coerce").astype(float)
    df["Price"] = df["Price"].round(3)

# Sort data to ensure correct order
df = df.sort_values("Date")

# ---------------------------------------------------
# Polynomial Regression for next entry prediction
# ---------------------------------------------------
# Changes date time to numerical values so modle can evaluate it
df["Days"] = (df["Date"] - df["Date"].min()).dt.days

# Drop any rows with missing Price or Days
df = df.dropna(subset=["Price", "Days"])
df = df[~(df["Price"] < 0)]

X = df["Days"].values.reshape(-1, 1) # Converts Days to  a 2D numpy array (matrix shape)
y = df["Price"].values

# Creates new features like days^2 for degree so the regression can fit a curve
poly = PolynomialFeatures(degree=2)
X_poly = poly.fit_transform(X)

# Fit model on polynomial features
model = LinearRegression()
model.fit(X_poly, y)

# Makes a prediction for the next entry by plugging in the next day count
next_entry = np.array([[df["Days"].max() + 1]])
next_entry_poly = poly.transform(next_entry)
next_price = model.predict(next_entry_poly)[0]

# Show prediction on dashboard
st.subheader("Commodities Cost Supply Dashboard With Polynomial Regression")
unit_label = df["Unit"].iloc[0]
st.metric(label="Predicted Next Entry Price", value=f"{next_price:.2f} {unit_label}")

# ---------------------------------------------------
# Graph creation with plotly
# ---------------------------------------------------
# Streamlit dashboard
st.title("Supply Chain Dashboard")
st.write("Data automatically updated from eia.gov API")

# Rolling average window
window = st.slider(label="Rolling Average Window:", min_value=1, max_value=200, value=100)
df["RollingAvg"] = df["Price"].rolling(window=window).mean()

# Plotly figure with interactive hover
fig = px.line(
    df,
    x="Date",
    y="Price",
    title=f"{option} Price Over Time",
    #markers=True
)

# Add rolling average as a second line
fig.add_trace(
    go.Scatter(
        x=df["Date"],
        y=df["RollingAvg"],
        mode='lines',
        name=f"{window}-day Avg",
        line=dict(color="red")
    )
)

# Update axis labels
fig.update_layout(
    xaxis_title="Date",
    yaxis_title=f"Price ({df['Unit'].iloc[0]})",
    legend_title="Legend"
)

# Calculate percentile bounds
lower_bound = df["Price"].quantile(0.05)
upper_bound = df["Price"].quantile(0.95)

# Find outliers
outliers = df[(df["Price"] < lower_bound) | (df["Price"] > upper_bound)]

# Add to plotly chart
fig.add_trace(
    go.Scatter(
        x=outliers["Date"],
        y=outliers["Price"],
        mode="markers",
        name="Outliers",
        marker=dict(color="orange", size=8, symbol="cross")
    )
)


# Show plot in Streamlit
st.plotly_chart(fig, use_container_width=True)

#------------------------------------
# Data for changing data vis
#---------------------------------------

# Declare the 2 latest entries
latest_price = df["Price"].iloc[-1]
previous_price = df["Price"].iloc[-2]

# Change from last entry to most recent
change_last_entry = latest_price - previous_price
percent_change_last_entry = (change_last_entry / previous_price) * 100

# Change from last month
one_month_ago = df["Date"].iloc[-1] - pd.DateOffset(days=30)
one_month_df = df[df["Date"] <= one_month_ago]
if not one_month_df.empty:
    price_one_month_ago = one_month_df["Price"].iloc[-1]
    change_month = latest_price - price_one_month_ago
    percent_change_month = (change_month / price_one_month_ago) * 100
else:
    change_month = 0
    percent_change_month = 0
    
# Change from last year
one_year_ago = df["Date"].iloc[-1] - pd.DateOffset(days=365)
one_year_df = df[df["Date"] <= one_year_ago]
if not one_year_df.empty:
    price_one_year_ago = one_year_df["Price"].iloc[-1]
    change_year = latest_price - price_one_year_ago
    percent_change_year = (change_year / price_one_year_ago) * 100
else:
    change_year = 0
    percent_change_year = 0

#---------------------------------------
# min and max this month
#---------------------------------------
# Create new df only containing entries from the current year
this_year = df["Date"].iloc[-1].year
df_this_year = df[df["Date"].dt.year == this_year]

# Max price from this year
max_price_this_year = df_this_year["Price"].max()

# Max price from this year
min_price_this_year = df_this_year["Price"].min()

#---------------------------------------
# Write design vis to page
#---------------------------------------
st.sidebar.header("Price Change Insights")

# Display in sidebar or page
st.sidebar.markdown(f"**5th percentile:** {lower_bound:.2f}")
st.sidebar.markdown(f"**95th percentile:** {upper_bound:.2f}")
st.sidebar.markdown(f"**Outliers detected:** {outliers.shape[0]}")
st.sidebar.write("**Mean Price:**", f"{df['Price'].mean():.2f}")
st.sidebar.write("**Std Dev:**", f"{df['Price'].std():.2f}")

st.sidebar.markdown("---")

# Last entry change
st.sidebar.metric(
    label="Since Last Entry",
    value=f"{latest_price:.2f} {unit_label}",
    delta=f"{change_last_entry:+.2f} ({percent_change_last_entry:+.2f}%)"
)

st.sidebar.markdown("---")

# Last month change
st.sidebar.metric(
    label="Since Last Month",
    value=f"{latest_price:.2f} {unit_label}",
    delta=f"{change_month:+.2} ({percent_change_month:+.2f}%)"
)

st.sidebar.markdown("---")

# Last year change
st.sidebar.metric(
    label="Since Last Year",
    value=f"{latest_price:.2f} {unit_label}",
    delta=f"{change_year:+.2f} ({percent_change_year:+.2f}%)"
)

st.sidebar.markdown("---")

st.sidebar.metric(
    label=f"{this_year} Highest Price",
    value=f"{max_price_this_year:.2f} {unit_label}",
)

st.sidebar.markdown("---")

st.sidebar.metric(
    label=f"{this_year} Lowest Price",
    value=f"{min_price_this_year:.2f} {unit_label}",
)

# df preview with styling
st.subheader("Latest 20 Data Points")

recent_df = df.sort_values("Date", ascending=False).head(20).copy()
recent_df["Price"] = recent_df["Price"].map("{:.2f}".format)
recent_df["RollingAvg"] = recent_df["RollingAvg"].map("{:.4f}".format)
price_col_name = f"Price ({df['Unit'].iloc[0]})"
recent_df.rename(columns={"Price": price_col_name}, inplace=True)

styled_df = recent_df.style\
    .highlight_max(subset=[price_col_name], color='green')\
    .highlight_min(subset=[price_col_name], color='red')\

st.dataframe(styled_df)

