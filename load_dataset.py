import xarray as xr
import geopandas as gpd
from shapely.geometry import mapping
import numpy as np
import pandas as pd
from datetime import datetime

def preprocess():
    # Load original dataset
    ds = xr.open_dataset("Dataset/chirps_data/chirps_nepal_merged.nc")
    
    # Rename variables if they exist
    try:
        ds = ds.rename({'latitude': 'lat', 'longitude': 'lon', 'precip': 'tp'})
    except ValueError:
        pass  # Skip if these variables are already renamed
    
    # Remove problematic attributes if present
    ds.attrs.pop('_FillValue', None)
    ds.attrs.pop('missing_value', None)
    
    # Define encoding to handle fill values properly
    encoding = {'tp': {'_FillValue': -99.9, 'missing_value': -99.9}}

    # Write to NetCDF with the correct extension
    output_path = "Dataset/encoded_chirps.nc"
    ds.to_netcdf(output_path, encoding=encoding)
    
    # Load the newly saved NetCDF file
    pre_processed_ds = xr.open_dataset(output_path)
    
    # Drop all fill values (-99.9) from the 'tp' variable
    pre_processed_ds = pre_processed_ds.where(pre_processed_ds.tp != -99.9, drop=True)

    return pre_processed_ds

def process(dataset):
    dataset= dataset
    shp= gpd.read_file('Shapefile/Nepal_bnd_WGS84.shp')

    dataset=dataset.rio.write_crs("EPSG:4326")
    shp=shp.to_crs(dataset.rio.crs)

    dataset=dataset.rio.clip(shp.geometry.apply(mapping), shp.crs,drop= True)

    daily_dataset= dataset.copy()
    monthly_dataset= dataset.resample(time='1ME').sum(dim=['time'], skipna= True)
    yearly_dataset= dataset.resample(time='1YE').sum(dim=["time"],skipna= True)

    dataframe=dataset.mean(dim=['lat','lon'], skipna=True).to_dataframe().reset_index()
    dataframe['year']= dataframe['time'].dt.year
    dataframe['month']= dataframe['time'].dt.month
    dataframe['day']= dataframe['time'].dt.day

    min_year= dataframe['year'].min()
    max_year= dataframe['year'].max()

    min_date= dataframe['time'].min()
    max_date= dataframe['time'].max()

    return shp, daily_dataset, monthly_dataset, yearly_dataset, dataframe, min_year, max_year, min_date, max_date


####LOADING MAIN DATASET####

def load_main_dataset():
    pre_processed= preprocess()
    return process(pre_processed)

shp, daily_dataset, monthly_dataset, yearly_dataset, dataframe, min_year, max_year, min_date, max_date = load_main_dataset()




###FOR HYDROLOGICAL YEAR##

def seasonal_calculation(dataset):
    month = dataset['time'].dt.month
    year = dataset['time'].dt.year
    day = dataset['time'].dt.day

    season_year = xr.DataArray(
        np.where(month==12, year+1, year),
        coords={'time': dataset['time']},
        dims=['time']
    )

    seasonal_date = xr.DataArray(
        [f"{y}-{m:02d}-{d:02d}" for y,m,d in zip(season_year.values, month.values, day.values)],
        coords={'time': dataset['time']},
        dims=['time']
    )
    
    seasonal_date = pd.to_datetime(seasonal_date, format="%Y-%m-%d")

    array = xr.DataArray(
        seasonal_date,
        coords={'time': dataset['time']},
        dims=['time']
    )

    return dataset.assign_coords(time=array)

def load_hydrological_year_dataset():
    # Step 1: Load and preprocess
    pre_processed = preprocess()
    
    # Step 2: Apply seasonal adjustment (Dec → next year)
    dataset = seasonal_calculation(pre_processed)
    
    # Step 3: Remove "fake future" years
    current_year = datetime.now().year
    dataset = dataset.where(dataset['time.year'] <= current_year, drop=True)
    
    # Step 4: Sort by time
    dataset = dataset.sortby('time')
    
    return process(dataset)

shp, seasonal_daily_dataset, seasonal_monthly_dataset, seasonal_yearly_dataset, seasonal_dataframe, seasonal_min_year, seasonal_max_year, seasonal_min_date, seasonal_max_date = load_hydrological_year_dataset()