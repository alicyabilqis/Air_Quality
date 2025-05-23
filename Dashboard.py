# Import dataset
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import plotly.graph_objects as go
import plotly.express as px

# Load dataset
data_name = 'air_quality.csv'
air_quality = pd.read_csv(data_name)

# Filter data for years 2014–2016 only
air_quality = air_quality[(air_quality['year'] >= 2014) & (air_quality['year'] <= 2016)]

# Interpolate missing values for selected columns
columns = ['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3', 'TEMP', 'PRES', 'DEWP', 'RAIN', 'WSPM']
for col in columns:
    air_quality[col] = air_quality[col].interpolate(method='linear', limit_direction='both')

# Convert wind direction to degrees
wind_direction_map = {
    'N': 0, 'NNE': 22.5, 'NE': 45, 'ENE': 67.5,
    'E': 90, 'ESE': 112.5, 'SE': 135, 'SSE': 157.5,
    'S': 180, 'SSW': 202.5, 'SW': 225, 'WSW': 247.5,
    'W': 270, 'WNW': 292.5, 'NW': 315, 'NNW': 337.5
}
air_quality['wd_deg'] = air_quality['wd'].map(wind_direction_map)
air_quality['wd_deg'] = air_quality['wd_deg'].interpolate(method='linear', limit_direction='both')

# Create complete datetime column and a date-only column
air_quality['datetime'] = pd.to_datetime(air_quality[['year', 'month', 'day', 'hour']])
air_quality['date'] = air_quality['datetime'].dt.normalize()

# AQI breakpoints for each pollutant
pm25_breakpoints = [
    (0.0, 12.0, 0, 50), (12.1, 35.4, 51, 100), (35.5, 55.4, 101, 150),
    (55.5, 150.4, 151, 200), (150.5, 250.4, 201, 300), (250.5, 500.4, 301, 500)
]
pm10_breakpoints = [
    (0, 54, 0, 50), (55, 154, 51, 100), (155, 254, 101, 150),
    (255, 354, 151, 200), (355, 424, 201, 300), (425, 604, 301, 500)
]
so2_breakpoints = [
    (0, 35, 0, 50), (36, 75, 51, 100), (76, 185, 101, 150),
    (186, 304, 151, 200), (305, 604, 201, 300), (605, 1004, 301, 500)
]
no2_breakpoints = [
    (0, 53, 0, 50), (54, 100, 51, 100), (101, 360, 101, 150),
    (361, 649, 151, 200), (650, 1249, 201, 300), (1250, 2049, 301, 500)
]
co_breakpoints = [
    (0.0, 4.4, 0, 50), (4.5, 9.4, 51, 100), (9.5, 12.4, 101, 150),
    (12.5, 15.4, 151, 200), (15.5, 30.4, 201, 300), (30.5, 50.4, 301, 500)
]
o3_breakpoints = [
    (0, 54, 0, 50), (55, 70, 51, 100), (71, 85, 101, 150),
    (86, 105, 151, 200), (106, 200, 201, 300), (201, 404, 301, 500)
]

# AQI calculation function
def calculate_aqi(concentration, breakpoints):
    for C_lo, C_hi, I_lo, I_hi in breakpoints:
        if C_lo <= concentration <= C_hi:
            return round(((I_hi - I_lo) / (C_hi - C_lo)) * (concentration - C_lo) + I_lo)
    return None

# Apply AQI calculation
air_quality['AQI_PM25'] = air_quality['PM2.5'].apply(lambda x: calculate_aqi(x, pm25_breakpoints))
air_quality['AQI_PM10'] = air_quality['PM10'].apply(lambda x: calculate_aqi(x, pm10_breakpoints))
air_quality['AQI_SO2']  = air_quality['SO2'].apply(lambda x: calculate_aqi(x, so2_breakpoints))
air_quality['AQI_NO2']  = air_quality['NO2'].apply(lambda x: calculate_aqi(x, no2_breakpoints))
air_quality['AQI_CO']   = air_quality['CO'].apply(lambda x: calculate_aqi(x, co_breakpoints))
air_quality['AQI_O3']   = air_quality['O3'].apply(lambda x: calculate_aqi(x, o3_breakpoints))

