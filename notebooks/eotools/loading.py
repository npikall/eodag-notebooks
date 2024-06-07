import datetime as dt
import xarray as xr
import os

def load_assets(root:str, res=60, only_spectral:bool=True, include_tci:bool=False):
    jp2_files = [file for dirs in os.walk(root, topdown=True)
                     for file in dirs[2] if file.endswith(f"_{res}m.jp2")]
    assets = [file.split('_')[2] for file in jp2_files if file.startswith('T')]

    if only_spectral and include_tci==False:
        assets = [a for a in assets if a[0]=='B']
    elif only_spectral and include_tci:
        assets = [a for a in assets if a[0] == 'B' or a[0] == 'T']
    else:
        pass
    
    return assets

def load_single_product(product, bands:list[str], params):
    loaded_data = {}
    for band in bands:
        # Load Band into an xarray Dataarray
        data = product.get_data(band=band, **params)

        # Get rid of Dimensions of size 1 [e.g.: shapes from (1,300,500) to (300,500)]
        data = data.squeeze()

        # Get time information from the product properties
        time_str = product.properties['startTimeFromAscendingNode']
        date = dt.datetime.strptime(time_str,'%Y-%m-%dT%H:%M:%S.%f%z')

        # Add a timestamp to the xarray dataarray (taken from product properties)
        data = data.expand_dims(dim={'time':[date.date()]})

        # Name the Dataarray (band name is used) -> Dataset uses the Dataarray name to name its variables
        data.name = band

        # Add Dataarray of a single band to the loaded_data dictionary
        loaded_data[band] = data
    # Create a xarray Dataset from a dictionary of Dataarrays
    ds = xr.Dataset(loaded_data)
    return ds

def load_multiple_timestamps(products, bands:list, *args, **kwargs):
    # Empty List where datasets are stored
    single_ds = []
    for product in products:
        # Load each dataarray and add to single_ds List
        single_product = load_single_product(product=product, bands=bands, *args, **kwargs)
        single_ds.append(single_product)
    # Merge datasets from List
    ds = xr.merge(single_ds)
    return ds


##############################################
# Regex functions
##############################################

def band_2_regex(band:str,res=60, **kwargs) -> str:
    if 'resolution' in kwargs and kwargs['resolution'] is not None:
        res = int(round(kwargs['resolution'] * 100_000, 0))
    return rf'^(?!.*MSK).*{band}_{res}m.*$'

def load_single_product_regex(product, bands:list[str], res=60, *args, **kwargs):
    loaded_data = {}
    for band in bands:
        regex = band_2_regex(band=band,res=res, **kwargs)
        # Load Band into an xarray Dataarray
        data = product.get_data(band=regex, **kwargs)

        # Get rid of Dimensions of size 1 [e.g.: shapes from (1,300,500) to (300,500)]
        data = data.squeeze()

        # Get time information from the product properties
        time_str = product.properties['startTimeFromAscendingNode']
        date = dt.datetime.strptime(time_str,'%Y-%m-%dT%H:%M:%S.%f%z')

        # Add a timestamp to the xarray dataarray (taken from product properties)
        data = data.expand_dims(dim={'time':[date.date()]})

        # Name the Dataarray (band name is used) -> Dataset uses the Dataarray name to name its variables
        data.name = band

        # Add Dataarray of a single band to the loaded_data dictionary
        loaded_data[band] = data
    # Create a xarray Dataset from a dictionary of Dataarrays
    ds = xr.Dataset(loaded_data)
    return ds

def load_multiple_timestamps_regex(products, bands:list, res,*args, **kwargs):
    # Empty List where datasets are stored
    single_ds = []
    for product in products:
        # Load each dataarray and add to single_ds List
        single_product = load_single_product_regex(product=product, bands=bands, res=res, *args, **kwargs)
        single_ds.append(single_product)
    # Merge datasets from List
    ds = xr.merge(single_ds)
    return ds

def get_data_regex(product, band:str,res:int, **kwargs):
    regex = band_2_regex(band, res=res)
    return product.get_data(band=regex, **kwargs)