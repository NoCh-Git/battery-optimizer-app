import pandas as pd
import matplotlib.pyplot as plt

def load_and_preprocess_prices(uploaded_file):
    # Specify the separator!
    df = pd.read_csv(uploaded_file, sep=';')

    # # Clean column names
    # df.columns = df.columns.str.strip()

    # Access known columns
    df["DateTime"] = pd.to_datetime(df["Start date"], utc=True)
    df["Price_EUR_per_kWh"] = df["Germany/Luxembourg [€/MWh] Original resolutions"] / 1000
    if not any(df["DateTime"].dt.year == 2023):
        raise ValueError("❌ The uploaded data does not contain any entries from the year 2023. All tests and optimizations are based on the year 2023. Please upload a file with data from 2023.")
    df = df["2023-01-01":"2023-12-31"] # Filter for the year 2023, if needed, change to any other year or modify the date range.
    df["Price_EUR_per_kWh"] = df["Price_EUR_per_kWh"].interpolate()

    return df[["Price_EUR_per_kWh"]]

def plot_results(df):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df.index, df["SoC_kWh"], label="SoC")
    ax.plot(df.index, df["charge_kWh"], label="Charge", alpha=0.6)
    ax.plot(df.index, df["discharge_kWh"], label="Discharge", alpha=0.6)
    ax.set_title("Battery Operation")
    ax.set_ylabel("kWh")
    ax.legend()
    return fig
