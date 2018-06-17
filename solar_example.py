
import pandas as pd
import iplot
iplot.BROWSER = 'google-chrome'

idx = pd.date_range("2018-01-01", "2018-02-01", freq = "1min")[:-1]
df = pd.DataFrame(index = idx)

df['irradiance'] = -(df.index.hour+df.index.minute/60.0-8) * (df.index.hour+df.index.minute/60.0-18)
df['irradiance'] = 1000 * df['irradiance'] / df['irradiance'].max()
df['irradiance'] *= 1-pd.np.random.random(len(df.index)) / 2
df['irradiance'] = df['irradiance'].clip_lower(0)


df['temperature'] = 20* pd.np.sin(pd.np.arange(len(df.index)) * 6.28 / (60*24)) + 20
df['wind speed'] = pd.np.random.random(len(df.index)) * 5

df['production'] = (df['irradiance'] * 8 * (1-0.003*(df['temperature']-20)*(5-df['wind speed'])))

df['clipping_loss'] = df['production'].clip_lower(5000) - 5000
df['production'] = df['production'].clip_upper(5000)


print "starting iplot"
iplot.show(df)

