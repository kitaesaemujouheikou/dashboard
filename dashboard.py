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
    dbname="DWBI_Frigovel",
    user="postgres",
    password="superusuario",
    host="host.docker.internal",
    port="5432"
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

#Aplicar filtros de forma eficiente
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


# Assegurar que os valores são números
soma_total_custo = float(df_filtered['valor_custo'].sum())
soma_total_contrib = float(df_filtered['contribuicao_marginal'].sum())

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


df_marcas = df_filtered.groupby(['marca']).agg({
    'valor_venda': 'sum',
    'peso_liquido': 'sum',
    'valor_custo': 'sum',
    'quantidade_venda': 'sum',
    'contribuicao_marginal': 'sum'
}).reset_index().sort_values(by='valor_venda', ascending=False)


# Criar dados para a nova tabela na aba "Dedo Duro"
df_cidade = df_filtered.groupby('cid_nome').agg({
    'id_participante': pd.Series.nunique,
    'quantidade_venda': 'sum',
    'peso_liquido': 'sum',
    'valor_venda': 'sum',
    'valor_custo': 'sum'
}).reset_index()

df_segmento = df_filtered.groupby('segmento').agg({
    'id_participante': pd.Series.nunique,
    'quantidade_venda': 'sum',
    'peso_liquido': 'sum',
    'valor_venda': 'sum',
    'valor_custo': 'sum'
}).reset_index()



# Calcular a relação venda/custo
df_cidade['venda_custo_ratio'] = ((df_cidade['valor_venda'] / df_cidade['valor_custo']) - 1) * 100
df_marcas['venda_custo_ratio'] = ((df_marcas['valor_venda'] / df_marcas['valor_custo']) - 1) * 100
df_segmento['venda_custo_ratio'] = ((df_segmento['valor_venda'] / df_segmento['valor_custo']) - 1) * 100




# Adicionar linha de totalizadores
totais = pd.DataFrame([{
    'cid_nome': 'Total',
    'id_participante': df_cidade['id_participante'].sum(),
    'quantidade_venda': df_cidade['quantidade_venda'].sum(),
    'peso_liquido': df_cidade['peso_liquido'].sum(),
    'valor_venda': df_cidade['valor_venda'].sum(),
    'valor_custo': df_cidade['valor_custo'].sum(),
    'venda_custo_ratio': df_cidade['venda_custo_ratio'].mean()  # Média da relação venda/custo
}])

# Adicionar linha de totalizadores
totaisMarcas = pd.DataFrame([{
    'marca': 'Total',
    'valor_venda': df_marcas['valor_venda'].sum(),
    'peso_liquido': df_marcas['peso_liquido'].sum(),
    'valor_custo': df_marcas['valor_custo'].sum(),
    'quantidade_venda': df_marcas['quantidade_venda'].sum(),
    'contribuicao_marginal': df_marcas['contribuicao_marginal'].sum(),
    'venda_custo_ratio': df_marcas['venda_custo_ratio'].mean()  # Média da relação venda/custo

}])
totaisMarcas = pd.DataFrame([{
    'marca': 'Total',
    'valor_venda': df_marcas['valor_venda'].sum(),
    'peso_liquido': df_marcas['peso_liquido'].sum(),
    'valor_custo': df_marcas['valor_custo'].sum(),
    'quantidade_venda': df_marcas['quantidade_venda'].sum(),
    'contribuicao_marginal': df_marcas['contribuicao_marginal'].sum(),
    'venda_custo_ratio': df_marcas['venda_custo_ratio'].mean()  # Média da relação venda/custo

}])

#---------
# Adicionar linha de totalizadores
totaisSegmento = pd.DataFrame([{
    'segmento': 'Total',
    'valor_venda': df_marcas['valor_venda'].sum(),
    'peso_liquido': df_marcas['peso_liquido'].sum(),
    'valor_custo': df_marcas['valor_custo'].sum(),
    'quantidade_venda': df_marcas['quantidade_venda'].sum(),
    'contribuicao_marginal': df_marcas['contribuicao_marginal'].sum(),
    'venda_custo_ratio': df_marcas['venda_custo_ratio'].mean()  # Média da relação venda/custo

}])




# Concatenar os dados das cidades com os totalizadores
df_cidade_total = pd.concat([df_cidade, totais], ignore_index=True)
df_marcas_total = pd.concat([df_marcas, totaisMarcas], ignore_index=True)
df_segmento_total = pd.concat([df_segmento, totaisSegmento], ignore_index=True)


