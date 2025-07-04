import numpy as np
import xarray as xr
import pymannkendall as mk  

def calculate_spatial_trend(dataset):
    """Calculate significant spatial trends (p < 0.05)"""
    da = dataset['tp']
    lat = da['lat'].values
    lon = da['lon'].values
    z = da.values

    slope = np.zeros(z.shape[1:])
    p_value = np.zeros(z.shape[1:])

    for ilat in range(z.shape[1]):
        for ilon in range(z.shape[2]):
            precip_series = z[:, ilat, ilon]
            
            if np.isnan(precip_series).all():
                slope[ilat, ilon] = np.nan
                p_value[ilat, ilon] = np.nan
            else:
                result = mk.original_test(precip_series)
                slope[ilat, ilon] = result.slope
                p_value[ilat, ilon] = result.p

    significant_trend = np.where(p_value <= 0.05, slope, np.nan)
    
    return xr.DataArray(
        significant_trend,
        dims=['lat', 'lon'],
        coords={'lat': lat, 'lon': lon},
        attrs={'description': 'Significant trends (p < 0.05)', 'units': 'mm/year'}
    )