# Final AQI is the highest among all pollutants
air_quality['AQI'] = air_quality[['AQI_PM25', 'AQI_PM10', 'AQI_SO2', 'AQI_NO2', 'AQI_CO', 'AQI_O3']].max(axis=1)

# Define AQI category labels
def aqi_category(aqi):
    if pd.isna(aqi):
        return 'Unknown'
    elif aqi <= 50:
        return 'Good'
    elif aqi <= 100:
        return 'Moderate'
    elif aqi <= 150:
        return 'Unhealthy for Sensitive Groups'
    elif aqi <= 200:
        return 'Unhealthy'
    elif aqi <= 300:
        return 'Very Unhealthy'
    else:
        return 'Hazardous'

air_quality['AQI_Category'] = air_quality['AQI'].apply(aqi_category)

monthly_avg = air_quality.groupby(['year', 'month'])[['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3']].mean().reset_index()

colors = ['#E60026', '#F39800', '#FFF100', '#009944', '#0068B7', '#1D2088']

##['#023e8a', '#2a6f9c', '#5c9bb1', '#98c3c8', '#b0bcc1', '#888f94']
##['#1E90FF', '#FFA500', '#32CD32', '#FF69B4', '#FFD700', '#8A2BE2']

# 🔹🔹 Streamlit App
st.title('Comprehensive Assessment of Air Quality at Aotizhongxin Monitoring Station')
st.write("### Explore Pollutant Data")

# 🔹 Set date selector range based on filtered years
selected_date = st.date_input(
    "Select a Date",
    value=pd.to_datetime('2014-01-01').date(),
    min_value=pd.to_datetime('2014-01-01').date(),
    max_value=pd.to_datetime('2016-12-31').date()
)

# Convert selected date to full timestamp
selected_date_ts = pd.to_datetime(selected_date)

# Filter data for the selected date
filtered = air_quality[air_quality['date'] == selected_date_ts]

# 🔹 Display summary metrics for each pollutant
pollutants = ['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3']
st.write("### Pollutant Summary Metrics")

for pol in pollutants:
    if filtered[pol].dropna().empty:
        st.warning(f"No valid data for {pol} on this date.")
        continue

    max_val = filtered[pol].max()
    max_hour = int(filtered.loc[filtered[pol].idxmax(), 'hour'])
    min_val = filtered[pol].min()
    min_hour = int(filtered.loc[filtered[pol].idxmin(), 'hour'])
    avg_val = filtered[pol].mean()

    st.markdown(f"#### {pol}")
    col0, col1, col2, col3, col4, col5, col6 = st.columns(7)
    col1.metric(f"Max {pol}", f"{max_val:.2f}")
    col2.write(f"At hour {max_hour}")
    col3.metric(f"Min {pol}", f"{min_val:.2f}")
    col4.write(f"At hour {min_hour}")
    col5.metric(f"Average {pol}", f"{avg_val:.2f}")
    col6.write("")  # Placeholder for spacing

# 🔹 Display hourly averages for each pollutant
st.write("### Hourly Averages")

# Calculate hourly averages for selected date
df_hourly_avg_all = filtered.groupby('hour')[pollutants].mean().round(2).reset_index()
df_hourly_avg_all = df_hourly_avg_all.set_index('hour')

# Initialize the figure
fig_pollutants = go.Figure()

# Stacked area trace
for i, pol in enumerate(df_hourly_avg_all.columns):
    fig_pollutants.add_trace(go.Scatter(
        x=df_hourly_avg_all.index,
        y=df_hourly_avg_all[pol],
        mode='lines',
        name=pol,
        stackgroup='one',
        line=dict(width=0.5, color=colors[i % len(colors)])
    ))

