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



#proj = ccrs.PlateCarree()
#extent = (-179.9, 179.9, -89.9, 89.9)

time_step = 1./365.


bin_size_degrees = .1

year_grid = pygmt.binstats(data=gdf_dec[['Longitude', 'Latitude', 'Year']], statistic='l',
                    spacing=bin_size_degrees, region='g', search_radius='{:f}d'.format(bin_size_degrees*2.5))

magnetic_grid = pygmt.binstats(data=gdf_dec[['Longitude', 'Latitude', 'Cleaned residual field']], statistic='m',
                     spacing=bin_size_degrees, region='g', search_radius='{:f}d'.format(bin_size_degrees*2.5))




for yr in np.arange(1970,1980,time_step):

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

    fig.savefig('./sequence/Shiptracks/sequence_{:0.3f}.png'.format(yr))


