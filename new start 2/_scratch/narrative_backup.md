# Sensor validation — thesis-style narrative

Calibration interval: ±1.96×RMSE (95% normal approximation, same as reference lux section).

## Tds (TDS (PPM))

Tds values were measured over a 7-minute window using TDS Sensor as the onboard sensor and TDS Meter as the reference meter in the NFADS node, as seen in Figure 12. The basic raw data generated showed that the MAE, RMSE and R² values were 31.67 PPM, 41.58 PPM and 0.9460 respectively. The graph has been plotted between sensor data, meter data and progressive RMSE value for a given time interval as shown in Figure 14a. On applying Ordinary Least Squares (OLS) linear regression model (Estimated TDS (PPM) = 0.8810 x (Raw Sensor Reading) + 52.8537), the calibration interval dropped from ±81.50 PPM to ±45.47 PPM.

## Water Temp (Nutrient Temperature (°C))

Nutrient temperature values were measured over a 10-minute window using Water Temperature Sensor as the onboard sensor and Temperature Meter as the reference meter in the NFADS node, as seen in Figure 13. The basic raw data generated showed that the MAE, RMSE and R² values were 0.68 °C, 0.68 °C and not applicable (low variance in reference) respectively. The graph has been plotted between sensor data, meter data and progressive RMSE value for a given time interval as shown in Figure 14b. On applying Ordinary Least Squares (OLS) linear regression model (Estimated Fluid Temperature (°C) = 0.0000 x (Raw Sensor Reading) + 30.8000), the calibration interval dropped from ±1.34 °C to ±0.00 °C.

## Ems Temp (Air Temperature (°C))

Air temperature values were measured over a 9-minute window using Environment Temperature Sensor as the onboard sensor and Temperature Meter as the reference meter in the EMS node, as seen in Figure 14. The basic raw data generated showed that the MAE, RMSE and R² values were 0.18 °C, 0.19 °C and -5.1754 respectively. The graph has been plotted between sensor data, meter data and progressive RMSE value for a given time interval as shown in Figure 16a. On applying Ordinary Least Squares (OLS) linear regression model (Estimated Air Temperature (°C) = 0.9215 x (Raw Sensor Reading) + 2.5556), the calibration interval dropped from ±0.36 °C to ±0.10 °C.

## Lux (Light Intensity (Lux))

Lux values were measured over a 12-hour daytime window using BH1750 as the lux sensor and TSL2591 as the lux meter in the LMS node, as seen in Figure 15. The basic raw data generated showed that the MAE, RMSE and R² values were 2207.98 Lux, 2660.56 Lux and 0.7842 respectively. The graph has been plotted between sensor data, meter data and progressive RMSE value for a given time interval as shown in Figure 17a. On applying Ordinary Least Squares (OLS) linear regression model (Estimated Light Intensity (Lux) = 0.7947 x (Raw Sensor Reading) - 143.7244), the calibration interval dropped from ±5214.69 Lux to ±235.18 Lux.
