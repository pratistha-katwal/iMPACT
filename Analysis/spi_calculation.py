import xarray as xr
import numpy as np
from climate_indices import indices, compute
from functools import partial

def calculate_spi_with_ufunc(monthly_ds, scale):
    # Extract time information
    time_coords = monthly_ds.time
    start_year = int(time_coords.dt.year[0])
    end_year = int(time_coords.dt.year[-1])
    
    # Define the core SPI calculation function
    def _spi_core(precip_series, scale, start_year, end_year):
        if np.isnan(precip_series).all():
            return np.full_like(precip_series, np.nan)
        
        try:
            return np.ma.filled(
                indices.spi(
                    precip_series,
                    scale=scale,
                    distribution=indices.Distribution.gamma,
                    periodicity=compute.Periodicity.monthly,
                    data_start_year=start_year,
                    calibration_year_initial=start_year,
                    calibration_year_final=end_year
                ),
                np.nan
            )
        except Exception as e:
            print(f"SPI calculation error: {str(e)}")
            return np.full_like(precip_series, np.nan)
    
    # Use apply_ufunc for parallel computation
    spi_array = xr.apply_ufunc(
        partial(_spi_core, scale=scale, start_year=start_year, end_year=end_year),
        monthly_ds['tp'],
        input_core_dims=[['time']],
        output_core_dims=[['time']],
        vectorize=True,
        dask='parallelized',
        output_dtypes=[np.float64],
        keep_attrs=True
    )
    
    return spi_array.transpose('time', 'lat', 'lon').rename('SPI')
