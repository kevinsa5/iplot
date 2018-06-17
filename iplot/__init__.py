import pandas as pd
import numpy as np
import webbrowser
import matplotlib.pyplot as plt
import matplotlib as mpl
import pkg_resources
import sys

from bokeh.layouts import column, row, widgetbox
from bokeh.models import CustomJS, Button, Select, Slider, PreText
from bokeh.models import Panel, Tabs, Spacer
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

    def make_about_tab():
        pkg = pkg_resources.require('iplot')[0]
        text = "\n".join(pkg.get_metadata_lines('METADATA'))
        text += "\n\n"
        text += "sys.version:" + sys.version
        pretext = PreText(text=text, width=600, height=600)
        
        panel = Panel(child = widgetbox(pretext), title = "About")
        return panel

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
        
            cols = df.columns.tolist()
            cols += ['minute', 'hour', 'day', 'month', 'index']
    
            xselect = Select(name = 'iplot-xvar', 
                             title="X-Var:", 
                             value=df.columns[0], 
                             options=cols)
    
            yselect = Select(name = 'iplot-yvar', 
                             title="Y-Var:", 
                             value=df.columns[1], 
                             options=cols)
        
            cselect = Select(name = 'iplot-cvar', 
                             title="C-Var:", 
                             value=df.columns[2], 
                             options=cols)

            rselect = Select(title="R-Var:", 
                             value="None", 
                             options=["1d", "1h", "15min", "5min", "None"])
                             
                             
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
                colors = colormap(source.data[new])
                data = source.data
                data['iplot-cvar'] = colors
                source.data = data
            
            def s_callback(attr, old, new):
                curdoc().get_model_by_name('xy_circle').glyph.size = new
                
            def a_callback(attr, old, new):
                curdoc().get_model_by_name('xy_circle').glyph.fill_alpha = new/255.0
            
            def r_callback(attr, old, new):
                if new == "None":
                    new = None
                source.selected.indices = []
                source.data = make_cds(df, new).data
            
            
            xselect.on_change('value', x_callback)
            yselect.on_change('value', y_callback)
            cselect.on_change('value', c_callback)
            sslider.on_change('value', s_callback)
            aslider.on_change('value', a_callback)
            rselect.on_change('value', r_callback)
                
            data = source.data
            data['iplot-xvar'] = data[xselect.value]
            data['iplot-yvar'] = data[yselect.value]
            source.data = data
            c_callback(None, None, cselect.value)
            
            controls = widgetbox([yselect, xselect, cselect, rselect, sslider, aslider])
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

    def make_cds(df, resample_freq):
        # have to build CDS with lists, not pd/np arrays
        # see https://github.com/bokeh/bokeh/issues/7417
        if resample_freq:
            aux = df.resample(resample_freq).mean()
        else:
            aux = df.copy()
        
        aux['minute'] = aux.index.minute
        aux['hour'] = aux.index.hour
        aux['day'] = aux.index.day
        aux['month'] = aux.index.month

        data = {'index' : list(aux.index)}
        for col in aux.columns:
            data[col] = list(aux[col])
        
        
        def model(name):
            return curdoc().get_model_by_name(name)
        
        try:
            data['iplot-xvar'] = data[model('iplot-xvar').value]
            data['iplot-yvar'] = data[model('iplot-yvar').value]
            data['iplot-cvar'] = colormap(data[model('iplot-cvar').value])
        except AttributeError:
            pass
        
        return ColumnDataSource(data)

    def colormap(values):
        colors = [
            "#%02x%02x%02x" % (int(r), int(g), int(b)) 
                for r, g, b, _ in 255*plt.cm.viridis(mpl.colors.Normalize()(values))
        ]
        return colors

    def make_document(doc):
        source = ColumnDataSource()
        source.data = make_cds(df, None).data
        
        table = make_table_tab(source)
        plots = make_plots_tab(source)
        about = make_about_tab()
        
        tabs = Tabs(tabs = [plots, table, about])
        doc.add_root(tabs)
        doc.title = "iPlot"

    return make_document

def available_browsers():
    return webbrowser._browsers.keys()

