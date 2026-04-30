import streamlit as st
import pandas as pd
import os
import unicodedata
from PIL import Image
import difflib
import base64
st.set_page_config(page_title="Hapvida + Odonto", layout="wide", initial_sidebar_state="collapsed")

def get_img_as_base64(path):
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()
def normalize_name(name):
    if pd.isna(name):
        return ''
    name = unicodedata.normalize('NFKD', str(name)).encode('ascii', 'ignore').decode('ascii').lower().strip()
    return name

image_path = "imagem_fundo.png"
if os.path.exists(image_path):
    b64 = get_img_as_base64(image_path)
    st.markdown(
        f"""
        <style>
            .bg-top {{
                height: 40vh;  # ← MUDANÇA 1: Agora 33vh (terço superior)
                width: 100%;
                background-image: url(data:image/png;base64,{b64});
                background-size: cover;
                background-position: center center;
                background-repeat: no-repeat;
            }}
        </style>
        """,
        unsafe_allow_html=True
    )
    st.markdown('<div class="bg-top"></div>', unsafe_allow_html=True)

st.markdown('<div style="margin-top: -600px;">', unsafe_allow_html=True)

st.markdown("""
<style>
.titulo-principal {
    font-family: 'Arial Black', Arial, sans-serif;
    font-size: 3rem;
    font-weight: bold;
    color: #333333;
    text-align: center;
    margin-bottom: 1rem;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
  }
.titulo-azul {
    font-family: Arial, sans-serif;
    font-size: 2.5rem;
    color: #0066CC;
    text-align: center;
    margin-bottom: 0.8rem;
    font-weight: 600;
  }
.texto-detalhe {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    font-size: 1.1rem;
    color: #666666;
    line-height: 1.7;
    text-align: justify;
    margin-bottom: 1rem;
  }
.stExpander {
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    border-radius: 0.375rem;
    padding: 1rem;
    margin: 1rem 0;
  }
</style>
""", unsafe_allow_html=True)

def verificar_senha():
    if 'senha_correta' not in st.session_state:
      st.session_state.senha_correta = False

    if not st.session_state.senha_correta:
        st.markdown(
            """
            <style>
                .stApp {
                    background-image: url("fundo.jpg");
                    background-size: cover;
                    background-position: center;
                    background-repeat: no-repeat;
                    background-attachment: fixed;
                }
                .centered-logo {
                    display: flex;
                    justify-content: center;
                    margin-top: 10%;
                }
                .password-container {
                    display: flex;
                    justify-content: center;
                    margin-top: 20%;
                    width: 100%;
                }
                .password-box {
                    background: rgba(255, 255, 255, 0.9);
                    padding: 2rem;
                    border-radius: 10px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    width: 300px;
                }
            </style>
            """,
            unsafe_allow_html=True
        )
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image("logo pbi.jpg", width=250)


        # Formulário de login
        with st.form("login_form"):
            senha = st.text_input("Senha:", type="password")
            entrar = st.form_submit_button("Acessar")

        if entrar:
            if senha == "Hapvida+Odonto":
                st.session_state.senha_correta = True
                st.success("Acesso liberado!")
                st.rerun()
            else:
                st.error("Senha incorreta! Tente novamente.")

        st.stop()
@st.cache_data
def carregar_dados():
    arquivo = "AUDITORIA_ODONTO_2026.xlsx"
    if not os.path.exists(arquivo):
        st.error(f"Arquivo '{arquivo}' não encontrado!")
        st.stop()
    def limpar_colunas(df):
        df.columns = df.columns.astype(str).str.strip()
        df.columns = df.columns.map(lambda x: unicodedata.normalize('NFKD', x).encode('ascii', 'ignore').decode('ascii'))
        df.columns = df.columns.str.lower().str.replace(r'[/\-\s]+', '_', regex=True)
        return df.fillna("-")
    glosas = pd.read_excel(arquivo, sheet_name="Glosas")
    procedimentos = pd.read_excel(arquivo, sheet_name="Procedimentos")
    regras_gerais = pd.read_excel(arquivo, sheet_name="Regras_Gerais")
    regras_espec = pd.read_excel(arquivo, sheet_name="Regras_Especialidade")
    produtos = pd.read_excel(arquivo, sheet_name="Produtos")
    glosas_limpo = limpar_colunas(glosas)
    proc_limpo = limpar_colunas(procedimentos)
    regras_gerais_limpo = limpar_colunas(regras_gerais)
    regras_espec_limpo = limpar_colunas(regras_espec)
    produtos_limpo = limpar_colunas(produtos)
    produtos_limpo = produtos_limpo.rename(columns={
    "produto": "codigo_do_produto",
    "descricao_completa": "nome_do_produto",
    "status": "status_do_produto",
    "procedimentos": "codigo_do_procedimento",
    "descricao_procedimento": "nome_do_procedimento",
    "grupo": "especialidade"
})

    def limpar_decimal(x):
        if pd.isna(x) or x == "-":
            return x
        try:
            return str(int(float(x)))
        except:
            return str(x)
    proc_limpo['codigo_interno'] = proc_limpo['codigo_interno'].apply(limpar_decimal)
    return glosas_limpo, proc_limpo, regras_gerais_limpo, regras_espec_limpo, produtos_limpo

