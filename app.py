import pandas as pd
import plotly.graph_objs as go
from dash import Dash, dcc, html, Input, Output
import dash_bootstrap_components as dbc
from openpyxl import load_workbook

# ======================
# CARGA DE DATOS DESDE TABLA DE EXCEL
# ======================
import os

excel_file = os.path.join(os.path.dirname(__file__), "estacion_metereologica.xlsx")
sheet_name = "Sheet1"

try:
    print(f"Cargando hoja '{sheet_name}' desde el archivo: {excel_file}")
    df = pd.read_excel(
        excel_file,
        sheet_name=sheet_name,
        engine="openpyxl"
    )
    print("Datos cargados correctamente desde Sheet1.")
except Exception as e:
    print(f"Error al cargar los datos: {e}")
    df = pd.DataFrame()


# ======================
# PREPARACIÓN DE DATOS
# ======================
df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
df = df.dropna(subset=['Fecha'])
df = df.sort_values('Fecha')
df['Año'] = df['Fecha'].dt.year
df['Mes'] = df['Fecha'].dt.month
df['Semana'] = df['Fecha'].dt.isocalendar().week

# ======================
# FUNCIONES
# ======================
def detectar_tramos(data):
    data = data.copy()
    data['dentro_rango'] = data['Humedad Relativa (%)'].between(90, 95)
    data['tramo_id'] = None
    tramo_actual = -1
    i = 0

    while i < len(data):
        if data['dentro_rango'].iloc[i]:
            tramo_inicio = i
            while i < len(data) and data['dentro_rango'].iloc[i]:
                i += 1
            tramo_fin = i
            if tramo_fin - tramo_inicio >= 4:
                tramo_actual += 1
                data.loc[data.index[tramo_inicio:tramo_fin], 'tramo_id'] = tramo_actual
        else:
            i += 1
    return data

def crear_tramos_plotly(data):
    tramos = []
    inicio = 0
    while inicio < len(data):
        estado_actual = data['secuencia_valida'].iloc[inicio]
        fin = inicio
        while fin < len(data) and data['secuencia_valida'].iloc[fin] == estado_actual:
            fin += 1
        color = 'rgba(255,0,0,0.9)' if estado_actual else 'rgba(0,0,255,0.6)'
        tramos.append(
            go.Scatter(
                x=data['Fecha'].iloc[inicio:fin],
                y=data['Humedad Relativa (%)'].iloc[inicio:fin],
                mode='lines',
                line=dict(color=color, width=2),
                name='Alerta' if estado_actual else 'Normal',
                showlegend=False
            )
        )
        inicio = fin
    return tramos

# ======================
# APP DASH
# ======================
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# ... (toda la parte inicial del código se mantiene igual)

# ... (todo tu código previo se mantiene igual hasta la línea app.layout = ...)

app.layout = dbc.Container([
    html.H2("Indicador de Humedad", className="mt-4"),

    dbc.Alert(
        [
            html.P("A partir de la 5ta hora consecutiva con valores entre 90% y 95% se muestrarán las horas acumuladas."),
            html.P("• 5 a 8 horas consecutivas entre valores 90% y 95% → línea amarilla"),
            html.P("• 9 o más horas consecutivas entre valores 90% y 95% → línea roja"),
            html.P("• Valores de humedad menores al 90% → línea azul")
        ],
        color="info",
        style={"fontSize": "16px"}
    ),

    dbc.Row([
        dbc.Col([
            html.Label("Año"),
            dcc.Dropdown(
                id='filtro-año',
                options=[{'label': str(a), 'value': a} for a in sorted(df['Año'].unique())],
                multi=True,
                placeholder="Selecciona uno o varios años"
            ),
        ], md=4),
        dbc.Col([
            html.Label("Mes"),
            dcc.Dropdown(
                id='filtro-mes',
                options=[{'label': str(m), 'value': m} for m in sorted(df['Mes'].unique())],
                multi=True,
                placeholder="Selecciona uno o varios meses"
            ),
        ], md=4),
        dbc.Col([
            html.Label("Semana"),
            dcc.Dropdown(
                id='filtro-semana',
                options=[{'label': str(s), 'value': s} for s in sorted(df['Semana'].unique())],
                multi=True,
                placeholder="Selecciona una o varias semanas"
            ),
        ], md=4),
    ]),
    dcc.Graph(id='grafico-humedad'),
], fluid=True)

