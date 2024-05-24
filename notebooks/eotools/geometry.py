import rioxarray
import xarray as xr
import numpy as np
import geopandas as gpd
from shapely.geometry import mapping
from sklearn.model_selection import train_test_split


def clip_dataset_2_shapefile(ds, shapefile):
    clip_shape = gpd.read_file(shapefile)
    ds = ds.rio.clip(clip_shape.geometry.apply(mapping), clip_shape.crs, drop=False, invert=False)
    return ds

def geojson_to_polygon(path:str) -> list:
    '''
    Reads a geojson File and returns a List of Polygons 

    Params:
        - ``path``: Filepath to Geojson

    Returns: 
        - ``polygons``: List of Polygons
    '''
    gdf = gpd.read_file(path)
    polygons = [feature for feature in gdf.geometry]
    return polygons

def geojson_to_polygon_dict(path:str) -> dict:
    '''
    Uses the Path of a Geojson File to extract the polygons and puts them into a Dictionary.

    Params: 
        - ``path``: Filepath to Geojson

    Returns: 
        - ``polygons_dict``
    '''
    polygons = geojson_to_polygon(path)
    polygons_dict = {idx: [polygon] for idx, polygon in enumerate(polygons)}
    return polygons_dict

def clip_array(ds:xr.Dataset, polygons):
    '''
    Takes an xarray.Dataset and a geometry and returns the xarray.Dataset, which has been spatialy clipped
    to the geometry.

    Params:
        - ``ds``: xarray.Dataset
        - ``polygons``: shapely.geometry
    
    Returns:
        - ``clipped_nan``: clipped dataset where values outside of polygons have Nan type
    '''
    clipped = ds.rio.clip(polygons, invert=False, all_touched=False, drop=True)
    clipped_nan = clipped.where(clipped == ds)
    return clipped_nan

def preprocess_data_to_classify(ds:xr.Dataset, feature_path:str, nonfeature_path:str, bands:list=None) -> list:
    '''
    Takes an xarray Dataset, two geojson files (one of areas with the desired feature, the other not with the feature)
    and a list of strings of the desired Bandnames in the Dataset and returns The Training and Test data for some Classifikators.

    Params:
        - ``ds``: xarray.Dataset
        - ``feature_path``: Filepath to Geojson with Polygons, which represent the Feature (e.g.: forested Areas)
        - ``nonfeature_path``: Filepath to Geojson, which does not have the feature (e.g.: not forested Areas)
        - ``bands`` (optional): List of Strings of desired Spectral Bands (e.g.: bands=['B02', 'B03', 'B04', 'B08'])
                                If None, then takes all in the Dataset.

    Returns:
        -  ``X_train, X_test, y_train, y_test``; Training and Test Split for scikit.learn Classificators
    '''
    # List all Bands which are loaded as Variables into the Dataset
    if bands == None:
        bands = list(ds.data_vars)

    # Geojsons from Features to Polygons
    polygons_feat = geojson_to_polygon_dict(feature_path)
    polygons_nonfeat = geojson_to_polygon_dict(nonfeature_path)

    # Dictionaries with Dataarrays, each clipped by a Polygon
    data_dict_feat = {idx: clip_array(ds, polygon) for idx, polygon in polygons_feat.items()}
    data_dict_nonfeat = {idx: clip_array(ds, polygon)  for idx, polygon in polygons_nonfeat.items()}

    # Median over time to get rid of outliers
    median_data_dict_feat = {idx: xarray.median(dim='time', skipna=True) for idx, xarray in data_dict_feat.items()}
    median_data_dict_nonfeat = {idx: xarray.median(dim='time', skipna=True) for idx, xarray in data_dict_nonfeat.items()}

    # Reshape the polygon dataarrays to get a tuple (one value per band) of pixel values
    feat_data = [xarray.to_array().values.reshape(len(bands),-1).T for xarray in median_data_dict_feat.values()]
    nonfeat_data = [xarray.to_array().values.reshape(len(bands),-1).T for xarray in median_data_dict_nonfeat.values()]

    # The rows of the different polygons are concatenated to a single array for further processing
    feat_values = np.concatenate(feat_data)
    nonfeat_values = np.concatenate(nonfeat_data)

    # Drop Nan Values
    X_feat_data = feat_values[~np.isnan(feat_values).any(axis=1)]
    X_nonfeat_data = nonfeat_values[~np.isnan(nonfeat_values).any(axis=1)]

    # Creating Output Vector (1 for pixel is features; 0 for pixel is not feature)
    y_feat_data = np.ones(X_feat_data.shape[0])
    y_nonfeat_data = np.zeros(X_nonfeat_data.shape[0])
    
    # Concatnate all Classes for training 
    X = np.concatenate([X_feat_data, X_nonfeat_data])
    y = np.concatenate([y_feat_data, y_nonfeat_data])

    # Split into Training and Testing Data.
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.5, random_state=42)

    return X_train, X_test, y_train, y_test