def find_column(df, keywords):
    cols_lower = [col.lower() for col in df.columns]
    for kw in keywords:
        kw_lower = kw.lower()
        matches = get_close_matches(kw_lower, cols_lower, n=1, cutoff=0.6)
        if matches:
            idx = cols_lower.index(matches[0])
            return df.columns[idx]
    return None

import os
import glob
import re

def responder_pergunta_chat(arquivo_nome: str, pergunta: str) -> str:
    if not pergunta or not pergunta.strip():
        return "Faça um pergunta ao Bob!"

    # Extrair palavras-chave da pergunta
    palavras_pergunta = re.findall(r'\w+', pergunta.lower())
    stopwords = {'o', 'a', 'de', 'que', 'e', 'do', 'da', 'em', 'um', 'para', 'com', 'não', 'uma', 'os', 'no', 'se', 'na', 'por', 'mais', 'as', 'foi', 'está', 'são', 'sua', 'suas', 'seu', 'seus', 'você', 'estou', 'estão'}
    keywords = set(palavras_pergunta) - stopwords

    if not keywords:
        return "Não entendi a pergunta. Tente palavras-chave mais específicas!"

    best_match = None
    best_score = 0

    # Buscar no arquivo específico
    if not os.path.exists(arquivo_nome):
        return f"Arquivo '{arquivo_nome}' não encontrado na pasta do projeto."

    try:
        with open(arquivo_nome, 'r', encoding='utf-8') as f:
            conteudo = f.read()

        linhas = conteudo.split('\n')
        for linha in linhas:
            linha_limpa = linha.strip()
            if len(linha_limpa) < 20:
                continue

            linha_lower = linha_limpa.lower()
            score = sum(1 for kw in keywords if kw in linha_lower)

            if score > best_score:
                best_score = score
                best_match = linha_limpa
    except Exception as e:
        return f"Erro ao ler arquivo: {str(e)}"

    if best_match and best_score > 0:
        return best_match
    else:
        return "Desculpe, não encontrei nada relevante. Tente reformular a pergunta!"
  
verificar_senha()
glosas_df, proc_df, regras_gerais_df, regras_espec_df, produtos_df = carregar_dados()
# Validações
colunas_glosas = ["n_da_glosa", "ativa", "descricao_interna", "tipo_de_glosa", "especialidade", "utilizacao", "subglosa", "como_evitar_a_glosa", "cabe_recurso", "como_recorrer", "justificativa", "origem_da_glosa"]
colunas_glosas_faltando = [c for c in colunas_glosas if c not in glosas_df.columns]
if colunas_glosas_faltando:
    st.error(f"Colunas faltando em Glosas: {colunas_glosas_faltando}")
    st.stop()
colunas_proc = ["codigo_interno", "tuss", "procedimento", "especialidade", "local_regiao", "procedimentos_pre_aprovados", "pre_requisito", "longevidade", "normas_tecnicas_e_observacoes"]
colunas_proc_faltando = [c for c in colunas_proc if c not in proc_df.columns]
if colunas_proc_faltando:
    st.error(f"Colunas faltando em Procedimentos: {colunas_proc_faltando}")
    st.stop()
if "secao_ativa" not in st.session_state:
    st.session_state.secao_ativa = None
# TELA INICIAL: 3 botões
left_col, mid_col, right_col = st.columns([1, 1, 1])
with left_col:
    if st.button("🔍 TABELA DE PROCEDIMENTOS", use_container_width=True):
        st.session_state.secao_ativa = "procedimentos"
        st.rerun()
