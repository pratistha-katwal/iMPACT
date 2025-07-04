import xarray as xr
import requests
from datetime import datetime, timedelta
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
DATA_DIR = Path("Dataset/chirps_data")
RAW_DATA_DIR = DATA_DIR / "raw_yearly"  # Folder for yearly downloads
MERGED_FILE = DATA_DIR / "chirps_nepal_merged.nc"  # Single merged output file

# Nepal bounding box
NEPAL_BBOX = {
    'lon_min': 79,
    'lon_max': 89,
    'lat_min': 26, 
    'lat_max': 31
}

def download_chirps():
    """Download and process CHIRPS data into a single merged Nepal dataset"""
    try:
        # Create directories if needed
        DATA_DIR.mkdir(exist_ok=True)
        RAW_DATA_DIR.mkdir(exist_ok=True)

        current_year = datetime.now().year
        base_url = "https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_daily/netcdf/p05/"

        # Determine which years we need to download
        existing_years = get_existing_years()
        years_to_download = determine_years_to_download(existing_years, current_year)

        # Download missing/updated yearly files
        download_yearly_files(base_url, years_to_download)

        # Merge all files with Nepal subset
        create_merged_dataset()

        logger.info(f"Successfully created merged dataset: {MERGED_FILE}")

    except Exception as e:
        logger.error(f"Error in processing: {str(e)}", exc_info=True)
        raise

def get_existing_years():
    """Check which yearly files we already have"""
    return {int(f.stem.split('_')[-1]) for f in RAW_DATA_DIR.glob("chirps_*.nc")}

def determine_years_to_download(existing_years, current_year):
    """Determine which years need to be downloaded"""
    # CHIRPS data starts from 1981
    all_years = set(range(2024, current_year + 1))
    return sorted(all_years - existing_years)

def download_yearly_files(base_url, years):
    """Download specified yearly files"""
    for year in years:
        url = f"{base_url}chirps-v2.0.{year}.days_p05.nc"
        local_file = RAW_DATA_DIR / f"chirps_{year}.nc"
        
        try:
            logger.info(f"Downloading {year} data...")
            with requests.get(url, stream=True, timeout=30) as r:
                r.raise_for_status()
                with open(local_file, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            logger.info(f"Downloaded {year} data")
        except requests.RequestException as e:
            logger.error(f"Failed to download {year}: {str(e)}")
            continue

def create_merged_dataset():
    """Merge all yearly files with Nepal subset"""
    nc_files = sorted(RAW_DATA_DIR.glob("chirps_*.nc"))
    if not nc_files:
        raise ValueError("No yearly files found to merge")

    logger.info("Merging datasets with Nepal subset...")
    
    # Open all files and subset for Nepal
    with xr.open_mfdataset(nc_files, combine='by_coords') as ds:
        ds = ds.chunk({'time': 365})
        ds_nepal = ds.sel(
            longitude=slice(NEPAL_BBOX['lon_min'], NEPAL_BBOX['lon_max']),
            latitude=slice(NEPAL_BBOX['lat_min'], NEPAL_BBOX['lat_max'])  # Reversed for north-south
        )
        

        ds_nepal.to_netcdf(MERGED_FILE)

if __name__ == "__main__":
    download_chirps()