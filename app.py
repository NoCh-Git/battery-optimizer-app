import streamlit as st
from optimization import rolling_optimize_battery
from utils import load_and_preprocess_prices, plot_results

st.title("Battery Optimization Explorer")

uploaded_file = st.file_uploader("Upload SMARD CSV", type="csv")
if uploaded_file:
    df = load_and_preprocess_prices(uploaded_file)
    st.line_chart(df["Price_EUR_per_kWh"])
    ##################
    st.subheader("⚙️ Optimization Parameters")

    col1, col2 = st.columns(2)

    with col1:
        capacity = st.number_input("🔋 Capacity (kWh)", 100, 10000, 1000)
        max_power = st.number_input("⚡ Max Power (kW)", 50, 1000, 500)

    with col2:
        eff = st.slider("🔁 Efficiency", 0.5, 1.0, 0.9)
        grid_fee = st.number_input("💸 Grid Fee (€/kWh)", 0.0, 0.5, 0.04)
        degradation = st.number_input("🧪 Degradation Cost (€/kWh moved)", 0.0, 0.1, 0.01)
    ###################
    if st.button("Run Optimization"):
        with st.spinner("⏳ Running optimization... this may take up to 10 minutes for the whole year due to the large number of optimization runs in the rolling optimization model..."):
            result_df, profit = rolling_optimize_battery(df, capacity, max_power, eff, grid_fee, degradation)
            if result_df is not None:
                st.success(f"Optimization complete. Total profit: €{profit:,.2f}") 
                st.info("⚠️ The final 12 hours of data were skipped due to unavailable price forecasts. This ensures only realistic, informed decisions are modeled.")

            else:
                st.error("Optimization failed. Please check your parameters.")
            st.pyplot(plot_results(result_df))
            st.download_button("Download Results", result_df.to_csv().encode(), "results.csv")
