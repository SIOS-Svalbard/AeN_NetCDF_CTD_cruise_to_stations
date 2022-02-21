#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 15 14:06:27 2022

@author: lukem

Script to split a NetCDF file into multiple smaller, single dimension NetCDF 
files.

The user should provide the parent file.

The output will be multiple small NetCDF files (single station/depth 
profile). Some global attributes will be updated accordingly.

This script has been tailored to the Nansen Legacy project CTD data,
and needs some tweaking to make it more broadly useable.
"""

import xarray as xr
import numpy as np
import sys
from datetime import datetime as dt
import pandas as pd
import os

class Parent_NetCDF_File:
    '''
    NetCDF file that needs to be split
    '''
    def __init__(self, filepath):
        self.filepath = filepath
        
    def load_contents(self):
        '''
        Loading the parent file. Checking if it exists.

        Returns
        -------
        None.

        '''
        try:
            self.contents = xr.open_dataset(self.filepath) 
        except:
            print(f'''Could not load {self.filepath}.
                  Are you sure that this is the right filepath to your NetCDF file?
                  ''')
            sys.exit('File not found')
    
    def get_coordinate_variables_values(self):
        '''
        Making a list of coordinate values that can be looped through when creating the child files

        Returns
        -------
        None.

        '''
        
        self.latitudes = np.array(self.contents['LATITUDE'])
        self.longitudes = np.array(self.contents['LONGITUDE'])
        self.times = np.array(self.contents['TIME'])
    
    def get_min_max_pressures(self):
        '''
        Getting a list of the minimum and maximum depths for each station
        
        Returns
        -------
        None.

        '''     
        self.min_pressures = [min(i) for i in np.array(self.contents['PRES'])]
        self.max_pressures = [max(i) for i in np.array(self.contents['PRES'])]
    
    def add_change_drop_gloabl_attributes(self):
        '''
        Updating some global attributes, where the values will be applicable to every child file

        Returns
        -------
        None.

        '''               
        self.contents.attrs['project'] = 'The Nansen Legacy Project (RCN # 276730)'
        self.contents.attrs['acknowledgement'] = f'The Nansen Legacy project is funded by the Research Council of Norway (RCN # 276730). These data are created from the CTD data published by NMDC for the whole cruise ({self.contents.attrs["doi"]}). The values have not be changed. For information about this process, please contact Luke Marsden at data.nleg@unis.no'
        self.contents.attrs['summary'] = self.contents.attrs['summary']+' These data are created from the CTD data published by NMDC for the whole cruise ({self.contents.attrs["doi"]}). The values have not be changed.'
        self.contents.attrs['references'] = 'https://doi.org/'+self.contents.attrs['doi']
        self.contents.attrs['naming_authority'] = 'no.unis'
        self.contents.attrs['creator_institution'] = self.contents.attrs['creator_name']
        self.contents.attrs['publisher_name'] = self.contents.attrs['creator_name']
        self.contents.attrs['creator_email'] = 'datahjelp@imr.no'
        self.contents.attrs['publisher_email'] = self.contents.attrs['creator_email']
        self.contents.attrs['publisher_url'] = self.contents.attrs['creator_url']
        unwanted_atts = [
            'last_latitude_observation',
            'last_longitude_observation',
            'format_version',
            'last_date_observation'
            ]
        for att in unwanted_atts:
            del self.contents.attrs[att] 
            
    # def checking_dimension(self):
    #     '''
    #     Written with a view to check whether there is a pressure or depth dimension, but incomplete.

    #     Returns
    #     -------
    #     None.

    #     '''
    #     if 'depth' in [s.lower() for s in list(self.contents.coords)]:
    #         print("depth coordinate variable found")
    #         pass
    #     else:
    #         print('No depth coordinate variable found.')
    #         ans = input('''Would you like to create one? Please note that the parent
    #                     file itself will not be modified
    #                     (Y/N): ''').lower()
    #         while ans not in ['y', 'n']: 
    #             ans = input('Please enter Y or N: ').lower()
    #         if ans == 'n':
    #             sys.exit('Unable to proceed without a coordinate variable. Quitting.')
    #         elif ans == 'y':
    #             try: 
    #                 minDepth = self.contents.attrs['geospatial_vertical_min']
    #                 maxDepth = self.contents.attrs['geospatial_vertical_max']    
    #             except:
    #                 minDepth = int(input('Enter the minimum depth: '))
    #                 maxDepth = int(input('Enter the minimum depth: '))
            
    #         ans = input('''In the absence of a depth coordinate variable I 
    #                     am assuming that the sample interval in depth is constant.
                        
    #                     Is this correct? (Y/N): ''').lower() 
    #         while ans not in ['y', 'n']: 
    #             ans = input('Please enter Y or N: ').lower()
    #         if ans == 'n':
    #             sys.exit('Unable to assign irregular sampling intervals. Quitting.')
    #         elif ans == 'y':
    #             #sampleInterval = 
    #             print('Minimum depth: ', minDepth, ' m')
    #             print('Maximum depth: ', maxDepth, ' m') 
                
class Child_NetCDF_File:
    '''
    Single station NetCDF file (the output)
    '''
    def __init__(self, position, parentFile):
        '''
        Initialising object
        
        Assigning some attributes that will be used later, based on content of the
        parent file, that are unique to this child file.

        Returns
        -------
        None.

        '''
        
        self.position = position
        self.parentFile = parentFile
        
        self.latitude = self.parentFile.latitudes[self.position]
        self.longitude = self.parentFile.longitudes[self.position]
        self.lat_string = "{:.4f}".format(self.latitude).replace('.','-')
        self.lon_string = "{:.4f}".format(self.longitude).replace('.','-')
        
        self.min_pressure = self.parentFile.min_pressures[self.position]
        self.max_pressure = self.parentFile.max_pressures[self.position]
        
        self.time = self.parentFile.times[self.position]
        self.timestamp_string = np.datetime_as_string(self.time, timezone='UTC').split('.')[0].replace(':','-') + 'Z'
        
        self.filename = f'Nansen_Legacy_CTD_data_single_station_lat_{self.lat_string}_lon_{self.lon_string}_dt_{self.timestamp_string}.nc'
        
    def create_dataset_with_variables(self):  
        '''
        Creating child xarray dataset
        
        Adding variables and variable attributes

        Returns
        -------
        None.

        '''
        pressures = np.array(self.parentFile.contents['PRES'][self.position])
        i_min = list(pressures).index(self.min_pressure)
        i_max = list(pressures).index(self.max_pressure)
        
        df = pd.DataFrame()
        
        for data_var in list(self.parentFile.contents.data_vars):
            if len(self.parentFile.contents[data_var].dims) == 2:
                values = np.array(self.parentFile.contents[data_var][self.position])
                values = values[i_min:i_max]
                df[data_var] = values
            elif len(self.parentFile.contents[data_var].dims) > 2:
                sys.exit(f'Not programmed to handle variables with more than 2 dimensions ({data_var})')
            else:
                pass
            
        self.contents = xr.Dataset.from_dataframe(df)
                
        self.contents = self.contents.set_coords('PRES') # Specfiy pressure as a coordinate (to be used as a dimension)
                
        self.contents = self.contents.reset_index('index', drop=True) # Get rid of the numeric index as dimension.
        
        self.contents = self.contents.swap_dims({'index':'PRES'})
        
        for data_var in list(self.parentFile.contents.data_vars):
            if len(self.parentFile.contents[data_var].dims) == 2:
                self.contents[data_var].attrs = self.parentFile.contents[data_var].attrs
                if 'QC' not in data_var:
                    if 'DM' not in data_var:
                        self.contents[data_var].attrs['coverage_content_type'] = 'physicalMeasurement'
                        if 'valid_min' in list(self.parentFile.contents[data_var].attrs.keys()):
                            self.contents[data_var].attrs['valid_min'] = self.parentFile.contents[data_var].attrs['valid_min']*0.001 # Correcting for scale factor being automatically removed by xarray
                        if 'valid_max' in list(self.parentFile.contents[data_var].attrs.keys()):
                            self.contents[data_var].attrs['valid_max'] = self.parentFile.contents[data_var].attrs['valid_max']*0.001     
            elif len(self.parentFile.contents[data_var].dims) > 2:
                sys.exit(f'Not programmed to handle variables with more than 2 dimensions ({data_var})')
            else:
                pass
                
            
            try:
                avs = self.parentFile.contents[data_var].attrs['ancillary_variables'].split(' ')
                for av in avs:
                    if av not in list(self.parentFile.contents.data_vars):
                        self.contents[data_var].attrs['ancillary_variables'] = self.contents[data_var].attrs['ancillary_variables'].replace(av,'')
                    else:
                        pass
            except:
                continue
            
    def assign_global_attributes(self):
        '''
        Assigning global attributes.
        Changing some from what they were defined as in the parent file in some cases

        Returns
        -------
        None.

        '''
        self.contents.attrs = self.parentFile.contents.attrs.copy()
        
        self.contents.attrs['geospatial_lat_min'] = self.latitude
        self.contents.attrs['geospatial_lat_max'] = self.latitude
        self.contents.attrs['geospatial_lon_min'] = self.longitude
        self.contents.attrs['geospatial_lon_max'] = self.longitude
        self.contents.attrs['geospatial_vertical_min'] = self.min_pressure
        self.contents.attrs['geospatial_vertical_max'] = self.max_pressure
        self.contents.attrs['geospatial_vertical_units'] = 'dbar'
        self.contents.attrs['geospatial_vertical_resolution'] = '1 dbar'
        
        self.contents.attrs['time_coverage_start'] = str(self.time).split('.')[0]+'Z'
        self.contents.attrs['time_coverage_end'] = str(self.time).split('.')[0]+'Z'
        
        dtnow = dt.now().strftime("%Y-%m-%dT%H:%M:%SZ")
        self.contents.attrs['date_created'] = dtnow
        self.contents.attrs['date_update'] = dtnow
        self.contents.attrs['history'] = f'Created at {dtnow} using the xarray library in Python'
        
        self.contents.attrs['id'] = self.contents.attrs['id']+'_'+self.lat_string+'_'+self.lon_string
        self.contents.attrs['title'] = self.filename.split('.')[0]
        del self.contents.attrs['doi']
        
        self.contents.attrs['comment'] = 'Descending CTD profile'

    def output_to_netcdf(self):
        '''
        Defining the encoding for each variable and outputting as a NetCDF file
        Each file is dumped in a subdirectory with the name from the ID of the parent file

        Returns
        -------
        None.

        '''
        self.encoding = {}
        
        for data_var in list(self.contents.data_vars):
            
            if data_var == 'PRES':
                self.encoding[data_var] = {
                    'dtype': 'float32',
                    '_FillValue': None
                    }
            elif 'DM' in data_var:
                self.contents[data_var].attrs['flag_values'] = np.array(self.contents[data_var].attrs['flag_values'].replace(' ','').split(','))
                self.encoding[data_var] = {
                    'dtype': 'S1',
                    '_FillValue': ' '
                    }
            elif 'QC' in data_var:
                self.encoding[data_var] = {
                    'dtype': 'int8',
                    '_FillValue': -127
                    }
            else:
                self.encoding[data_var] = {
                    'dtype': 'float32',
                    '_FillValue': -2147483647
                    }
        
        subdir = self.parentFile.contents.attrs['id']
        if not os.path.exists(subdir):
            os.makedirs(subdir)
        self.contents.to_netcdf(subdir+'/'+self.filename,encoding=self.encoding)       

def main():
    parent_files = os.listdir('data/')
    for parent_file in parent_files:
        print('\nParent file:',parent_file)
        parentFile = Parent_NetCDF_File('data/'+parent_file)
        parentFile.load_contents()
        parentFile.add_change_drop_gloabl_attributes()
        parentFile.get_coordinate_variables_values()
        parentFile.get_min_max_pressures()
        
        for p in np.array(parentFile.contents['POSITION']):
            print("Position:", p)
            childFile = Child_NetCDF_File(p, parentFile)
            childFile.create_dataset_with_variables()
            childFile.assign_global_attributes()
            childFile.output_to_netcdf()
            print('File created: ', childFile.filename,'\n')
            
if __name__ == "__main__":
    sys.exit(main())
        
#%%

file = xr.open_dataset('AR_PR_CT_58GS_2020113/Nansen_Legacy_CTD_data_single_station_lat_78-3517_lon_34-7638_dt_2020-10-20T07-35-31Z.nc')
print(file['PRES_DM'])

#%%
file.close()