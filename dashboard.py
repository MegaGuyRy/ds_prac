import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
import numpy as np

# Load API key from file
API_KEY = st.secrets["API_KEY"]
#with open("api_key.txt") as f:
    #API_KEY = f.read().strip()

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
st.subheader("Predicted Price for Next Entry (Polynomial Regression)")
unit_label = df["Unit"].iloc[0]
st.metric(label="Predicted Next Entry Price", value=f"{next_price:.3f} {unit_label}")

# ---------------------------------------------------
# Graph creation with seaborn
# ---------------------------------------------------
# Streamlit dashboard
st.title("Supply Chain Dashboard")
st.write("Data automatically updated from eia.gov API")

# Rolling average window
window = st.slider(label="Rolling Average Window:", min_value=1, max_value=200, value=100)
df["RollingAvg"] = df["Price"].rolling(window=window).mean()

# Build figure using seaborn
sns.set(style="whitegrid")
fig, ax = plt.subplots(figsize=(12,6))
sns.lineplot(data=df, x="Date", y="Price", color="green", ax=ax, alpha=0.5, label="Price")
sns.lineplot(data=df, x="Date", y="RollingAvg", color="red", label=f"{window}-day Avg", ax=ax)

# Labels
ax.set_title(f"{option} Price Over Time")
ax.set_xlabel("Date")
unit_label = df["Unit"].iloc[0]
ax.set_ylabel(f"Price ({unit_label})")
ax.legend()

# Plot data
st.pyplot(fig)

# Add df preview of the latest 20 entries
st.subheader("Latest 20 Data Points")
st.write(df.sort_values("Date", ascending=False).head(20))