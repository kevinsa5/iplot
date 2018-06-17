
import pandas as pd
import iplot
iplot.BROWSER = 'google-chrome'

try:
    df = pd.read_excel("rsfweatherdata2011.xlsx")
except:
    url = "https://openei.org/doe-opendata/dataset/8a33af58-0566-4244-a316-ae150481a6f2/resource/fed3e99c-dabc-44b4-9e34-08c820af7bcd/download/rsfweatherdata2011.csv"

    df = pd.read_csv(url, usecols = range(5), index_col = 0, parse_dates = True).dropna()
    df.index += pd.to_timedelta(df['HOUR-MST'], unit='h')
    df.drop(columns='HOUR-MST', inplace=True)
    df.to_excel("rsfweatherdata2011.xlsx")

df = df.loc[df.index.month == 4, :]

print "starting iplot"
iplot.show(df)