with mid_col:
    if st.button("📋 MANUAL DE GLOSAS", use_container_width=True):
        st.session_state.secao_ativa = "glosas"
        st.rerun()    

# CONTEÚDO CONDICIONAL
if st.session_state.secao_ativa == "glosas":
    st.markdown("### Manual de Glosas") 
    glosas_list = glosas_df.to_dict('records')
    opcoes_glosa = sorted([f"{g['n_da_glosa']} - {g['descricao_interna']}" for g in glosas_list])    
    selecao_glosa = st.selectbox(
        "Digite o número da glosa ou descrição:",
        [""] + opcoes_glosa,
        format_func=lambda x: "Selecione..." if x == "" else x
    )
    if selecao_glosa:
        glosa_id = selecao_glosa.split(" - ")[0]
        dados_glosa = [g for g in glosas_list if g["n_da_glosa"] == glosa_id]        
        if dados_glosa:
            primeira = dados_glosa[0]            
            st.markdown('<div class="titulo-azul">Detalhes da Glosa</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="texto-detalhe"><b>N DA GLOSA:</b> {primeira["n_da_glosa"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="texto-detalhe"><b>DESCRIÇÃO INTERNA:</b> {primeira["descricao_interna"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="texto-detalhe"><b>ORIGEM:</b> {primeira["origem_da_glosa"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="texto-detalhe"><b>ATIVA:</b> {primeira["ativa"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="texto-detalhe"><b>TIPO:</b> {primeira["tipo_de_glosa"]}</div>', unsafe_allow_html=True)
            st.markdown('<div class="titulo-azul">Especialidade / Subglosa</div>', unsafe_allow_html=True)            
            for linha in dados_glosa:
                with st.expander(f"{linha['especialidade']} - {linha['subglosa']}"):
                    st.markdown(f"**ESPECIALIDADE:** {linha['especialidade']}")
                    st.markdown(f"**UTILIZAÇÃO:** {linha['utilizacao']}")
                    st.markdown(f"**SUBGLOSA:** {linha['subglosa']}")
                    st.markdown(f"**COMO EVITAR:** {linha['como_evitar_a_glosa']}")
                    st.markdown(f"**CABE RECURSO:** {linha['cabe_recurso']}")
                    st.markdown(f"**COMO RECORRER:** {linha['como_recorrer']}")
                    st.markdown(f"**JUSTIFICATIVA:** {linha['justificativa']}")
        else:
            st.warning("Glosa não encontrada.")
    else:
        st.info("Selecione uma glosa para visualizar detalhes.")