# Renomear colunas para melhor clareza
df_cidade_total.rename(columns={'cid_nome': 'Cidade', 'id_participante': 'Clientes Distintos', 'quantidade_venda': 'Quantidade Vendida', 'peso_liquido': 'Peso Vendido', 'venda_custo_ratio': 'Venda/Custo (%)'}, inplace=True)

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

    # Criar layout 3x3 para gráficos
    row1_col1, row1_col2, row1_col3 = st.columns(3)
    row2_col1, row2_col2, row2_col3 = st.columns(3)
    row3_col1, row3_col2, row3_col3 = st.columns(3)

    # Adicionar gráficos no layout 3x3
    with row1_col1:
        # Gráfico de área com a evolução de vendas por vendedor
        fig_area_combined = px.area(
            df_grouped_vendedor,
            x='mes',
            y='valor_venda',
            color='apelido',
            title="Evolução de Vendas por Vendedor"
        )
        st.plotly_chart(fig_area_combined)

    with row1_col2:
        # Gráfico de área com soma de valor de venda e quantidade por mês
        fig_area = px.area(
            df_grouped,
            x='mes',
            y=['valor_venda', 'quantidade_venda'],
            title="Soma de Valor de Venda e Quantidade por Mês"
        )
        st.plotly_chart(fig_area)

    with row1_col3:
        fig_pie = px.pie(
            df_filtered,
            names='apelido',
            values='valor_venda',
            title='Distribuição de Vendas por Vendedor'
        )
        st.plotly_chart(fig_pie)

    with row2_col1:
        # Gráfico de donut com a contagem distinta de id_participante por supervisor
        df_participante_supervisor = df_filtered.groupby('supervisor')['id_participante'].nunique().reset_index()
        df_participante_supervisor = df_participante_supervisor.sort_values(by='id_participante', ascending=False)
        fig_donut = px.pie(
            df_participante_supervisor,
            names='supervisor',
            values='id_participante',
            title="Positivações por Supervisor",
            hole=0.4  # Isso cria o formato de donut
        )
        st.plotly_chart(fig_donut)

    with row2_col2:
        # Gráfico de barras com contagem distinta de id_participante por vendedor
        df_participante_vendedor = df_filtered.groupby('apelido')['id_participante'].nunique().reset_index()
        df_participante_vendedor = df_participante_vendedor.sort_values(by='id_participante', ascending=False)
        fig_bar = px.bar(
            df_participante_vendedor,
            x='apelido',
            y='id_participante',
            title="Positivações por Vendedor",
            labels={'apelido': 'Vendedor', 'id_participante': 'Clientes Distintos'}
        )
        st.plotly_chart(fig_bar)

    with row2_col3:
        # Gráfico de linhas com contagem distinta de produtos vendidos e clientes mês a mês
        fig_distinct = px.line(
            df_distinct_counts,
            x='mes',
            y=['produtos_distintos', 'clientes_distintos'],
            markers=True,
            title="Contagem Distinta de Produtos Vendidos e Clientes por Mês"
        )
        st.plotly_chart(fig_distinct)

    with row3_col1:
        # Exibir a tabela
        st.subheader("Tabela de Desempenho por Cidade")
        st.dataframe(df_cidade_total)

    with row3_col2:
        st.subheader("Tabela de Desempenho por Marcas")
        st.dataframe(df_marcas_total)
    
    with row3_col3:
        # Exibir a tabela
        st.subheader("Tabela Agregada por Segmento")
        st.dataframe(df_segmento_total)





with tab2:
    st.header("Custos e Contribuição")

    col5, col6 = st.columns(2)
    row1_col5, row1_col6 = st.columns(2)


    with col5:
        st.markdown(f"""
            <div style="background-color:darkblue;padding:10px;border-radius:10px">
            <h2 style="color:white;text-align:center;font-family:'Times New Roman', Times, serif;">Custo Total: R$ {soma_total_custo:,.2f}</h2>
            </div>
        """, unsafe_allow_html=True)

    with col6:
        st.markdown(f"""
            <div style="background-color:darkgreen;padding:10px;border-radius:10px">
            <h2 style="color:white;text-align:center;font-family:'Times New Roman', Times, serif;">Contribuição Marginal: R$ {soma_total_contrib:,.2f}</h2>
            </div>
        """, unsafe_allow_html=True)


  
# Fechar a conexão
conn.close()
