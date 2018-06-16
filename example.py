
import pandas as pd
import iplot

iplot.BROWSER = 'google-chrome'
idx = pd.date_range('2018-01-01', '2019-01-01', freq='h')[:-1]
df = pd.DataFrame(index = idx)
df['POA'] = pd.np.sin(idx.hour *3.14159/ 24 + pd.np.random.random(len(idx))*0.1)*1000
df['Wind'] = pd.np.random.random(len(idx))*5
df['Temp'] = 15 + -20*pd.np.cos(idx.dayofyear*6.28/365) + pd.np.sin(idx.hour *3.14159/ 24)*10
df['Power'] = df['POA'].multiply(7000).multiply(1-0.005*(df['Temp']-25)*(5-df['Wind'])).clip_upper(5000000)
iplot.show(df.loc[df.index.month == 1, :])

