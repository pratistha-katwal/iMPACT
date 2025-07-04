import plotly.graph_objects as go
import pymannkendall as mk

def plot_precipitation_trend(x,y, legend, hovertemplate, title, yaxis, y_max, y_min, y_pad, mk_result,unit):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x= x,
        y=y,
        mode='lines+markers',
        name=legend,
        line=dict(color='royalblue', width=3),
        marker=dict(size=8, color='white', line=dict(width=2, color='darkblue')),
        hovertemplate=hovertemplate
    ))

    fig.update_layout(
        title={
            'text': title,
            'x': 0.5,
            'xanchor': 'center',
            'font': dict(size=18, family="Arial Black", color='MidnightBlue')
        },
        xaxis=dict(
            title=dict(
                text='Year',
                font=dict(size=16, family="Arial Black", color='black')
            ),
            tickfont=dict(size=12, family="Arial", color='black'),
            showgrid=True,
            gridcolor='lightgrey',
            showline=True,
            linewidth=2,
            linecolor='grey',
            ticks='outside'
        ),
        yaxis=dict(
            title=dict(
                text=yaxis,
                font=dict(size=16, family="Arial Black", color='black')
            ),
            tickfont=dict(size=12, family="Arial", color='black'),
            showgrid=True,
            gridcolor='lightgrey',
            showline=True,
            linewidth=2,
            linecolor='grey',
            ticks='outside',
            range=[y_min, y_max + y_pad]
        ),
        plot_bgcolor= 'rgba(240,248,255, 0.4)',
        paper_bgcolor='white',
        annotations=[
            dict(
                x=0.02,
                y=1,
                xref='paper',
                yref='paper',
                text=(
                    f"<b>Mann-Kendall Test</b><br>"
                    f"Trend: <i>{mk_result.trend}</i><br>"
                    f"Slope: { mk_result.slope:.2f} {unit}<br>"
                    f"p-value: { mk_result.p:.2f}"
                ),
                showarrow=False,
                align='left',
                font=dict(size=12, color='black'),
                bgcolor='rgba(240,240,240,0.9)',
                bordercolor='black',
                borderwidth=1,
                borderpad=8
            )
        ],
        width=1250,
        height=700,
    )
    return fig
