import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# --- CONFIGURAÇÃO DA PÁGINA E ESTÉTICA ---
st.set_page_config(page_title="Dashboard Logístico", layout="wide", page_icon="🚛")

st.markdown("""
<style>
    .main-title { 
        font-size: 3.5rem; 
        font-weight: 800; 
        color: #1E3A8A; 
        margin-bottom: 10px; 
        text-align: center; 
    }
    .month-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1F2937;
        text-align: center;
        margin-top: 15px;
        margin-bottom: 5px;
    }
    .caption-header {
        font-size: 1.2rem;
        color: #6B7280;
        text-align: center;
        margin-bottom: 25px;
    }
    div[data-testid="metric-container"] { 
        background-color: #F9FAFB; 
        border-radius: 8px; 
        padding: 15px; 
        border: 1px solid #E5E7EB;
        text-align: center;
    }
    div[data-testid="metric-container"] > div {
        justify-content: center;
    }
</style>
""", unsafe_allow_html=True)

# TÍTULO PRINCIPAL
st.markdown('<p class="main-title">🚛 Acompanhamento Logístico 2026</p>', unsafe_allow_html=True)

def format_brl(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

MESES_PT = {
    1: "JANEIRO", 2: "FEVEREIRO", 3: "MARÇO", 4: "ABRIL",
    5: "MAIO", 6: "JUNHO", 7: "JULHO", 8: "AGOSTO",
    9: "SETEMBRO", 10: "OUTUBRO", 11: "NOVEMBRO", 12: "DEZEMBRO"
}

# --- CARREGAMENTO E TRATAMENTO DOS DADOS ---
@st.cache_data
def load_data():
    try:
        df = pd.read_excel("Indicadores_2.xlsx")
        df.columns = df.columns.astype(str).str.strip().str.upper()
        
        df['Carga'] = df['NºCARGA'] if 'NºCARGA' in df.columns else df.iloc[:, 4]
        df['Data'] = pd.to_datetime(df.iloc[:, 81], errors='coerce') if len(df.columns) > 81 else pd.NaT

        df['Mes_LD'] = df.iloc[:, 26] if len(df.columns) > 26 else pd.NA
        df['Receita_RS'] = df.iloc[:, 27] if len(df.columns) > 27 else pd.NA
        df['Ocupacao'] = df.iloc[:, 59] if len(df.columns) > 59 else pd.NA
        df['Frete_RS'] = df.iloc[:, 94] if len(df.columns) > 94 else pd.NA
        df['Frete_Receita_Pct'] = df.iloc[:, 63] if len(df.columns) > 63 else pd.NA
        df['Cliente'] = df.iloc[:, 11] if len(df.columns) > 11 else pd.NA
        df['Tabela_Transp'] = df.iloc[:, 46] if len(df.columns) > 46 else pd.NA
        df['Transportadora'] = df.iloc[:, 41] if len(df.columns) > 41 else pd.NA
        df['Perfil_Embarque'] = df.iloc[:, 39] if len(df.columns) > 39 else pd.NA
        df['Perfil_Veiculo'] = df.iloc[:, 42] if len(df.columns) > 42 else pd.NA
        
        cols_to_fill = ['Data', 'Mes_LD', 'Ocupacao', 'Frete_Receita_Pct', 'Frete_RS', 'Cliente', 'Tabela_Transp', 'Transportadora', 'Perfil_Embarque', 'Perfil_Veiculo']
        for col in cols_to_fill:
            df[col] = df[col].replace(["N/D", "NAN", "nan", " ", ""], pd.NA)
            
        df[cols_to_fill] = df.groupby('Carga')[cols_to_fill].transform(lambda x: x.ffill().bfill())

        df['Ocupacao'] = pd.to_numeric(df['Ocupacao'], errors='coerce').fillna(0)
        df['Frete_Receita_Pct'] = pd.to_numeric(df['Frete_Receita_Pct'], errors='coerce').fillna(0)
        df['Receita_RS'] = pd.to_numeric(df['Receita_RS'], errors='coerce').fillna(0)
        df['Frete_RS'] = pd.to_numeric(df['Frete_RS'], errors='coerce').fillna(0)

        df['Mes_LD'] = df['Mes_LD'].astype(str).str.strip().str.upper().fillna("N/D")
        
        return df
    except Exception as e:
        st.error(f"Erro ao processar a base de dados: {e}")
        return pd.DataFrame()

df_raw = load_data()
if df_raw.empty:
    st.stop()

ordem_meses = { "JANEIRO": 1, "FEVEREIRO": 2, "MARÇO": 3, "MARCO": 3, "ABRIL": 4, "MAIO": 5, "JUNHO": 6, "JULHO": 7, "AGOSTO": 8, "SETEMBRO": 9, "OUTUBRO": 10, "NOVEMBRO": 11, "DEZEMBRO": 12 }
meses_disponiveis = [str(m) for m in df_raw['Mes_LD'].unique() if str(m) not in ["NAN", "N/D", "nan", "<NA>"]]
meses_ordenados = sorted(meses_disponiveis, key=lambda x: ordem_meses.get(x, 99))

mes_atual_nome = MESES_PT.get(datetime.now().month, "")
indice_default_mes = 0
if mes_atual_nome in meses_ordenados:
    indice_default_mes = meses_ordenados.index(mes_atual_nome)

# --- BARRA LATERAL ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2769/2769339.png", width=110)
    
    # RESERVA UM ESPAÇO NO TOPO PARA O BOTÃO DE EXPORTAÇÃO
    topo_sidebar = st.container()
    st.markdown("---")
    
    st.markdown("### 📅 Período")
    anos = df_raw['Data'].dt.year.dropna().astype(int).unique().tolist() if df_raw['Data'].notna().any() else [2026]
    ano_selecionado = st.selectbox("Selecione o Ano", sorted(anos, reverse=True))
    mes_selecionado = st.selectbox("Mês (Lead Time)", meses_ordenados, index=indice_default_mes)

    st.markdown("### ⚙️ Operacional")
    perfis_carga = ["TODOS"] + sorted([str(p) for p in df_raw['Perfil_Embarque'].dropna().unique() if str(p) not in ["N/D", "NAN"]])
    transportadoras = ["TODOS"] + sorted([str(t) for t in df_raw['Transportadora'].dropna().unique() if str(t) not in ["N/D", "NAN"]])
    perfis_veiculo = ["TODOS"] + sorted([str(v) for v in df_raw['Perfil_Veiculo'].dropna().unique() if str(v) not in ["N/D", "NAN"]])

    perfil_carga_sel = st.selectbox("Perfil da Carga", perfis_carga, index=0)
    transportadora_sel = st.selectbox("Transportadora", transportadoras)
    perfil_veic_sel = st.selectbox("Perfil do Veículo", perfis_veiculo)

# --- APLICAÇÃO DOS FILTROS ---
df_filtrado = df_raw.copy()
if perfil_carga_sel != "TODOS": df_filtrado = df_filtrado[df_filtrado['Perfil_Embarque'] == perfil_carga_sel]
if transportadora_sel != "TODOS": df_filtrado = df_filtrado[df_filtrado['Transportadora'] == transportadora_sel]
if perfil_veic_sel != "TODOS": df_filtrado = df_filtrado[df_filtrado['Perfil_Veiculo'] == perfil_veic_sel]

df_mes_raw = df_filtrado[df_filtrado['Mes_LD'] == mes_selecionado]

# Cálculos Iniciais
rec_mes = df_mes_raw['Receita_RS'].sum()
receita_por_carga = df_mes_raw.groupby('Carga')['Receita_RS'].sum().reset_index()

df_mes_cargas = df_mes_raw.drop_duplicates(subset=['Carga']).copy()
df_mes_cargas = df_mes_cargas.drop(columns=['Receita_RS']).merge(receita_por_carga, on='Carga', how='left')

ocup_mes = df_mes_cargas['Ocupacao'].mean() if not df_mes_cargas.empty else 0
fr_mes = df_mes_cargas['Frete_Receita_Pct'].mean() if not df_mes_cargas.empty else 0

# ====================================================================================
# LÓGICA DE EXPORTAÇÃO DO RELATÓRIO HTML (GERADO DIRETO NA MEMÓRIA)
# ====================================================================================
def gerar_html_infografico():
    if df_mes_cargas['Data'].dropna().empty:
        return "<h1>Não há datas preenchidas para gerar o relatório</h1>"

    # Preparar Dados
    df_frete = df_mes_cargas.dropna(subset=['Data']).groupby('Data')['Frete_Receita_Pct'].mean().reset_index().sort_values('Data')
    df_frete['Data_Str'] = df_frete['Data'].dt.strftime('%d/%m')

    df_ocup = df_mes_cargas.dropna(subset=['Data']).groupby('Data')['Ocupacao'].mean().reset_index().sort_values('Data')
    df_ocup['Data_Str'] = df_ocup['Data'].dt.strftime('%d/%m')

    ultima_data = df_mes_cargas['Data'].dropna().max()
    ultima_data_str = ultima_data.strftime('%d/%m/%Y')
    
    # Pegar os dados do último dia e ordenar
    df_ultimo_dia_frete = df_mes_cargas[df_mes_cargas['Data'] == ultima_data].sort_values(by='Frete_Receita_Pct', ascending=False)
    df_ultimo_dia_ocup = df_mes_cargas[df_mes_cargas['Data'] == ultima_data].sort_values(by='Ocupacao', ascending=True)

    # --- CÁLCULO DINÂMICO DE ALTURAS PARA EVITAR BARRA DE ROLAGEM ---
    qtd_linhas_frete = max(1, len(df_ultimo_dia_frete))
    qtd_linhas_ocup = max(1, len(df_ultimo_dia_ocup))

    altura_kpi = 150
    altura_grafico = 450
    # 50px de cabeçalho + 35px por cada linha de dados
    altura_tabela_frete = 50 + (35 * qtd_linhas_frete)
    altura_tabela_ocup = 50 + (35 * qtd_linhas_ocup)

    # Altura total do infográfico + um respiro (padding) de 250px
    altura_total_px = altura_kpi + (2 * altura_grafico) + altura_tabela_frete + altura_tabela_ocup + 250

    # Proporções em porcentagem para o Plotly renderizar os quadros perfeitamente
    p_kpi = altura_kpi / altura_total_px
    p_g1 = altura_grafico / altura_total_px
    p_t1 = altura_tabela_frete / altura_total_px
    p_g2 = altura_grafico / altura_total_px
    p_t2 = altura_tabela_ocup / altura_total_px

    # NOVO LAYOUT COM ALTURAS DINÂMICAS
    fig = make_subplots(
        rows=5, cols=1, 
        vertical_spacing=0.04, 
        row_heights=[p_kpi, p_g1, p_t1, p_g2, p_t2],
        specs=[[{"type": "table"}], [{"type": "xy"}], [{"type": "table"}], [{"type": "xy"}], [{"type": "table"}]],
        subplot_titles=(
            f"📊 NÚMEROS ACUMULADOS - {mes_selecionado.upper()}",
            "💰 TENDÊNCIA: % FRETE / RECEITA POR DIA",
            f"🔎 DETALHAMENTO DO ÚLTIMO DIA ({ultima_data_str}) - PIORES CUSTOS DE FRETE",
            "🚚 TENDÊNCIA: % DE OCUPAÇÃO POR DIA",
            f"⚠️ DETALHAMENTO DO ÚLTIMO DIA ({ultima_data_str}) - PIORES OCUPAÇÕES"
        )
    )

    # 1. KPIs
    fig.add_trace(go.Table(
        header=dict(values=["💵 Receita Líquida", "🚚 % de Ocupação", "💰 % Frete / Receita"],
                    fill_color='#1E3A8A', align='center', font=dict(color='white', size=18)),
        cells=dict(values=[[format_brl(rec_mes)], [f"{ocup_mes*100:.1f}%"], [f"{fr_mes*100:.2f}%"]],
                   fill_color='#F9FAFB', align='center', font=dict(color='#0F172A', size=22, family="Arial Black"), height=40)
    ), row=1, col=1)

    # 2. Gráfico Frete
    fig.add_trace(go.Bar(x=df_frete['Data_Str'], y=df_frete['Frete_Receita_Pct'], text=df_frete['Frete_Receita_Pct'].apply(lambda x: f"{x*100:.1f}%"), textposition='outside', marker_color='#0F172A'), row=2, col=1)
    fig.add_hline(y=0.095, line_dash="dash", line_color="red", row=2, col=1, exclude_empty_subplots=False)
    fig.add_hline(y=fr_mes, line_dash="dot", line_color="#2563EB", row=2, col=1, exclude_empty_subplots=False)

    # 3. Tabela do Último Dia - Frete (Sem barra de rolagem)
    if not df_ultimo_dia_frete.empty:
        fig.add_trace(go.Table(
            header=dict(values=["Cliente", "Transportadora", "Tabela Transp.", "Perfil", "Veículo", "% Frete", "Receita (R$)"], fill_color='#1E3A8A', align='left', font=dict(color='white', size=14)),
            cells=dict(
                values=[
                    df_ultimo_dia_frete['Cliente'].astype(str), df_ultimo_dia_frete['Transportadora'].astype(str), df_ultimo_dia_frete['Tabela_Transp'].astype(str),
                    df_ultimo_dia_frete['Perfil_Embarque'].astype(str), df_ultimo_dia_frete['Perfil_Veiculo'].astype(str),
                    df_ultimo_dia_frete['Frete_Receita_Pct'].apply(lambda x: f"{x*100:.2f}%"), df_ultimo_dia_frete['Receita_RS'].apply(format_brl)
                ],
                fill_color='#F9FAFB', align='left', font=dict(color='#0F172A', size=12), height=35 # Altura fixa da célula forçando a expansão
            )
        ), row=3, col=1)

    # 4. Gráfico Ocupação
    fig.add_trace(go.Bar(x=df_ocup['Data_Str'], y=df_ocup['Ocupacao'], text=df_ocup['Ocupacao'].apply(lambda x: f"{x*100:.1f}%"), textposition='outside', marker_color='#10B981'), row=4, col=1)
    fig.add_hline(y=0.90, line_dash="dash", line_color="red", row=4, col=1, exclude_empty_subplots=False)
    fig.add_hline(y=ocup_mes, line_dash="dot", line_color="#059669", row=4, col=1, exclude_empty_subplots=False)

    # 5. Tabela do Último Dia - Ocupação (Sem barra de rolagem)
    if not df_ultimo_dia_ocup.empty:
        fig.add_trace(go.Table(
            header=dict(values=["Cliente", "Transportadora", "Tabela Transp.", "Perfil", "Veículo", "% Ocupação", "Receita (R$)"], fill_color='#065F46', align='left', font=dict(color='white', size=14)),
            cells=dict(
                values=[
                    df_ultimo_dia_ocup['Cliente'].astype(str), df_ultimo_dia_ocup['Transportadora'].astype(str), df_ultimo_dia_ocup['Tabela_Transp'].astype(str),
                    df_ultimo_dia_ocup['Perfil_Embarque'].astype(str), df_ultimo_dia_ocup['Perfil_Veiculo'].astype(str),
                    df_ultimo_dia_ocup['Ocupacao'].apply(lambda x: f"{x*100:.1f}%"), df_ultimo_dia_ocup['Receita_RS'].apply(format_brl)
                ],
                fill_color='#F9FAFB', align='left', font=dict(color='#0F172A', size=12), height=35 # Altura fixa da célula forçando a expansão
            )
        ), row=5, col=1)

    # Aplica a altura TOTAL calculada dinamicamente
    fig.update_layout(height=altura_total_px, width=1200, showlegend=False, title_text=f"🚛 RELATÓRIO LOGÍSTICO EXECUTIVO - {mes_selecionado}", title_x=0.5, title_font_size=28, title_font_color='#1E3A8A', plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="#FFFFFF")
    
    fig.update_yaxes(tickformat='.1%', row=2, col=1)
    fig.update_yaxes(tickformat='.1%', row=4, col=1)
    fig.update_xaxes(type='category', row=2, col=1)
    fig.update_xaxes(type='category', row=4, col=1)
    
    return fig.to_html(full_html=True, include_plotlyjs='cdn')

# --- INSERINDO O BOTÃO NO TOPO DA BARRA LATERAL ---
with topo_sidebar:
    st.markdown("### 📩 Exportar para E-mail")
    html_gerado = gerar_html_infografico()
    st.download_button(
        label="📥 Baixar Relatório (HTML)",
        data=html_gerado,
        file_name=f"Relatorio_{mes_selecionado}.html",
        mime="text/html",
        use_container_width=True,
        type="primary"
    )
    st.caption("Baixe o arquivo, abra no navegador e copie para o e-mail!")

# ====================================================================================
# EXIBIÇÃO CABEÇALHO DO PAINEL NA TELA
# ====================================================================================
st.markdown(f'<p class="month-header">{mes_selecionado.title()} de {ano_selecionado}</p>', unsafe_allow_html=True)
st.markdown(f'<p class="caption-header">Cargas carregadas: {len(df_mes_cargas)}</p>', unsafe_allow_html=True)

with st.container(border=True):
    col1, col2, col3 = st.columns(3) 
    with col1: st.metric(label="💵 Receita Líquida", value=format_brl(rec_mes))
    with col2: st.metric(label="🚚 % de Ocupação", value=f"{ocup_mes*100:.1f}%")
    with col3: st.metric(label="💰 % Frete / Receita", value=f"{fr_mes*100:.2f}%")

st.write("") 

# --- GRÁFICOS INTERATIVOS DA TELA ---
with st.container(border=True):
    if not df_mes_cargas.empty and df_mes_cargas['Data'].notna().any():
        df_tendencia_frete = df_mes_cargas.dropna(subset=['Data']).groupby('Data')['Frete_Receita_Pct'].mean().reset_index().sort_values('Data')
        df_tendencia_frete['Data_Str'] = df_tendencia_frete['Data'].dt.strftime('%d/%m')
        
        fig_bar_frete = px.bar(df_tendencia_frete, x='Data_Str', y='Frete_Receita_Pct', title="% Frete / Receita", text=df_tendencia_frete['Frete_Receita_Pct'].apply(lambda x: f"{x*100:.1f}%"))
        fig_bar_frete.add_hline(y=0.095, line_dash="dash", line_color="red")
        fig_bar_frete.add_hline(y=fr_mes, line_dash="dot", line_color="#2563EB", annotation_text=f"Média Mês: {fr_mes*100:.2f}%")
        fig_bar_frete.update_layout(title_x=0.5, template="plotly_white", yaxis_tickformat='.1%', hovermode="x unified", clickmode='event+select')
        fig_bar_frete.update_traces(marker_color='#0F172A', textposition='outside')
        
        selected_frete = st.plotly_chart(fig_bar_frete, use_container_width=True, on_select="rerun")
        
        if selected_frete and selected_frete.get("selection") and selected_frete["selection"]["points"]:
            dia_str = selected_frete["selection"]["points"][0]["x"]
            df_dia_f = df_mes_cargas[df_mes_cargas['Data'].dt.strftime('%d/%m') == dia_str].sort_values(by='Frete_Receita_Pct', ascending=False)
            st.markdown(f"#### 🔎 Detalhamento: {dia_str}")
            st.dataframe(df_dia_f[['Cliente', 'Transportadora', 'Tabela_Transp', 'Perfil_Embarque', 'Perfil_Veiculo']].assign(
                Frete=df_dia_f['Frete_Receita_Pct'].apply(lambda x: f"{x*100:.2f}%"),
                Receita=df_dia_f['Receita_RS'].apply(format_brl)
            ).rename(columns={'Tabela_Transp': 'Tabela', 'Perfil_Embarque': 'Perfil Carga'}), use_container_width=True, hide_index=True)

with st.container(border=True):
    if not df_mes_cargas.empty and df_mes_cargas['Data'].notna().any():
        df_tendencia_ocup = df_mes_cargas.dropna(subset=['Data']).groupby('Data')['Ocupacao'].mean().reset_index().sort_values('Data')
        df_tendencia_ocup['Data_Str'] = df_tendencia_ocup['Data'].dt.strftime('%d/%m')
        
        fig_bar_ocup = px.bar(df_tendencia_ocup, x='Data_Str', y='Ocupacao', title="% de Ocupação", text=df_tendencia_ocup['Ocupacao'].apply(lambda x: f"{x*100:.1f}%"))
        fig_bar_ocup.add_hline(y=0.90, line_dash="dash", line_color="red")
        fig_bar_ocup.add_hline(y=ocup_mes, line_dash="dot", line_color="#059669", annotation_text=f"Média Mês: {ocup_mes*100:.1f}%")
        fig_bar_ocup.update_layout(title_x=0.5, template="plotly_white", yaxis_tickformat='.1%', hovermode="x unified", clickmode='event+select')
        fig_bar_ocup.update_traces(marker_color='#10B981', textposition='outside')
        
        selected_ocup = st.plotly_chart(fig_bar_ocup, use_container_width=True, on_select="rerun")
        
        if selected_ocup and selected_ocup.get("selection") and selected_ocup["selection"]["points"]:
            dia_str = selected_ocup["selection"]["points"][0]["x"]
            df_dia_o = df_mes_cargas[df_mes_cargas['Data'].dt.strftime('%d/%m') == dia_str].sort_values(by='Ocupacao', ascending=True)
            st.markdown(f"#### ⚠️ Detalhamento: {dia_str}")
            st.dataframe(df_dia_o[['Cliente', 'Transportadora', 'Tabela_Transp', 'Perfil_Embarque', 'Perfil_Veiculo']].assign(
                Ocupacao=df_dia_o['Ocupacao'].apply(lambda x: f"{x*100:.1f}%"),
                Receita=df_dia_o['Receita_RS'].apply(format_brl)
            ).rename(columns={'Tabela_Transp': 'Tabela', 'Perfil_Embarque': 'Perfil Carga'}), use_container_width=True, hide_index=True)