elif st.session_state.secao_ativa == "procedimentos":
    st.markdown("### 🔍 Tabela de Procedimentos")    
    if "proc_select" not in st.session_state:
        st.session_state.proc_select = ""    
    if "label_busca" not in proc_df.columns:
        proc_df["label_busca"] = (
            proc_df["tuss"].astype(str) + " - " +
            proc_df["codigo_interno"].astype(str) + " - " +
            proc_df["procedimento"].astype(str)
        )   
    opcoes_proc = [""] + sorted(proc_df["label_busca"].unique().tolist())

    st.selectbox(
        "Selecione um procedimento:",
        opcoes_proc,
        key="proc_select",
        format_func=lambda x: "Selecione..." if x == "" else x
    )
    if st.session_state.proc_select and st.session_state.proc_select != "":
        proc_row = proc_df[proc_df["label_busca"] == st.session_state.proc_select]
        if not proc_row.empty:
            row = proc_row.iloc[0]
            codigo_interno = str(row["codigo_interno"]).strip()
            with st.expander("Cobertura"):
                codigo_interno = str(row["codigo_interno"]).strip()
                produtos_df["codigo_do_procedimento"] = produtos_df["codigo_do_procedimento"].astype(str).str.strip()
                produtos_df["cobertura"] = produtos_df["cobertura"].astype(str).str.strip().str.lower()
                produtos_cobertos = produtos_df[
                    (produtos_df["codigo_do_procedimento"] == codigo_interno) &
                    (produtos_df["cobertura"] == "sim")
                ]
                if not produtos_cobertos.empty:
                    st.write("Produtos cobertos:")
                    for _, produto in produtos_cobertos.iterrows():
                        st.write(f"- {produto['nome_do_produto']} (Código: {produto['codigo_do_produto']})")
                else:
                    st.write("Nenhum produto coberto encontrado para este procedimento.")
            with st.expander("Detalhes do Procedimento"):
                detalhes = {
                    "CÓDIGO INTERNO": row["codigo_interno"],
                    "TUSS": row["tuss"],
                    "PROCEDIMENTO": row["procedimento"],
                    "ESPECIALIDADE": row["especialidade"],
                    "LOCAL / REGIÃO": row["local_regiao"],
                    "PRÉ-REQUISITOS": row["pre_requisito"],
                    "LONGEVIDADE": row["longevidade"],
                    "NORMAS TÉCNICAS": row["normas_tecnicas_e_observacoes"]
                }
                for label, valor in detalhes.items():
                    st.write(f"**{label}:** {valor}")                   
            with st.expander("⚖️ Regras Gerais"):
                if not regras_gerais_df.empty and "regras_gerais" in regras_gerais_df.columns:
                    regras = regras_gerais_df["regras_gerais"].dropna().astype(str).str.strip()
                    regras = regras[regras != ""]
                    if not regras.empty:
                        for regra in regras:
                            st.write(f"• {regra}")
                    else:
                        st.info("Nenhuma regra geral encontrada.")
                else:
                    st.info("Tabela de regras não disponível.")                   

            with st.expander("Regras por Especialidade"):
                if not regras_espec_df.empty and "especialidade" in regras_espec_df.columns:
                    especialidade_proc = str(row["especialidade"]).strip().lower()
                    especialidades_regras = (
                        regras_espec_df["especialidade"]
                        .astype(str)
                        .str.strip()
                        .str.lower()
                    )
                    match_regras = regras_espec_df[especialidades_regras == especialidade_proc]               
                    if not match_regras.empty and "regras_da_especialidade" in match_regras.columns:
                        regras = match_regras["regras_da_especialidade"].dropna().astype(str).str.strip()
                        regras = regras[regras != ""]
                        if not regras.empty:
                            for regra in regras:
                                st.write(f"• {regra}")
                        else:
                            st.info("Nenhuma regra específica encontrada.")
                    else:
                        st.info("Nenhuma regra encontrada para esta especialidade.")
                else:
                    st.info("Tabela de regras não disponível.")
        else:
            st.warning("Procedimento não encontrado.")
    else:
        st.info("Selecione um procedimento para visualizar detalhes.")

st.markdown("---")  # Separador
import streamlit as st

def search_file(filename, query):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
        query_lower = query.lower()
        query_words = query_lower.split()
        relevant = []
        for line in lines:
            line_lower = line.lower()
            if query_lower in line_lower or any(word in line_lower for word in query_words):
                relevant.append(line)
        if relevant:
            response = ' '.join(relevant[:10])[:2000]
            return response + f"\n\nFonte: {filename}"
        else:
            return f"Desculpe, não encontrei informações relevantes sobre '{query}' no arquivo {filename}."
    except FileNotFoundError:
        return f"Arquivo {filename} não encontrado."
    except Exception as e:
        return f"Erro ao ler {filename}: {str(e)}"

st.set_page_config(page_title="Pergunta ao Bob", page_icon="💬")

st.markdown("Faça uma Pergunta ao Bob")

# Initialize session states
if 'messages_procedimentos' not in st.session_state:
    st.session_state.messages_procedimentos = []
if 'messages_produtos' not in st.session_state:
    st.session_state.messages_produtos = []

# Seção Sobre Procedimentos

prompt_procedimentos = st.chat_input("Digite sua pergunta sobre procedimentos...")
if prompt_procedimentos:
    st.session_state.messages_procedimentos.append({"role": "user", "content": prompt_procedimentos})
    with st.chat_message("user"):
        st.markdown(prompt_procedimentos)
    
    response = search_file("Chat Auditoria Odontológica.txt", prompt_procedimentos)
    st.session_state.messages_procedimentos.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)
    
    st.rerun()

prompt_produtos = st.chat_input("Digite sua pergunta sobre produtos...")
if prompt_produtos:
    st.session_state.messages_produtos.append({"role": "user", "content": prompt_produtos})
    with st.chat_message("user"):
        st.markdown(prompt_produtos)
    
    response = search_file("Produtostxt.txt", prompt_produtos)
    st.session_state.messages_produtos.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)
    
    st.rerun()