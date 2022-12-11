PROVIDERS = {'https://data.bs.ch': 'Kanton Basel-Stadt (Switzerland)',
    'https://data.bl.ch':'Kanton Baselland (Switzerland)',
    'https://data.tg.ch':'Kanton Thurgau (Switzerland)',
    'https://opendata.paris.fr': 'Ville de Paris',
    'https://data.sncf.com/': 'SNCF (France)',
    'https://opendata.edf.fr': "EDF (France)", 
    'https://northernpowergrid.opendatasoft.com/': "Northern Powergrid",
    'https://opendata.wuerzburg.de': 'Würzburg',
    'https://opendata.townofmorrisville.org/': "Town of Morrisville",
    'https://nihr.opendatasoft.com/': "National Institute for Health and Care Research (NIHR)",
    'https://swisspost.opendatasoft.com/': "Swiss Post",
    }

SUMMARY_FUNCTIONS = ['sum', 'avg', 'count', 'max', 'min', 'median']
COMPARE_OPERATORS = ['=','<','<','>','like', 'in']
ALL_THEMES = '<select a theme>'
MAX_PREVIEW_RECORDS = 1000 
MAX_QUERY_RECORDS = 9900
QUERY_INCREMENT = 100