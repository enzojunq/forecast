from datetime import datetime
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import statsmodels.api as sm
import streamlit as st
import pydeck as pdk
import plotly.express as px

# wide mode
st.set_page_config(layout="wide")

coordenadas = ['-7.104935045442301, -49.944180202040144',
'-17.81789104369522, -50.942953679730714',
'-16.740554665717063, -49.276168266190844',
'-7.198426368757455, -48.21708964909973',
'-16.360169556284408, -49.4988302886782',
'-19.723173398308386, -50.18948435846853',
'-17.565426842916985, -52.553537306761335',
'-18.167783142193848, -47.94259399323886',
'-23.41995531136246, -51.96955386439833',
'-10.183440463502905, -48.347687420261465',
'-16.659333957995464, -49.25944472026559',
'-5.369181546566486, -49.129346576082725',
'-16.62918753942868, -49.27869531546405',
'-15.590031024792644, -56.12064987792857',
'-12.088367899790967, -45.793093020259704',
'-16.079055308522197, -47.984471250870925',
'-16.47225656117028, -54.60812963379254',
'-11.861400305416547, -55.48914936442164',
'-22.34229310858127, -49.04927403559247',
'-15.885483018027692, -52.27315128647707',
'-19.592067585500125, -46.93716057290371',
'-5.512368257229494, -47.47913701716634',
'-22.9781934494537, -49.88120454061135',
'-18.957255137052723, -48.277667811723276',
'-7.525127162824259, -46.04684441350707',
'-12.537929126127747, -55.73433713829772',
'-6.06461329939856, -49.91121224234016',
'-16.334401271828778, -48.95167681352015',
'-3.2099526559781393, -52.21466352882893',
'-12.149395895040984, -44.99198140179163',
'-17.88396874378835, -51.73322165765797',
'-17.81785018686167, -50.9428946711879',
'-19.496743849911876, -42.56610612701848',
'-15.42149911589068, -54.31703327710728',
'-16.702868862226328, -49.293944772978165',
'-10.9108296267219, -37.04909392453898']

filiais = ['TXC XINGUARA - PA',
 'TATIANE - TXC RIO VERDE - GO',
 'TXC BURITI',
 'TXC ARAGUAINA - TO',
 'MB STORE - TXC INHUMAS - GO',
 'TXC ITURAMA - MG',
 'SH STORE - TXC MINEIROS - GO',
 'TXC CATALAO - GO',
 'TXC MARINGA - PR',
 'TXC PALMAS - TO',
 'TXC ARAGUAIA',
 'TXC MARABA - PA',
 'TXC PASSEIO',
 'TXC CUIABA - MT',
 'TXC LEM - BA',
 'TXC VALPARAISO - GO',
 'TXC RONDONOPOLIS - MT',
 'TXC SINOP - MT',
 'TXC BAURU - SP',
 'TXC BARRA - MT',
 'TXC ARAXA - MG',
 'TXC IMPERATRIZ - MA',
 'TXC OURINHOS - SP',
 'TXC UBERLANDIA - MG',
 'TXC BALSAS - MA',
 'TXC SORRISO - MT',
 'TXC PARAUAPEBAS - PA',
 'TXC - Anápolis',
 'TXC ALTAMIRA - PA',
 'TXC BARREIRAS - BA',
 'TXC JATAI - GO',
 'HS STORE - TXC CENTRO RIO VERDE - GO',
 'TXC IPATINGA - MG',
 'TXC - Primavera',
 'TXC - Canaã',
 'TXC - Aracaju']

# Criando um DataFrame a partir dos dados fornecidos
df_filial_coordenadas = pd.DataFrame({
    'Filial': filiais,
    'Coordenadas': coordenadas
})

# Dividindo a coluna de coordenadas em duas colunas separadas
df_filial_coordenadas[['latitude', 'longitude']] = df_filial_coordenadas['Coordenadas'].str.split(', ', expand=True)

