import streamlit as st
import pandas as pd
import os
import glob
import re
import unicodedata
import base64
import difflib
st.set_page_config(page_title="Hapvida + Odonto", layout="wide", initial_sidebar_state="collapsed")
# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def get_img_as_base64(path):
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()
def normalize_name(name):
    if pd.isna(name):
        return ''
    name = unicodedata.normalize('NFKD', str(name)).encode('ascii', 'ignore').decode('ascii').lower().strip()
    return name
def encontrar_arquivo(padrao):
    """Procura um arquivo pelo padrão (glob), tolerando pequenas variações de nome
    (acentos, espaços, sufixos) que costumam quebrar entre Windows e o Linux do
    Streamlit Cloud. Retorna o primeiro encontrado ou None."""
    candidatos = glob.glob(padrao)
    return candidatos[0] if candidatos else None
def ler_texto_arquivo(caminho):
    """Lê um .txt tentando utf-8 primeiro e caindo para latin-1/cp1252 se
    necessário. Alguns dos arquivos de apoio deste projeto foram exportados do
    Windows em cp1252 e quebravam a leitura forçada em utf-8, derrubando o
    app no meio de um rerender (o que o navegador mostra como um erro
    genérico de DOM, tipo 'removeChild')."""
    for enc in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            with open(caminho, "r", encoding=enc) as f:
                return f.read()
        except (UnicodeDecodeError, LookupError):
            continue
    with open(caminho, "r", encoding="utf-8", errors="replace") as f:
        return f.read()
def search_file(filename, query):
    if not filename or not os.path.exists(filename):
        return f"Arquivo '{filename}' não encontrado no projeto."
    try:
        conteudo = ler_texto_arquivo(filename)
        lines = [line.strip() for line in conteudo.splitlines() if line.strip()]
        query_lower = query.lower()
        query_words = query_lower.split()
        relevant = []
        for line in lines:
            line_lower = line.lower()
            if query_lower in line_lower or any(word in line_lower for word in query_words):
                relevant.append(line)
        if relevant:
            response = ' '.join(relevant[:10])[:2000]
            return response + f"\n\nFonte: {os.path.basename(filename)}"
        else:
            return f"Desculpe, não encontrei informações relevantes sobre '{query}'."
    except Exception as e:
        return f"Erro ao ler o arquivo de apoio: {e}"
def find_column(df, keywords):
    cols_lower = [col.lower() for col in df.columns]
    for kw in keywords:
        kw_lower = kw.lower()
        matches = difflib.get_close_matches(kw_lower, cols_lower, n=1, cutoff=0.6)
        if matches:
            idx = cols_lower.index(matches[0])
            return df.columns[idx]
    return None
def limpar_decimal(x):
    """Normaliza valores numéricos (que o pandas às vezes lê como int64/float,
    às vezes como texto) para uma mesma representação em string, ex.: 407,
    407.0 e '407' viram todos '407'. Isso evita que comparações do tipo
    "407" == 407 (string vs número) falhem silenciosamente."""
    if pd.isna(x) or x == "-":
        return x
    try:
        return str(int(float(x)))
    except Exception:
        return str(x).strip()
