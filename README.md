# AeN_NetCDF_cruise_to_stations

Python script to separate a NetCDF file consisting of CTD data from a whole cruise to several smaller files, divided station by station, each including a single depth profile.

This script has been tailored to the Nansen Legacy project CTD data,
and needs some tweaking to make it more broadly useable. Some global attributes will be updated accordingly.

Required modules:
xarray, numpy, sys, datetime, pandas, os
