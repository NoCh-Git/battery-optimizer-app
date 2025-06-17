
import pandas as pd
import cvxpy as cp
import numpy as np
#import time

def rolling_optimize_battery(df, capacity, max_power, eff, grid_fee, degradation_cost):
    """
    Rolling optimization with realistic day-ahead price visibility:
    - Before ~13:00 each day, only current day's prices (until 23:00) are known.
    - After ~13:00, both today and tomorrow's prices are known (full 48h horizon).
    
     Parameters:
        df (pd.DataFrame): DataFrame with a column 'Price_EUR_per_kWh' indexed by hourly timestamps
        capacity (float): Battery energy capacity in kWh
        max_power (float): Max charge/discharge power in kW
        eff (float): Round-trip efficiency's square root (0 < eff ≤ 1)
        grid_fee (float): Grid import cost per kWh
        degradation_cost (float): Degradation cost per kWh of throughput [in future iterations can be influenced by the number of cycles, and estimated lifetime]

    
    Returns:
        pd.DataFrame: Original df with added columns for charge, discharge, and SoC
    
    """
    #start_time = time.time()  # 🕒 Start timing

    soc = 0.5 * capacity  # Start at 50% SoC
    soc_history = []
    charge_history = []
    discharge_history = []

    df = df.copy()
    prices = df["Price_EUR_per_kWh"].values
    T = len(df)

    for t in range(0, T - 12): # Spannig the whole hours of our year except the last 12 hours.
        current_hour = t % 24 # Here we are assuming the CSV data starts with midnight, it's practically correct but we should maybe check if there is another data source used in the future.
        
        day_hour = current_hour
        remaining_today = 24 - day_hour

        # If it's before 13:00 → tomorrow's prices not yet known based on the current system.
        if day_hour < 13:
            forecast_horizon = remaining_today
        else:
            # After 13:00, both today's remaining hours and all of tomorrow are known.
            # So the forecast horizon is: (24 - current hour) today + 24h tomorrow = (48 - current_hour) [in practice the longest forecast horizon is 35h]
            # We also cap it at T - t to avoid exceeding the end of the dataset.
            forecast_horizon = min((48 - current_hour), T - t)

        # Debugging output
        #print(f"Processing hour {forecast_horizon} (Hour of day: {day_hour})")

        p_window = prices[t:t + forecast_horizon]

        # ⚠️ Ensure price window matches forecast horizon
        if len(p_window) != forecast_horizon:
            print(f"❌ Skipping hour {t} — insufficient price data: got {len(p_window)}h, expected {forecast_horizon}h")
            continue  # Skip this hour and move on to the next one

        charge = cp.Variable(forecast_horizon, nonneg=True)
        discharge = cp.Variable(forecast_horizon, nonneg=True)
        soc_vars = cp.Variable(forecast_horizon + 1)
        
        # Battery operation constraints for each hour in the forecast window
        # - soc_vars[0] == soc: Initialize state of charge with current SoC value.
        # - For each hour `i`:
        #     • Charging and discharging must not exceed the max power limit.
        #     • Update SoC based on charging/discharging and round-trip efficiency:
        #         SoC(i+1) = SoC(i) + (charge * efficiency) - (discharge / efficiency)
        #     • SoC must remain non-negative and within battery capacity.


        constraints = [soc_vars[0] == soc]
        for i in range(forecast_horizon):
            constraints += [
                charge[i] <= max_power,
                discharge[i] <= max_power,
                soc_vars[i + 1] == soc_vars[i] + charge[i] * eff - discharge[i] / eff,
                soc_vars[i + 1] >= 0,
                soc_vars[i + 1] <= capacity,
            ]
        # Print the shape of discharge and p_window:
        #print(f"Discharge shape: {discharge.shape}, p_window shape: {p_window.shape}")
        revenue = cp.sum(cp.multiply(discharge, p_window))
        cost = cp.sum(cp.multiply(charge, p_window + grid_fee))
        degradation = cp.sum(charge + discharge) * degradation_cost
        profit = revenue - cost - degradation

        problem = cp.Problem(cp.Maximize(profit), constraints)
        problem.solve(solver=cp.SCS)

        charge_val = charge.value[0]
        discharge_val = discharge.value[0]
        soc_val = soc_vars.value[1]

        charge_history.append(charge_val)
        discharge_history.append(discharge_val)
        soc = soc_val
        soc_history.append(soc)

    df = df.iloc[:len(charge_history)].copy()
    df["charge_kWh"] = charge_history
    df["discharge_kWh"] = discharge_history
    df["SoC_kWh"] = soc_history


    # Calculate total profit:
    charge_arr = np.array(charge_history)
    discharge_arr = np.array(discharge_history)
    price_arr = df["Price_EUR_per_kWh"].values

    total_profit = (
        discharge_arr.dot(price_arr) -
        charge_arr.dot(price_arr + grid_fee) -
        degradation_cost * (charge_arr + discharge_arr).sum()
    )

    #elapsed_time = time.time() - start_time  # 🕒 Measure time
    #print(f"\n Optimization completed in {elapsed_time:.2f} seconds.")
    return df, total_profit
