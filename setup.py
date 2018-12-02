from setuptools import setup, find_packages

setup(name='subset_nwm_netcdf',
      version='1.2.5',
      description='Subset National Water Model (NWM) NetCDF',
      long_description=open("README.rst").read(),
      long_description_content_type="text/markdown",
      url='https://github.com/zhiyuli/subset_nwm_netcdf',
      author='Zhiyu/Drew Li',
      author_email='zyli2004@gmail.com',
      license='BSD-2',
      include_package_data=True,
      packages=find_packages('src'),
      package_dir={'': 'src'},
      zip_safe=False,
      install_requires=[
          'Fiona>=1.7.5',
          'Shapely>=1.5.17',
          'pysqlite>=2.8.3',
          'numpy>=1.2.1',
          'pyproj>=1.9.5.1',
          'netCDF4>=1.2.7',
          'GDAL>=2.1.2'],
      # package_data={'': ['*.py'],
      #               'subset_nwm_netcdf': ['static/sed_win/*',
      #                                     'static/data/utah/*',
      #                                     'static/netcdf_templates/v1.1/forcing/analysis_assim/*',
      #                                     'static/netcdf_templates/v1.1/forcing/medium_range/*',
      #                                     'static/netcdf_templates/v1.1/forcing/short_range/*',
      #                                     'static/netcdf_templates/v1.1/forecast/analysis_assim/*',
      #                                     'static/netcdf_templates/v1.1/forecast/short_range/*',
      #                                     'static/netcdf_templates/v1.1/forecast/medium_range/*',
      #                                     'static/netcdf_templates/v1.1/forecast/long_range/*'],
      #               },
      )
