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

    df = df.set_index("DateTime").sort_index()
    df = df["2023-01-01":"2023-12-31"]
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
