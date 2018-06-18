from setuptools import setup, find_packages

setup(
    name = 'iplot',
    version = '0.0.1',
    url ='https://github.com/kevinsa5/iplot',
    author = 'Kevin Anderson',
    author_email = 'kevinanderso@gmail.com',
    description = 'An interactive tool intended for timeseries data exploration',
    packages = ['iplot'],    
    install_requires = ['bokeh==0.12.16', 'pandas', 'matplotlib'],
)

