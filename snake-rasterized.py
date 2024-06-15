import numpy as np
import geopandas as gpd
import pygmt
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy


from datetime import datetime

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

gdf_dec = gdf.iloc[::5,:]



proj = ccrs.PlateCarree()
extent = (-179.9, 179.9, -89.9, 89.9)

time_step = 1./365.


bin_size_degrees = .1

year_grid = pygmt.binstats(data=gdf_dec[['Longitude', 'Latitude', 'Year']], statistic='l',
                    spacing=bin_size_degrees, region='g', search_radius='{:f}d'.format(bin_size_degrees*2.5))

magnetic_grid = pygmt.binstats(data=gdf_dec[['Longitude', 'Latitude', 'Cleaned residual field']], statistic='m',
                     spacing=bin_size_degrees, region='g', search_radius='{:f}d'.format(bin_size_degrees*2.5))





for yr in np.arange(1964,2009,time_step):
    
    #if yr>1980:
    #    all_data_so_far = gdf_dec20.query('Year<@yr')
    #else:
    #all_data_so_far = gdf_dec.query('Year<@yr')
    all_data_so_far = magnetic_grid.where(year_grid<yr)


    most_recent_data = gdf_dec.query('Year<@yr & Year>(@yr-@time_step*5)')

    fig = plt.figure(figsize=[32, 16])

    # We choose to plot in an Orthographic projection as it looks natural
    # and the distortion is relatively small around the poles where
    # the aurora is most likely.

    # ax1 for Northern Hemisphere
    ax = fig.add_subplot(1, 1, 1, projection=ccrs.Mollweide(0))

    #ax.coastlines(zorder=3)
    #ax.stock_img()
    #ax.gridlines()
    #ax.gridlines(linewidth=1, color='gray', alpha=0.5, linestyle='--', xlocs=range(-180, 181, 15), ylocs=range(-90, 91, 15))

    ax.add_feature(cartopy.feature.LAND.with_scale('10m'), facecolor='grey')
    ax.set_extent(extent, crs=proj)

    ax.spines['geo'].set_linewidth(4)
    ax.spines['geo'].set_edgecolor('black')

    #if len(all_data_so_far)>0:
    #    ax.scatter(all_data_so_far.geometry.x, 
    #               all_data_so_far.geometry.y, 
    #               c=all_data_so_far['Residual field'], 
    #               cmap='seismic', vmin=-200, vmax=200,
    #               s=1, alpha=0.7,
    #               transform=proj)
    ax.pcolormesh(all_data_so_far, cmap='seismic', vmin=-200, vmax=200, transform=proj)
    if len(most_recent_data)>0:
        alpha_factor = np.array(1+(most_recent_data.Year-yr) / (time_step*5))
        ax.scatter(most_recent_data.geometry.x, 
                   most_recent_data.geometry.y, 
                   color='darkorange', s=30,
                   transform=proj, alpha=alpha_factor, zorder=2)

    plt.tight_layout()
    yyyy,mm,dd = decimal_year_to_year_month(yr)
    fig.suptitle('{:d}/{:d}/{:d}'.format(yyyy,mm,dd), y=0.97, x=0.1, fontsize=80)
    #plt.show()
    
    fig.savefig('./sequence/Shiptracks/sequence_{:0.3f}.jpg'.format(yr), dpi=75)
    plt.close()
    break