# layout
fig_pollutants.update_layout(
    xaxis=dict(
        title='Hour',
        tickmode='linear',  # ticks linear mode
        dtick=1,  # Tick interval 1 hour
        range=[0, 23],
        tickangle=0,  # labels horizontal
        tickfont=dict(size=10)
    ),
    yaxis=dict(
        title='Concentration (µg/m³)',
        rangemode='tozero' ##
    ),
    template='plotly_white',
    hovermode='x unified',
    margin=dict(b=80)  # bottom margin
)

# Display
st.plotly_chart(fig_pollutants, use_container_width=True)

# 🔹 Display wind direction per hour
st.write("### Hourly Wind Direction")

# Description
directions = [
    ("N", "North"), ("NNE", "North-Northeast"), ("NE", "Northeast"), ("ENE", "East-Northeast"),
    ("E", "East"), ("ESE", "East-Southeast"), ("SE", "Southeast"), ("SSE", "South-Southeast"),
    ("S", "South"), ("SSW", "South-Southwest"), ("SW", "Southwest"), ("WSW", "West-Southwest"),
    ("W", "West"), ("WNW", "West-Northwest"), ("NW", "Northwest"), ("NNW", "North-Northwest"),
]

cols = st.columns(4)
for i, col in enumerate(cols):
    with col:
        for j in range(4):
            idx = i * 4 + j
            dir_short, dir_full = directions[idx]
            col.caption(f"{dir_short} - {dir_full}")

# Extract hour and wind direction, sort by hour
df_wd_only = filtered[['hour', 'wd']].dropna().sort_values('hour')

# Transpose
wind_direction_row = df_wd_only.set_index('hour')['wd'].T
df_wd_only.columns = ['Hour', 'Wind Direction'] # rename
wind_direction_table = pd.DataFrame(wind_direction_row).T

# Display
st.dataframe(wind_direction_table, use_container_width=True)

# 🔹 Monthly Average Pollutant Concentrations
st.write('### Monthly Average')

# select pollutant
pollutants = ['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3']
selected_pollutant = st.selectbox("Select pollutant to display", pollutants)

# Filter data for the selected pollutant
data_plot = monthly_avg[['year', 'month', selected_pollutant]]

# Create a combined year-month column for the x-axis (optional, for clarity)
data_plot['Year-Month'] = data_plot.apply(lambda row: f"{int(row['year'])}-{int(row['month']):02d}", axis=1)

# Plot monthly average lines per year
show_by_year = st.checkbox("Show separate lines by year", value=True) # combine all years or show separately per year

if show_by_year:
    fig = px.line(data_plot, x='month', y=selected_pollutant, color='year',
                  labels={'month': 'Month', selected_pollutant: 'Concentration', 'year': 'Year'},
                  title=f"Monthly Average Concentration of {selected_pollutant} by Year (2014-2016)")
else:
    # If not by year, calculate the overall average per month across all years
    avg_per_month = data_plot.groupby('month')[selected_pollutant].mean().reset_index()
    fig = px.line(avg_per_month, x='month', y=selected_pollutant,
                  labels={'month': 'Month', selected_pollutant: 'Concentration'},
                  title=f"Overall Monthly Average Concentration of {selected_pollutant} (2014-2016 Combined)")

# Display
fig.update_layout(xaxis=dict(tickmode='linear', dtick=1))
st.plotly_chart(fig, use_container_width=True)

# 🔹 Show AQI summary
st.write("### Air Quality Index (AQI)")
aqi_values = filtered['AQI']
aqi_category_values = filtered['AQI_Category']
if not aqi_values.empty:
    max_aqi = aqi_values.max()
    avg_aqi = aqi_values.mean()
    category = aqi_category(max_aqi)

    col1, col2 = st.columns(2)
    col1.metric("Max AQI", f"{max_aqi:.0f}", category)
    col2.metric("Average AQI", f"{avg_aqi:.0f}")
else:
    st.warning("AQI data is not available for the selected date.")

# 🔹 Display Correlation of Meteorological Variables and Pollutants Correlation
st.write("### Meteorological Impacts on Concentrations of Pollutant")

