import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2

# Configurar a página do dashboard
st.set_page_config(page_title="Dashboard Comercial Geral", layout="wide")

# Adicionar o título
st.markdown("<h1 style='text-align: center; color: white;'>Dashboard Comercial Geral</h1>", unsafe_allow_html=True)

# Adicionar CSS para mudar o background e as fontes
st.markdown(
    """
    <style>
    body {
        background: linear-gradient(to bottom, black, #2b2b2b);
        font-family: 'Times New Roman', Times, serif;
    }
    .main {
        background: linear-gradient(to bottom, black, #2b2b2b);
        color: white;
        font-family: 'Times New Roman', Times, serif;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Configurar a conexão
conn = psycopg2.connect(
    dbname="DW_Frigovel",
    user="postgres",
    password="superusuario",
    host="localhost",
    port="5434"
)

# Consultar dados usando pandas diretamente
query = "select * from fato_posit_vendedor_semanal where ano::integer > 2023"
df = pd.read_sql(query, conn)

# ---- SIDEBAR ----
st.sidebar.header("Filtros:")

# Opções de filtro
anos = df["ano"].unique().tolist()
anos.insert(0, "Todos")
meses = df["mes"].unique().tolist()
meses.insert(0, "Todos")
apelidos = df["apelido"].unique().tolist()
apelidos.insert(0, "Todos")

# Filtros do sidebar
ano = st.sidebar.multiselect(
    "Selecione o ano:",
    options=anos,
    default="Todos"
)
mes = st.sidebar.multiselect(
    "Selecione o mês:",
    options=meses,
    default="Todos"
)
apelido = st.sidebar.multiselect(
    "Selecione o vendedor:",
    options=apelidos,
    default="Todos"  # Seleciona "Todos" por padrão
)

# Aplicar filtros de forma eficiente
if "Todos" in ano:
    ano = df["ano"].unique()
if "Todos" in mes:
    mes = df["mes"].unique()
if "Todos" in apelido:
    apelido = df["apelido"].unique()

df_filtered = df[df['ano'].isin(ano) & df['mes'].isin(mes) & df['apelido'].isin(apelido)]

# Calcular a soma total das vendas e a quantidade total
soma_total_vendas = df_filtered['valor_venda'].sum()
soma_total_quantidade = df_filtered['quantidade_venda'].sum()

# Formatar soma total da quantidade para duas casas decimais
soma_total_quantidade_formatado = f"{soma_total_quantidade:.2f}"

# Contar distintos id_participante e id_produto
count_distinct_participante = df_filtered['id_participante'].nunique()
count_distinct_produto = df_filtered['id_produto'].nunique()

# Agrupar e somar vendas e quantidade mês a mês
df_grouped = df_filtered.groupby('mes').agg({
    'valor_venda': 'sum',
    'quantidade_venda': 'sum'
}).reset_index()

# Agrupar e somar vendas mês a mês por vendedor
df_grouped_vendedor = df_filtered.groupby(['mes', 'apelido']).agg({
    'valor_venda': 'sum'
}).reset_index()

# Contar distintos id_participante por mes e apelido
df_participant_count = df_filtered.groupby(['mes', 'apelido'])['id_participante'].nunique().reset_index()

# Contar distintos produtos vendidos e clientes mês a mês
df_distinct_counts = df_filtered.groupby('mes').agg({
    'id_produto': pd.Series.nunique,
    'id_participante': pd.Series.nunique
}).reset_index()

# Renomear colunas para melhor clareza
df_distinct_counts.rename(columns={'id_produto': 'produtos_distintos', 'id_participante': 'clientes_distintos'}, inplace=True)

# Criar abas no dashboard
tab1, tab2 = st.tabs(["Dedo Duro", "Visão Geral"])

with tab1:
    st.header("Análise Dedo Duro")

    # Exibir os cards
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
            <div style="background-color:darkblue;padding:10px;border-radius:10px">
            <h2 style="color:white;text-align:center;font-family:'Times New Roman', Times, serif;">Vendas: R$ {soma_total_vendas:,.2f}</h2>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div style="background-color:darkgreen;padding:10px;border-radius:10px">
            <h2 style="color:white;text-align:center;font-family:'Times New Roman', Times, serif;">Quantidade: {soma_total_quantidade_formatado}</h2>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
            <div style="background-color:darkgoldenrod;padding:10px;border-radius:10px">
            <h2 style="color:black;text-align:center;font-family:'Times New Roman', Times, serif;">Clientes Distintos: {count_distinct_participante}</h2>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
            <div style="background-color:darkred;padding:10px;border-radius:10px">
            <h2 style="color:white;text-align:center;font-family:'Times New Roman', Times, serif;">Produtos Distintos: {count_distinct_produto}</h2>
            </div>
        """, unsafe_allow_html=True)

    # Criar layout 2x2 para gráficos
    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)

    # Adicionar gráficos
    with row1_col1:
        # Gráfico de linhas com a evolução de vendas por vendedor
        fig_line_combined = px.line(
            df_grouped_vendedor,
            x='mes',
            y='valor_venda',
            color='apelido',
            markers=True,
            title="Evolução de Vendas por Vendedor"
        )
        st.plotly_chart(fig_line_combined)

    with row1_col2:
        fig_pie = px.pie(
            df_filtered,
            names='apelido',
            values='valor_venda',
            title='Distribuição de Vendas por Vendedor'
        )
        st.plotly_chart(fig_pie)

    with row2_col1:
        # Gráfico de linhas com duas métricas
        fig_line = px.line(
            df_grouped,
            x='mes',
            y=['valor_venda', 'quantidade_venda'],
            markers=True,
            title="Soma de Valor de Venda e Quantidade por Mês"
        )
        st.plotly_chart(fig_line)

    with row2_col2:
        # Gráfico de linhas com contagem distinta de produtos vendidos e clientes mês a mês
        fig_distinct = px.line(
            df_distinct_counts,
            x='mes',
            y=['produtos_distintos', 'clientes_distintos'],
            markers=True,
            title="Contagem Distinta de Produtos Vendidos e Clientes por Mês"
        )
        st.plotly_chart(fig_distinct)

# Fechar a conexão
conn.close()
