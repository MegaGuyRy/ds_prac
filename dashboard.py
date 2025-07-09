import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns

# Load API key from file
with open("api_key.txt") as f:
    API_KEY = f.read().strip()

# Build URL
url = f"https://api.eia.gov/v2/seriesid/PET.RWTC.D?API_KEY={API_KEY}"

# Fetch data
response = requests.get(url)
data_json = response.json()

# Check for error
if "error" in data_json:
    print("API error:", data_json["error"])
else:
    data = data_json["response"]["data"]
    df = pd.DataFrame(data)

# Reorganize dataframe with relievant data
df = df[["period", "value", "units"]].copy()

# Convert period to pandas datetime format
df["period"] = pd.to_datetime(df["period"])
df.rename(columns={"period": "Date", "value": "Price", "units": "Unit"}, inplace=True)
df = df.sort_values("Date")

# Build out streamlit dashboard
st.title("Supply Chain Dashboard")
st.write("Data Automaticlly Updated From API")

# Rolling interactive window
window = st.slider(label="Rolling Average Window:", min_value=1, max_value=60, value=30)
df["RollingAvg"] = df["Price"].rolling(window=window).mean() # Create rolling average column in dataframe 

# Build figure using seaborn
sns.set(style="whitegrid")
fig, ax = plt.subplots(figsize=(10,5))

# Plot data on line plot
sns.lineplot(data=df, x="Date", y="Price", color="green", ax=ax)

#Plot rolling avg
sns.lineplot(data=df, x="Date", y="RollingAvg", color="red", label=f"{window}-day Avg", ax=ax)

# Construct the rest of the figure
ax.set_title("Crude Oil Prices")
ax.set_xlabel("Date")
ax.set_ylabel("Price (USD/barrel)")
ax.legend()

st.pyplot(fig)
