from datetime import datetime
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import statsmodels.api as sm
import streamlit as st

# wide mode
st.set_page_config(layout="wide")


def calcular_previsao_vendas(file_path, file_path_features, file_path_forecast, file_path_feriados):
    # Carregar os arquivos
    excel_data = file_path
    features_excel = pd.read_excel(file_path_features)
    forecast_excel = pd.read_excel(file_path_forecast)
    feriados_excel = pd.read_excel(file_path_feriados)

    # Filtrar as operações para 'S - Venda'
    apenas_vendas = excel_data[excel_data['Operação'] == 'S - Venda']

    # Criando um intervalo de datas e contagem de vendas por dia
    data_inicial = apenas_vendas['Data'].min()
    data_final = apenas_vendas['Data'].max()
    todas_datas = pd.date_range(start=data_inicial, end=data_final, freq='D')
    contagem_vendas = apenas_vendas.groupby('Data').size().reset_index(name='Número de Vendas')

    # Unindo as contagens de vendas com o DataFrame de todas as datas
    vendas_por_dia = pd.DataFrame(todas_datas, columns=['Data']).merge(contagem_vendas, on='Data', how='left')
    vendas_por_dia['Número de Vendas'].fillna(0, inplace=True)
    vendas_por_dia['Número de Vendas'] = vendas_por_dia['Número de Vendas'].astype(int)
    vendas_por_dia = vendas_por_dia[vendas_por_dia['Data'] >= '2022-01-01']
    vendas_por_dia = vendas_por_dia.reset_index(drop=True)

    # Função para realizar a regressão
    def regressao(x, y):
        x = sm.add_constant(x)  # Adicionando a constante
        modelo = sm.OLS(y, x)
        resultados = modelo.fit()
        return resultados

    # Preparando os dados para regressão e previsão
    features_for_regression = features_excel.drop('Data', axis=1).reset_index(drop=True)
    vendas_for_regression = vendas_por_dia['Número de Vendas'].reset_index(drop=True)

    # Treinando o modelo e fazendo previsões
    modelo = regressao(features_for_regression, vendas_for_regression)
    efeitos_passados = modelo.predict(sm.add_constant(features_for_regression))

    # Preparando colunas Alpha e Beta
    vendas = vendas_por_dia.copy()
    vendas['Alpha'] = vendas['Número de Vendas'] / efeitos_passados
    vendas['Beta'] = vendas['Data'].apply(lambda x: 0 if x in feriados_excel['FERIADOS'].values else 1)

    # Calcular Lambda
    lambda_value = vendas['Alpha'].sum() / vendas['Beta'].sum()
    
    previsao_modelo = pd.DataFrame()
    previsao_modelo['Forecast'] = efeitos_passados * lambda_value
    # Adicionando a coluna de Data
    previsao_modelo['Data'] = pd.date_range(start='2022-01-01', periods=len(previsao_modelo), freq='D')
    previsao_modelo = previsao_modelo[['Data', 'Forecast']]
    
    
    # Calculando a previsão de vendas
    features_forecast = forecast_excel.drop('Data', axis=1)
    efeitos_previsao = modelo.predict(sm.add_constant(features_forecast))

    previsao_vendas = pd.DataFrame()
    previsao_vendas['Forecast'] = efeitos_previsao * lambda_value

    # Adicionando a coluna de Data
    previsao_vendas['Data'] = pd.date_range(start='2024-01-01', periods=len(previsao_vendas), freq='D')
    previsao_vendas = previsao_vendas[['Data', 'Forecast']]

    return lambda_value, vendas_por_dia, previsao_vendas, previsao_modelo

# Inicializando a aplicação Streamlit
st.title("Forecast Bubup")



# Lista de produtos para seleção
col1, col2 = st.columns(2)




# Upload do arquivo SKU
uploaded_file = col1.file_uploader(f"Fazer upload do arquivo de vendas", type="xlsx")

# Se um arquivo for carregado, processá-lo
if uploaded_file is not None:
    # Lendo o arquivo carregado
    sku_data = pd.read_excel(uploaded_file)

    # Caminhos para os outros arquivos necessários
    features = 'features.xlsx'
    forecast = 'forecast.xlsx'
    feriados = 'feriados.xlsx'

    # Calculando a previsão de vendas para o produto selecionado
    lambda_value, vendas_por_dia, previsao_vendas,modelo = calcular_previsao_vendas(sku_data, features, forecast, feriados)

    # Exibindo o valor de lambda
    col1.success(f'lambda: {lambda_value:.4f}')

    # Filtros de data
    data_inicio = col2.date_input("Data de início", datetime(2023, 1, 1))
    data_fim = col2.date_input("Data de fim", datetime(2024, 12, 31))

    # Filtrando as vendas atuais, previsões e previsões do Excel
    vendas_filtradas = vendas_por_dia[(vendas_por_dia['Data'] >= pd.to_datetime(data_inicio)) &
                                      (vendas_por_dia['Data'] <= pd.to_datetime(data_fim))]
    forecast_excel_filtrado = previsao_vendas[(previsao_vendas['Data'] >= pd.to_datetime(data_inicio)) &
                                              (previsao_vendas['Data'] <= pd.to_datetime(data_fim))]
    modelo_filtrado = modelo[(modelo['Data'] >= pd.to_datetime(data_inicio)) &
                                              (modelo['Data'] <= pd.to_datetime(data_fim))]

    # Criando o gráfico interativo com Plotly
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=vendas_filtradas['Data'], y=vendas_filtradas['Número de Vendas'],
                             mode='lines', name='Vendas Atuais'))
    fig.add_trace(go.Scatter(x=modelo_filtrado['Data'], y=modelo_filtrado['Forecast'],
                             mode='lines+markers', name='Modelo', line=dict(dash='dot')))
    fig.add_trace(go.Scatter(x=forecast_excel_filtrado['Data'], y=forecast_excel_filtrado['Forecast'],
                             mode='lines+markers', name='Previsão', line=dict(dash='dot')))

    fig.update_layout(title='Vendas Atuais vs Previsão de Vendas',
                      xaxis_title='Data',
                      yaxis_title='Vendas',
                      hovermode='x unified')

    st.plotly_chart(fig, use_container_width=True)