# ----------------------------------------------------------------------------
# Caminhos dos arquivos de apoio (tolerantes a pequenas variações de nome)
# ----------------------------------------------------------------------------
ARQUIVO_EXCEL = encontrar_arquivo("AUDITORIA_ODONTO_2026*.xlsx")
ARQUIVO_IMG_FUNDO = encontrar_arquivo("imagem_fundo*.png")
ARQUIVO_LOGO = encontrar_arquivo("logo*pbi*.jpg") or encontrar_arquivo("logo*pbi*.jpeg") or encontrar_arquivo("logo*pbi*.png")
ARQUIVO_CHAT_PROCEDIMENTOS = (
    encontrar_arquivo("Chat*Auditoria*Odontol*.txt")
    or encontrar_arquivo("Chat_Auditoria_Odontologica.txt")
)
ARQUIVO_PRODUTOS_TXT = encontrar_arquivo("Produtostxt*.txt") or encontrar_arquivo("Produtos*.txt")
# ----------------------------------------------------------------------------
# Estilos / imagem de topo
# ----------------------------------------------------------------------------
if ARQUIVO_IMG_FUNDO and os.path.exists(ARQUIVO_IMG_FUNDO):
    try:
        b64 = get_img_as_base64(ARQUIVO_IMG_FUNDO)
        st.markdown(
            f"""
            <style>
                .bg-top {{
                    height: 40vh;
                    width: 100%;
                    margin-top: -600px;
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
    except Exception:
        pass
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
# ----------------------------------------------------------------------------
# Login
# ----------------------------------------------------------------------------
def verificar_senha():
    if 'senha_correta' not in st.session_state:
        st.session_state.senha_correta = False
    if not st.session_state.senha_correta:
        st.markdown(
            """
            <style>
                .stApp {
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
            </style>
            """,
            unsafe_allow_html=True
        )
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if ARQUIVO_LOGO and os.path.exists(ARQUIVO_LOGO):
                try:
                    st.image(ARQUIVO_LOGO, width=250)
                except Exception:
                    pass
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
# ----------------------------------------------------------------------------
# Dados
# ----------------------------------------------------------------------------
@st.cache_data
def carregar_dados(arquivo):
    if not arquivo or not os.path.exists(arquivo):
        st.error(
            "Arquivo de dados 'AUDITORIA_ODONTO_2026.xlsx' não encontrado no projeto. "
            "Verifique se ele foi enviado ao repositório com esse nome."
        )
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
    proc_limpo['codigo_interno'] = proc_limpo['codigo_interno'].apply(limpar_decimal)
    # "N DA GLOSA" às vezes vem como número (407) e às vezes como texto ("407")
    # dependendo de como a linha foi digitada na planilha. Sem essa normalização,
    # comparar o valor selecionado no combo (sempre string) com o valor da
    # coluna (às vezes int64) falha e a glosa aparece como "não encontrada"
    # mesmo existindo na base.
    glosas_limpo['n_da_glosa'] = glosas_limpo['n_da_glosa'].apply(limpar_decimal)
    return glosas_limpo, proc_limpo, regras_gerais_limpo, regras_espec_limpo, produtos_limpo
verificar_senha()
glosas_df, proc_df, regras_gerais_df, regras_espec_df, produtos_df = carregar_dados(ARQUIVO_EXCEL)
# Validações
colunas_glosas = ["n_da_glosa", "ativa", "descricao_interna", "tipo_de_glosa", "especialidade", "utilizacao",
                   "subglosa", "como_evitar_a_glosa", "cabe_recurso", "como_recorrer", "justificativa",
                   "origem_da_glosa"]
colunas_glosas_faltando = [c for c in colunas_glosas if c not in glosas_df.columns]
if colunas_glosas_faltando:
    st.error(f"Colunas faltando em Glosas: {colunas_glosas_faltando}")
    st.stop()
colunas_proc = ["codigo_interno", "tuss", "procedimento", "especialidade", "local_regiao",
                 "procedimentos_pre_aprovados", "pre_requisito", "longevidade", "normas_tecnicas_e_observacoes"]
colunas_proc_faltando = [c for c in colunas_proc if c not in proc_df.columns]
if colunas_proc_faltando:
    st.error(f"Colunas faltando em Procedimentos: {colunas_proc_faltando}")
    st.stop()
if "secao_ativa" not in st.session_state:
    st.session_state.secao_ativa = None
# TELA INICIAL: botões
left_col, mid_col, right_col = st.columns([1, 1, 1])
with left_col:
    if st.button("🔍 TABELA DE PROCEDIMENTOS", use_container_width=True, key="btn_procedimentos"):
        st.session_state.secao_ativa = "procedimentos"
        st.rerun()
with mid_col:
    if st.button("📋 MANUAL DE GLOSAS", use_container_width=True, key="btn_glosas"):
        st.session_state.secao_ativa = "glosas"
        st.rerun()
# CONTEÚDO CONDICIONAL
if st.session_state.secao_ativa == "glosas":
    st.markdown("### Manual de Glosas")
    glosas_list = glosas_df.to_dict('records')
    # Uma mesma glosa (mesmo "N DA GLOSA") pode ter várias linhas na planilha,
    # uma para cada especialidade/subglosa. O combo deve mostrar cada glosa
    # UMA única vez; o detalhamento por especialidade/subglosa continua sendo
    # feito mais abaixo, nos expanders, usando todas as linhas daquele número.
    descricao_por_glosa = {}
    for g in glosas_list:
        num = g["n_da_glosa"]
        if num not in descricao_por_glosa:
            descricao_por_glosa[num] = g["descricao_interna"]
    def _chave_ordenacao_glosa(num):
        try:
            return (0, int(num))
        except (ValueError, TypeError):
            return (1, str(num))
    opcoes_glosa = [
        f"{num} - {descricao_por_glosa[num]}"
        for num in sorted(descricao_por_glosa.keys(), key=_chave_ordenacao_glosa)
    ]
    selecao_glosa = st.selectbox(
        "Digite o número da glosa ou descrição:",
        [""] + opcoes_glosa,
        format_func=lambda x: "Selecione..." if x == "" else x,
        key="select_glosa"
    )
    if selecao_glosa:
        glosa_id = selecao_glosa.split(" - ", 1)[0].strip()
        dados_glosa = [g for g in glosas_list if str(g["n_da_glosa"]).strip() == glosa_id]
        if dados_glosa:
            primeira = dados_glosa[0]
            st.markdown('<div class="titulo-azul">Detalhes da Glosa</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="texto-detalhe"><b>N DA GLOSA:</b> {primeira["n_da_glosa"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="texto-detalhe"><b>DESCRIÇÃO INTERNA:</b> {primeira["descricao_interna"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="texto-detalhe"><b>ORIGEM:</b> {primeira["origem_da_glosa"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="texto-detalhe"><b>ATIVA:</b> {primeira["ativa"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="texto-detalhe"><b>TIPO:</b> {primeira["tipo_de_glosa"]}</div>', unsafe_allow_html=True)
            st.markdown('<div class="titulo-azul">Especialidade / Subglosa</div>', unsafe_allow_html=True)
            for i, linha in enumerate(dados_glosa):
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
    if "label_busca" not in proc_df.columns:
        proc_df["label_busca"] = (
            proc_df["tuss"].astype(str) + " - " +
            proc_df["codigo_interno"].astype(str) + " - " +
            proc_df["procedimento"].astype(str)
        )
    if "proc_select" not in st.session_state:
        st.session_state.proc_select = ""
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
# ----------------------------------------------------------------------------
# "Faça uma Pergunta ao Bob" — OCULTO A PEDIDO. Bloco mantido no código,
# apenas comentado, para poder reativar rapidamente no futuro: basta remover
# o "# " do início de cada linha abaixo.
# ----------------------------------------------------------------------------
# st.markdown("---")
# st.markdown("Faça uma Pergunta ao Bob")
# if 'messages_bob' not in st.session_state:
#     st.session_state.messages_bob = []
# assunto = st.radio(
#     "Sobre o que é a sua pergunta?",
#     ["Procedimentos", "Produtos"],
#     horizontal=True,
#     key="assunto_bob"
# )
# for msg in st.session_state.messages_bob:
#     with st.chat_message(msg["role"]):
#         st.markdown(msg["content"])
# placeholder = (
#     "Digite sua pergunta sobre procedimentos..."
#     if assunto == "Procedimentos"
#     else "Digite sua pergunta sobre produtos..."
# )
# prompt_bob = st.chat_input(placeholder, key="chat_bob")
# if prompt_bob:
#     st.session_state.messages_bob.append({"role": "user", "content": prompt_bob})
#     with st.chat_message("user"):
#         st.markdown(prompt_bob)
#     arquivo_busca = ARQUIVO_CHAT_PROCEDIMENTOS if assunto == "Procedimentos" else ARQUIVO_PRODUTOS_TXT
#     response = search_file(arquivo_busca, prompt_bob)
#     st.session_state.messages_bob.append({"role": "assistant", "content": response})
#     with st.chat_message("assistant"):
#         st.markdown(response)
