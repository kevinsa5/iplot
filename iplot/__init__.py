import pandas as pd
import numpy as np
import webbrowser
import matplotlib.pyplot as plt
import matplotlib as mpl


from bokeh.layouts import column, row, widgetbox
from bokeh.models import CustomJS, Button, Select, Slider
from bokeh.models import Panel, Tabs 
from bokeh.models import DataTable, TableColumn
from bokeh.models import DateFormatter, NumberFormatter, BooleanFormatter, StringFormatter
from bokeh.models import BoxSelectTool, LassoSelectTool
from bokeh.plotting import figure, curdoc, ColumnDataSource
from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler



BROWSER = None

def show(df, port=8080):
    doc_maker = document_factory(df)
    apps = {'/': Application(FunctionHandler(doc_maker))}
    # might need to add allow_websocket_origin=['foo.com', 'localhost', etc]
    server = Server(apps, port = port)

    # bit of a race condition here, but it hasn't bit me yet...
    url = "http://localhost:{}".format(port)
    if BROWSER is not None:
        webbrowser.get(BROWSER).open(url)
    else:
        webbrowser.open(url)
    server.run_until_shutdown()


def document_factory(df):

    def make_table_tab(source):
    
        def get_formatter(data):
            if data.dtype.name == 'datetime64[ns]':
                return DateFormatter(format='%Y-%m-%d %H:%M:%S')
            if data.dtype.name in ['float64', 'int64']:
                return NumberFormatter(format='0.0[000]')
            if data.dtype.name == 'bool':
                return BooleanFormatter()
            
            return StringFormatter()
        
        table_columns = [
            TableColumn(field = 'index', title = '', formatter = get_formatter(df.index))
        ]
        
        for col in df.columns:
            fmt = get_formatter(df[col])
            title = col
            table_col = TableColumn(field = col, title = title, formatter = fmt)
            table_columns.append(table_col)
        
        data_table = DataTable(source = source, columns = table_columns, width = 1600, height = 800)
        panel = Panel(child = data_table, title = "Table View")
        return panel

    def make_plots_tab(source):
    
        def make_controls(source):
    
            xselect = Select(name = 'iplot-xvar', 
                             title="X-Var:", 
                             value=df.columns[0], 
                             options=df.columns.tolist())
    
            yselect = Select(name = 'iplot-yvar', 
                             title="Y-Var:", 
                             value=df.columns[1], 
                             options=df.columns.tolist())
        
            cselect = Select(name = 'iplot-cvar', 
                             title="C-Var:", 
                             value=df.columns[2], 
                             options=df.columns.tolist())
                             
            sslider = Slider(start=1, end=20, step=1, value=4, title="Marker Size")
            aslider = Slider(start=0, end=255, step=1, value=255, title="Marker Alpha")

        
            def x_callback(attr, old, new):
                data = source.data
                data['iplot-xvar'] = data[new]
                source.data = data
        
            def y_callback(attr, old, new):
                data = source.data
                data['iplot-yvar'] = data[new]
                source.data = data
                
            def c_callback(attr, old, new):

                var = df[new]
                colors = [
                    "#%02x%02x%02x" % (int(r), int(g), int(b)) 
                        for r, g, b, _ in 255*plt.cm.viridis(mpl.colors.Normalize()(var.values))
                ]
                data = source.data
                data['iplot-cvar'] = colors
                source.data = data
            
            def s_callback(attr, old, new):
                curdoc().get_model_by_name('xy_circle').glyph.size = new
                
            def a_callback(attr, old, new):
                curdoc().get_model_by_name('xy_circle').glyph.fill_alpha = new/255.0

            xselect.on_change('value', x_callback)
            yselect.on_change('value', y_callback)
            cselect.on_change('value', c_callback)
            sslider.on_change('value', s_callback)
            aslider.on_change('value', a_callback)
            
            data = source.data
            data['iplot-xvar'] = data[xselect.value]
            data['iplot-yvar'] = data[yselect.value]
            source.data = data
            c_callback(None, None, cselect.value)
        
            controls = widgetbox([yselect, xselect, cselect, sslider, aslider])
            return controls
        
        def make_ts_combo(source, col):

            def make_ts_plot(source, col):
                ts_args = {
                    'x_axis_type' : 'datetime',
                    'tools' : 'reset,previewsave',
                    'plot_width' : 800,
                    'plot_height' : 400,
                }
        
                ts = figure(**ts_args)
                ts.line(x = 'index', y = col, source = source)
                ts.circle(x = 'index', y = col, source = source)
                ts.add_tools(BoxSelectTool(dimensions="width"))
            
                return ts
            
            def make_histogram(source, col):
                fig = figure(toolbar_location=None, plot_width = 100, plot_height = 400, x_axis_location=None, y_axis_location=None)
                fig.xgrid.grid_line_color = None
                fig.ygrid.grid_line_color = None
                
                hist, edges = np.histogram(source.data[col], bins=20)
                all_quad = fig.quad(left=0, bottom=edges[:-1], top=edges[1:], right=hist, color="white", line_color="#3A5785")
                sel_quad = fig.quad(left=0, bottom=edges[:-1], top=edges[1:], right=[0]*(len(edges)-1), color="#3A5785", line_color="#3A5785")
                
                def update(attr, old, new):
                    inds = source.selected.indices
                    
                    hist, edges = np.histogram(source.data[col], bins=20)
                    all_quad.data_source.data['right'] = hist
                    
                    hist, _ = np.histogram(np.array(source.data[col])[inds], bins=edges)
                    sel_quad.data_source.data['right'] = hist                
                
                source.on_change('selected', update)
                source.on_change('data', update)

                return fig
            
            ts = make_ts_plot(source, col)
            hist = make_histogram(source, col)
            
            return row(ts, hist)


        TOOLS = "hover,crosshair,pan,wheel_zoom,zoom_in,zoom_out," \
                "box_zoom,reset,save,box_select,lasso_select,"

        xy = figure(plot_width = 800, plot_height = 800, tools=TOOLS, active_drag='lasso_select')
        xy.select(LassoSelectTool).select_every_mousemove = False
        xy.circle(x = 'iplot-xvar', y = 'iplot-yvar', fill_color = 'iplot-cvar', line_color = 'iplot-cvar', source = source, name = 'xy_circle')
        
        controls = make_controls(source)

        ts1 = make_ts_combo(source, 'iplot-xvar')
        ts2 = make_ts_combo(source, 'iplot-yvar')

        panel = Panel(child = row([controls, xy, column([ts2, ts1])]), title = "Plot View")
        return panel


    def make_document(doc):
        # have to build CDS with lists, not pd/np arrays
        # see https://github.com/bokeh/bokeh/issues/7417
        source = ColumnDataSource()
        data = {'index' : list(df.index)}
        for col in df.columns:
            data[col] = list(df[col])
        source.data = data
        
        table = make_table_tab(source)
        plots = make_plots_tab(source)
        
        tabs = Tabs(tabs = [plots, table])
        doc.add_root(tabs)
        doc.title = "iPlot"

    df = df.copy()
    df['minute'] = df.index.minute
    df['hour'] = df.index.hour
    df['day'] = df.index.day
    df['month'] = df.index.month

    return make_document

def available_browsers():
    return webbrowser._browsers.keys()

BROWSER = 'google-chrome'
idx = pd.date_range('2018-01-01', '2019-01-01', freq='h')[:-1]
df = pd.DataFrame(index = idx)
df['POA'] = pd.np.sin(idx.hour *3.14159/ 24 + pd.np.random.random(len(idx))*0.1)*1000
df['Wind'] = pd.np.random.random(len(idx))*5
df['Temp'] = 15 + -20*pd.np.cos(idx.dayofyear*6.28/365) + pd.np.sin(idx.hour *3.14159/ 24)*10
df['Power'] = df['POA'].multiply(7000).multiply(1-0.005*(df['Temp']-25)*(5-df['Wind'])).clip_upper(5000000)
show(df.loc[df.index.month == 1, :])