# ... (resto de tu código se mantiene sin cambios)


@app.callback(
    Output('grafico-humedad', 'figure'),
    [Input('filtro-año', 'value'),
     Input('filtro-mes', 'value'),
     Input('filtro-semana', 'value')]
)
def actualizar_grafico(años, meses, semanas):
    df_filtrado = df.copy()

    if años:
        df_filtrado = df_filtrado[df_filtrado['Año'].isin(años)]
    if meses:
        df_filtrado = df_filtrado[df_filtrado['Mes'].isin(meses)]
    if semanas:
        df_filtrado = df_filtrado[df_filtrado['Semana'].isin(semanas)]

    if not años and not meses and not semanas:
        año_actual = df['Año'].max()
        ultima_semana = df[df['Año'] == año_actual]['Semana'].max()
        df_filtrado = df[(df['Año'] == año_actual) & (df['Semana'] == ultima_semana)]

    print(f"Filas seleccionadas: {len(df_filtrado)}")

    # ... (todo lo que sigue en tu función se mantiene exactamente igual)


    if df_filtrado.empty:
        fig = go.Figure()
        fig.update_layout(title='No hay datos para ese rango')
        return fig

    df_procesado = detectar_tramos(df_filtrado)
    tramos = []
    i = 0
    while i < len(df_procesado):
        tramo_id = df_procesado['tramo_id'].iloc[i]
        j = i
        while j < len(df_procesado) and df_procesado['tramo_id'].iloc[j] == tramo_id:
            j += 1

        if pd.notna(tramo_id):
            tramo_data = df_procesado.iloc[i:j]
            n = len(tramo_data)
            inicio_tramo = tramo_data['Fecha'].iloc[0]
            horas = [(f"{int((f - inicio_tramo).total_seconds() // 3600) + 1}h") for f in tramo_data['Fecha']]
            humedad = tramo_data['Humedad Relativa (%)'].round(1).astype(str)

            if 5 <= n <= 8:
                color = 'rgba(255, 255, 0, 0.9)'
            elif n > 8:
                color = 'rgba(255, 0, 0, 0.9)'
            else:
                color = 'rgba(0, 0, 255, 0.6)'

            tramos.append(
                go.Scatter(
                    x=tramo_data['Fecha'],
                    y=tramo_data['Humedad Relativa (%)'],
                    mode='lines+markers+text',
                    line=dict(color=color, width=2),
                    showlegend=False,
                    text=humedad,
                    textposition="top center"
                )
            )
            tramos.append(
                go.Scatter(
                    x=tramo_data['Fecha'],
                    y=tramo_data['Humedad Relativa (%)'],
                    mode='text',
                    text=horas,
                    textposition="bottom center",
                    showlegend=False,
                    hoverinfo='skip'
                )
            )
        else:
            tramo_data = df_procesado.iloc[i:j] if j > i else df_procesado.iloc[i:i+1]
            color = 'rgba(0, 0, 255, 0.6)'
            text = tramo_data['Humedad Relativa (%)'].round(1).astype(str)

            tramos.append(
                go.Scatter(
                    x=tramo_data['Fecha'],
                    y=tramo_data['Humedad Relativa (%)'],
                    mode='lines+markers+text',
                    line=dict(color=color, width=2),
                    showlegend=False,
                    text=text,
                    textposition="top center"
                )
            )
        i = j if j > i else i + 1

    fig = go.Figure(data=tramos)
    fig.update_layout(
        title="Indicador de Humedad",
        xaxis_title="Fecha y Hora",
        yaxis_title="Humedad Relativa (%)",
        height=500
    )
    return fig

if __name__ == '__main__':
    app.run_server(debug=False, host='0.0.0.0', port=10000)