# Define
pollutant_gases = ['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3']
meteorological_vars = ['TEMP', 'DEWP', 'WSPM']

# correlation matrix
correlation_matrix = air_quality[pollutant_gases + meteorological_vars].corr()
corr_df = correlation_matrix.loc[meteorological_vars, pollutant_gases].reset_index().melt(id_vars='index')
corr_df.columns = ['Meteorology', 'Pollutant', 'Correlation']

# Create bubble chart
fig = px.scatter(
    corr_df,
    x='Pollutant',
    y='Meteorology',
    size=corr_df['Correlation'].abs(),       # Bubble size based on absolute correlation
    color='Correlation',                     # Bubble color based on actual correlation value
    color_continuous_scale='RdBu',
    range_color=[-1, 1],
    text=corr_df['Correlation'].round(2),    # Show correlation values inside bubbles
    size_max=40,
)

# Layout styling
fig.update_layout(
    xaxis=dict(
        title='Pollutant',
        tickfont=dict(size=11)
    ),
    yaxis=dict(
        title='Meteorological Variable',
        tickfont=dict(size=11)
    ),
    template='plotly_white',
    hovermode='closest',
    margin=dict(t=50, b=80)
)

# Add labels inside bubbles
fig.update_traces(
    textposition='middle center',
    marker=dict(line=dict(width=0)),
    textfont=dict(color='black', family='Arial')
)

# Display
st.plotly_chart(fig, use_container_width=True)

# Description
meteorology_desc = [("TEMP", "Temperature (°C)"),("DEWP", "Dew Point (°C)"),("WSPM", "Wind Speed (m/s)")
]

cols = st.columns(3)
for i, col in enumerate(cols):
    var_short, var_full = meteorology_desc[i]
    col.caption(f"**{var_short}** – {var_full}")

# 🔹 Display Correlation between Wind Direction and Pollutant Concentrations
st.write("### Correlation Between Wind Direction Shifts and Pollutant Concentrations")

# Convert wind direction from degrees to radians
air_quality['wd_rad'] = np.deg2rad(air_quality['wd_deg'])

# Calculate average sin and cosin of wind direction
wind_grouped = air_quality.groupby('hour')['wd_rad']
mean_sin = wind_grouped.apply(lambda x: np.sin(x).mean())
mean_cos = wind_grouped.apply(lambda x: np.cos(x).mean())

# Compute average wind direction in radians and then convert back to degrees
mean_wd_rad = np.arctan2(mean_sin, mean_cos)
mean_wd_deg = (np.rad2deg(mean_wd_rad)) % 360
mean_wd_deg = mean_wd_deg.rename('Wind Direction (°)')

# Calculate average pollutant concentrations by hour
pollutants_per_hour = air_quality.groupby('hour')[['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3']].mean()

# Combine data
combined_data = pd.concat([mean_wd_deg, pollutants_per_hour], axis=1).reset_index()

# Calculate correlation matrix
corr_matrix = combined_data[['Wind Direction (°)', 'PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3']].corr()
corr_wind_pollutants = corr_matrix.loc['Wind Direction (°)', ['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3']]# Extract correlations

# DataFrame
corr_df = pd.DataFrame({
    'Pollutant': corr_wind_pollutants.index,
    'Correlation': corr_wind_pollutants.values
})
corr_df['Meteorological Variable'] = 'Wind Direction (°)'

# Create bubble chart
fig = px.scatter(
    corr_df,
    x='Pollutant',
    y='Meteorological Variable',
    size=corr_df['Correlation'].abs(),
    color='Correlation',
    color_continuous_scale='RdBu',
    range_color=[-1, 1],
    text=corr_df['Correlation'].round(2),
    size_max=40,
)

fig.update_layout(
    xaxis_title='Pollutant',
    template='plotly_white',
    margin=dict(t=50, b=80),
    hovermode='closest',
)

fig.update_traces(
    textposition='middle center',
    marker=dict(line=dict(width=0)),
    textfont=dict(color='black', family='Arial')
)

# Display
st.plotly_chart(fig, use_container_width=True)
