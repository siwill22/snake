import numpy as np
import geopandas as gpd
import pygmt
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy
from datetime import datetime
from multiprocessing import Pool



def decimal_year_to_year_month(decimal_year):
    year = int(decimal_year)
    month_decimal = (decimal_year - year) * 12
    month = int(month_decimal) + 1  # Adding 1 to convert 0-based index to 1-based index

    # Handle December
    #if month == 13:
    #    year += 1
    #    month = 1

    # Convert fractional month to days
    if month==12:
        days_in_month=31
    else:
        days_in_month = (datetime(year, month + 1, 1) - datetime(year, month, 1)).days
    day = int((month_decimal - int(month_decimal)) * days_in_month) + 1

    return year, month, day


def process_single_image(params):
    
    yr, magnetic_grid, year_grid, gdf_dec, time_step = params
    
    print(yr)
    #all_data_so_far = gdf.query('Year<@yr')
    all_data_so_far = magnetic_grid.where(year_grid<yr)

    #most_recent_data = all_data_so_far.query('Year>(@yr-@time_step*5)')
    most_recent_data = gdf_dec.query('Year<@yr & Year>(@yr-@time_step*5)')


    region = 'd'
    projection = 'W180/12c'
    fig = pygmt.Figure()
    
    pygmt.makecpt(cmap='polar', series='-200/200', reverse=True)
    fig.grdimage(all_data_so_far, region=region, projection=projection, cmap=True, verbose='q')

    fig.coast(land='gray70', resolution='l', area_thresh=5000.,
              region=region, projection=projection, 
              transparency=20)

    if len(most_recent_data)>0:
        fig.plot(x=most_recent_data.geometry.x, 
                 y=most_recent_data.geometry.y,
                 fill='darkorange', 
                 style='c',
                 size=0.05+np.arange(len(most_recent_data))/(len(most_recent_data)*20),
                 transparency=70,
                 #pen='0.02p,darkgray', 
                 region=region, projection=projection)

    yyyy,mm,dd = decimal_year_to_year_month(yr)
    fig.text(x=0.01,y=1.07,text='{:d}/{:d}/{:d}'.format(yyyy,mm,dd), justify='LM',
                     region='0/1/0/1', projection='x5.25c', font='12p', no_clip=True)
    
    fig.basemap(frame=['f'],#,'+t{:0.1f}'.format(yr)], 
                region=region, projection=projection)

    fig.savefig('./sequence/sequence_{:0.3f}.png'.format(yr))
    #fig.show(width=1000)
    #break
    

def generate_images_parallel(data_array, mask_array, mask_values, profile_data, time_step, num_processes=None):
    """
    Generate multiple images in parallel using multiprocessing.
    
    Args:
        data_array (xarray.DataArray): The input data array
        mask_values (list): List of mask values to process
        output_dir (str): Directory to save the output images
        num_processes (int, optional): Number of processes to use. 
                                     Defaults to CPU count - 1
    """
    
    # If num_processes not specified, use CPU count - 1
    if num_processes is None:
        num_processes = max(1, mp.cpu_count() - 1)
    
    # Prepare parameters for each image
    params = [
        (
            mask_value,
            data_array,
            mask_array,
            profile_data,
            time_step
        )
        for mask_value in mask_values
    ]
        
    # Create and run the process pool
    with Pool(processes=num_processes) as pool:
        pool.map(process_single_image, params)



# Example usage:
if __name__ == '__main__':
    
    grid_spacing_degrees = 0.1
    profile_desampling_factor = 1


    print('Loading profile data....')
    df = gpd.pd.read_csv('/Users/simon/Data/Quesnel/global_marine_lvl.xymlt', 
                         header=None, 
                         sep='\s+',
                         names=['Longitude',
                                'Latitude',
                                'Residual field',
                                'Cleaned residual field',
                                'Cruise ID',
                                'Year'])

    # Convert DataFrame to GeoDataFrame
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.Longitude, df.Latitude), crs='EPSG:4326')

    #proj = ccrs.PlateCarree()
    #extent = (-179.9, 179.9, -89.9, 89.9)

    gdf_dec = gdf.iloc[::profile_desampling_factor,:].reset_index(drop=True)

    #bin_size_degrees = 0.1

    print('Binning data into grid cells....')
    base = grid_spacing_degrees

    gdf_dec['lat_bin'] = base * np.round(gdf_dec['Latitude']/base)
    gdf_dec['lon_bin'] = base * np.round(gdf_dec['Longitude']/base)

    print('Making grid of first data coverage time....')
    year_grid = pygmt.nearneighbor(x=gdf_dec.Longitude,
                              y=gdf_dec.Latitude, 
                              z=gdf_dec.Year,
                              region='d', spacing='{:f}d'.format(grid_spacing_degrees), search_radius='{:f}d'.format(grid_spacing_degrees*2),
                              sectors='4+m1')

    print('Making grid of magnetic anomalies....')
    pixel_stats = gdf_dec.groupby(['lon_bin','lat_bin']).agg({
            'Longitude': ['count', 'median', 'std'],
            'Latitude': ['median', 'std'],
            'Cleaned residual field': ['median']
        }).reset_index()

    magnetic_grid = pygmt.sphinterpolate(
        data = np.vstack((pixel_stats['Longitude']['median'],
               pixel_stats['Latitude']['median'],
               pixel_stats['Cleaned residual field']['median'])).T,
        spacing='{:f}d'.format(grid_spacing_degrees),
        region='d')

    magnetic_grid = magnetic_grid.where(np.isfinite(year_grid), np.nan)


    print('Starting animation loop....')
    time_step = 1./365.

    year_array = list(np.arange(1980.0,1990.0,time_step))
    num_processes = 3


    generate_images_parallel(
            data_array=magnetic_grid,
            mask_array=year_grid,
            mask_values=year_array,
            profile_data=gdf_dec,
            time_step=time_step,
            num_processes=num_processes  # Adjust based on your CPU cores
        )




    
    
