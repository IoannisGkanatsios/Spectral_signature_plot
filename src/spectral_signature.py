import rasterio
import numpy as np

import geopandas as gpd
from shapely import geometry
import rasterstats

import matplotlib.pylab as plt
from seaborn import set_style
import seaborn as sns
sns.set()
# remove grid
sns.set_style("ticks")


def load_data(path):
    with rasterio.open(path) as src:
        s2 = src.read()
        profile = src.profile
        return s2, profile


def point_to_dataframe(coords, profile):
    p = geometry.Point(coords)
    point = gpd.GeoDataFrame({'geometry': [(p)]}, index=[
                             0], crs=profile['crs'])
    return point


def extract_value(point, path, spectra):
    point_location = []
    point_location_percent = []
    for i, loc in enumerate(spectra):
        count = i+1
        extract_val_loc = rasterstats.zonal_stats(point,
                                                  path,
                                                  nodata=-999,
                                                  band=count,
                                                  raster_out=True
                                                  )
        s2_reflect = np.divide(extract_val_loc[0]['mini_raster_array'], 10000)
        # get reflectance values in percentages
        reflectance_loc_percent = s2_reflect * 100
        point_location.append(s2_reflect)
        point_location_percent.append(reflectance_loc_percent)
    return point_location, point_location_percent


def spectral_signature_plot(data_path, coords,  label='spectral signature'):
    s2, profile = load_data(data_path)

    # SENTINEL-2 spectral bands
    aerosol = s2[0, :, :]
    blue = s2[1, :, :]
    green = s2[2, :, :]
    red = s2[3, :, :]
    veg_red_edge = s2[4, :, :]
    veg_red_edge1 = s2[5, :, :]
    veg_red_edge2 = s2[6, :, :]
    nir = s2[7, :, :]
    narrow_nir = s2[8, :, :]
    water_vap = s2[9, :, :]
    swir = s2[10, :, :]
    swir2 = s2[11, :, :]

    # SENTINEL-2 bandwidth (https://sentinel.esa.int/web/sentinel/user-guides/sentinel-2-msi/resolutions/radiometric)
    B1_nm = 21
    B2_nm = 66
    B3_nm = 36
    B4_nm = 31
    B5_nm = 15
    B6_nm = 15
    B7_nm = 20
    B8_nm = 115
    B8a_nm = 20
    B9_nm = 20
    B11_nm = 90
    B12_nm = 180

    wavelengths = np.array(
        [443, 490, 560, 665, 705, 740, 783, 842, 865, 945, 1610, 2190])
    spectra = [aerosol, blue, green, red, veg_red_edge, veg_red_edge1, veg_red_edge2, nir,
               narrow_nir, water_vap, swir, swir2]

    # Set up the bandwidth for each spectral band
    B1 = (wavelengths[0], wavelengths[0] + B1_nm)
    B2 = (wavelengths[1], wavelengths[1] + B2_nm)
    B3 = (wavelengths[2], wavelengths[2] + B3_nm)
    B4 = (wavelengths[3], wavelengths[3] + B4_nm)
    B5 = (wavelengths[4], wavelengths[4] + B5_nm)
    B6 = (wavelengths[5], wavelengths[5] + B6_nm)
    B7 = (wavelengths[6], wavelengths[6] + B7_nm)
    B8 = (wavelengths[7], wavelengths[7] + B8_nm)
    B8a = (wavelengths[8], wavelengths[8] + B8a_nm)
    B9 = (wavelengths[9], wavelengths[9] + B9_nm)
    B11 = (wavelengths[10], wavelengths[10] + B11_nm)
    B12 = (wavelengths[11], wavelengths[11] + B12_nm)

    # Extract the piel value for each spectral band based on the coordinates
    p = point_to_dataframe(coords, profile)
    values, values_percent = extract_value(p, data_path, spectra)
    p_vals = [p[0][0] for p in values]
    p_vals_percent = [p[0][0] for p in values_percent]

    # set up all the customization for the plot
    bandwidth = [B1, B2, B3, B4, B5, B6, B7, B8, B8a, B9, B11, B12]
    colors = ['lightsteelblue', 'blue', 'green', 'red', 'lime', 'limegreen',
              'darkgreen', 'brown', 'indianred', 'firebrick', 'blueviolet', 'darkviolet']
    coords = [(440, 0.19), (495, 0.19), (565, 0.19), (666, 0.19), (710, 0.19), (745, 0.19),
              (790, 0.19), (908, 0.21), (855, 0.19), (945, 0.19), (1630, 0.19), (2250, 0.19)]
    ticks = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6',
             'B7', 'B8', 'B8a', 'B9', 'B11', 'B12']

    # define size of the plot
    fig = plt.figure(figsize=(18, 5))
    ax = set_style('dark')
    ax = fig.add_subplot(1, 1, 1)
    ax2 = ax.twinx()

    ax.plot(wavelengths, p_vals, 'o', mfc='none',
            markersize=8, markeredgewidth=1, color='black')
    ax.plot(wavelengths, p_vals, linestyle=':',
            linewidth=1.5, label=label, color='black')
    ax2.plot(wavelengths, p_vals_percent, linestyle=':',
             linewidth=1.5, color='black')
    for band, color, tick, coord in zip(bandwidth, colors, ticks, coords):
        ax.axvspan(band[0], band[1], alpha=0.4, color=color)
        ax.annotate(tick, xy=coord, xytext=coord, color='black')
        ax.set_xlabel('wavelength(nm)', fontsize=15)
        ax.set_xticks(wavelengths)
        ax.tick_params(axis='x', rotation=75)
        ax.set_ylabel('reflectance', fontsize=15)
        ax.legend(loc='upper right')
        ax2.set_ylabel('reflectance (%)', fontsize=15)
