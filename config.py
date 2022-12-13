

PROVIDERS = {'https://data.bs.ch': 'Kanton Basel-Stadt (CH)',
    'https://data.bl.ch':'Kanton Baselland (CH)',
    'https://data.tg.ch':'Kanton Thurgau (CH)',
    'https://opendata.paris.fr': 'Ville de Paris (F)',
    'https://data.sncf.com': 'SNCF (F)',
    'https://opendata.edf.fr': 'EDF (F)', 
    'https://data.casey.vic.gov.au/': 'City of Casey (AU)',
    'https://data.campbelltown.nsw.gov.au/': 'City of Cambelltown (AU)',
    'https://opendata.comune.bologna.it': 'Città de Bologna',
    'https://northernpowergrid.opendatasoft.com/': 'UK Northern Powergrid (UK)',
    'https://opendata.wuerzburg.de': 'Stadt Würzburg (DE)',
    'https://opendata.townofmorrisville.org/': 'Town of Morrisville (US)',
    'https://nihr.opendatasoft.com/': 'National Institute for Health and Care Research (NIHR), (UK)',
    'https://swisspost.opendatasoft.com/': 'Swiss Post (CH)',
    'https://opendata.umea.se/': 'City of Umeå (SV)',
    'https://kapsarc.opendatasoft.com/': 'KAPSARC', 
    'https://kering-group.opendatasoft.com/': 'KERING',
    'https://opendata.infrabel.be/': 'Infrabel sustainable train mobility (NL)',
    'https://israellivinglab.opendatasoft.com/': 'The Israel Smart Mobility Living Lab Consortium (IS)'
    }

SUMMARY_FUNCTIONS = ['sum', 'avg', 'count', 'max', 'min', 'median']
COMPARE_OPERATORS = ['=','<','<=','>','>=','!=','like', 'in']
ALL_THEMES = '<select a theme>'
MAX_PREVIEW_RECORDS = 1000 
MAX_QUERY_RECORDS = 9900
QUERY_INCREMENT = 100
DEFAULT_PROVIDER = 'https://data.bs.ch'