# Convertendo para numérico
df_filial_coordenadas['latitude'] = pd.to_numeric(df_filial_coordenadas['latitude'])
df_filial_coordenadas['longitude'] = pd.to_numeric(df_filial_coordenadas['longitude'])


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
    
    # Calculando a quantidade de vendas por filial
    quantidade_vendas_por_filial = apenas_vendas.groupby('Franqueada').size().reset_index(name='Quantidade de Vendas')

    # Ordenando os resultados para ver as filiais com mais vendas no topo
    quantidade_vendas_por_filial = quantidade_vendas_por_filial.sort_values(by='Quantidade de Vendas', ascending=False)


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

    return lambda_value, vendas_por_dia, previsao_vendas, previsao_modelo,quantidade_vendas_por_filial

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
    lambda_value, vendas_por_dia, previsao_vendas,modelo,qnt_por_filial = calcular_previsao_vendas(sku_data, features, forecast, feriados)
    
    # Realizando a junção dos DataFrames
    vendas_coordenadas = pd.merge(qnt_por_filial, df_filial_coordenadas, 
                        left_on='Franqueada', right_on='Filial', how='inner')

    # Removendo a coluna duplicada 'Filial', já que 'Franqueada' e 'Filial' são equivalentes
    vendas_coordenadas.drop('Filial', axis=1, inplace=True)


    vendas_dia, vendas_mes, mapa_tab= st.tabs(["Vendas por Dia", "Vendas por Mês","Mapa de Filiais"])
    with vendas_dia:
        # Exibindo o valor de lambda
        # col1.success(f'lambda: {lambda_value:.4f}')

        # Filtros de data
        data_inicio = col2.date_input("Data de início", datetime(2023, 1, 1))
        data_fim = col2.date_input("Data de fim", datetime(2023, 12, 31))

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
        
        col11,col22 = st.columns(2)
        
        # Adicionando um seletor de data para escolher uma data específica
        data_escolhida = col11.date_input("Escolha uma data para ver a previsão de vendas", datetime.now())

        # Filtrando as previsões para a data escolhida
        previsao_especifica = previsao_vendas[previsao_vendas['Data'] == pd.to_datetime(data_escolhida)]

        # Verificando se há dados para a data selecionada e exibindo a previsão
        if not previsao_especifica.empty:
            venda_prevista = previsao_especifica['Forecast'].values[0]
            col22.metric(label="Previsão de Vendas", value=f"{venda_prevista:.2f} unidades")

        else:
            st.write("Não há previsão disponível para esta data.")
            
        
        # Adicionando um seletor de número de dias para a previsão
        dias_previsao = col11.number_input('Selecione o número de dias para previsão', step=1)

        # hoje
        hoje = datetime.now()
        
        # Calculando a data final baseada na data escolhida e no número de dias selecionados
        data_final_previsao = hoje + pd.Timedelta(days=dias_previsao - 0)
        print(data_escolhida)
        # Filtrando as previsões para o período selecionado
        previsoes_periodo = previsao_vendas[(previsao_vendas['Data'] >= pd.to_datetime(hoje)) &
                                            (previsao_vendas['Data'] <= pd.to_datetime(data_final_previsao))]

        # Calculando a soma das vendas previstas para o período
        total_vendas_previstas = previsoes_periodo['Forecast'].sum()

        # Exibindo a soma das vendas previstas para o período selecionado
        col22.metric(label=f"Previsão de Vendas para os próximos {dias_previsao} dias", value=f"{total_vendas_previstas:.2f} unidades")

    
    def calcular_wmape(vendas_reais, vendas_previstas):
        erro_absoluto = abs(vendas_reais - vendas_previstas)
        total_absoluto_erro = erro_absoluto.sum()
        total_vendas = vendas_reais.sum()
        wmape = total_absoluto_erro / total_vendas
        return wmape

    # Supondo que 'vendas_por_dia' tenha uma coluna 'Número de Vendas' para vendas reais
    # e 'previsao_modelo' tenha uma coluna 'Forecast' para vendas previstas
    # Certifique-se de que ambos os DataFrames estão alinhados por data antes de chamar a função
    wmape = calcular_wmape(vendas_por_dia['Número de Vendas'], modelo['Forecast'])
    print(f"WMAPE: {wmape:.5f}")
    
    
    with vendas_mes:
        # Supondo que 'Número de Vendas' é a coluna com os valores numéricos
        vendas_por_mes = vendas_por_dia.groupby(vendas_por_dia['Data'].dt.to_period("M"))['Número de Vendas'].sum().reset_index()
        previsao_por_mes = previsao_vendas.groupby(previsao_vendas['Data'].dt.to_period("M"))['Forecast'].sum().reset_index()

        # Converter 'Data' para formato de data
        vendas_por_mes['Data'] = vendas_por_mes['Data'].dt.to_timestamp()
        previsao_por_mes['Data'] = previsao_por_mes['Data'].dt.to_timestamp()

        # Criar DataFrame para o gráfico
        df_bar = pd.merge(vendas_por_mes, previsao_por_mes, on='Data', how='outer', suffixes=('_real', '_previsto'))

        # Criar o gráfico de barras
        fig_bar = px.line(df_bar, x='Data', y=['Número de Vendas', 'Forecast'],
                        labels={'value':'Número de Vendas', 'Data':'Mês'},
                        title="Comparação Mensal de Vendas Reais e Previstas")
        st.plotly_chart(fig_bar, use_container_width=True)
        
        col1, col2 = st.columns(2)
    
        # Adicionando um seletor de mês e ano
        mes_escolhido = col1.selectbox("Escolha o mês", range(1, 13), format_func=lambda x: datetime(1900, x, 1).strftime('%B'))
        ano_escolhido = 2024
        
        # Convertendo para o primeiro dia do mês escolhido
        data_escolhida = datetime(ano_escolhido, mes_escolhido, 1)
        
        # Filtrando as previsões para o mês escolhido
        previsao_especifica_mes = previsao_vendas[previsao_vendas['Data'].dt.year == ano_escolhido][previsao_vendas['Data'].dt.month == mes_escolhido]

        # Verificando se há dados para o mês selecionado e exibindo a previsão
        if not previsao_especifica_mes.empty:
            venda_prevista_mes = previsao_especifica_mes['Forecast'].sum()  # Soma de todas as previsões para o mês
            col2.metric(label=f"Previsão de Vendas para {data_escolhida.strftime('%B %Y')}", value=f"{venda_prevista_mes:.2f} unidades")
        else:
            col2.write("Não há previsão disponível para este mês.")
        
    with mapa_tab:
        
        
        # Organiza o DataFrame para obter as 5 maiores filiais
        top_5_vendas = vendas_coordenadas.sort_values(by='Quantidade de Vendas', ascending=False).head(5)

        # Configura o layout com duas colunas: mapa à esquerda, ranking à direita
        col_mapa, col_ranking = st.columns([3, 1])  # Ajusta as proporções conforme necessário

        with col_mapa:
            # Ajusta o raio proporcional à "Quantidade de Vendas"
            vendas_coordenadas['raio'] = vendas_coordenadas['Quantidade de Vendas'] * 500  # Ajuste conforme necessário

            # Configuração do mapa PyDeck
            mapa = pdk.Deck(
                map_style='mapbox://styles/mapbox/light-v9',
                initial_view_state=pdk.ViewState(
                    latitude=vendas_coordenadas['latitude'].mean(),
                    longitude=vendas_coordenadas['longitude'].mean(),
                    zoom=5,
                    pitch=0,
                ),
                layers=[
                    pdk.Layer(
                        "ScatterplotLayer",
                        data=vendas_coordenadas,
                        get_position="[longitude, latitude]",
                        get_radius="raio",
                        get_color="[200, 30, 0, 160]",
                        pickable=True,
                    ),
                ],
            )

            st.pydeck_chart(mapa, use_container_width=True)

        with col_ranking:
            st.write("Top 5 Filiais com Mais Vendas")
            st.table(top_5_vendas[['Franqueada', 'Quantidade de Vendas']])
