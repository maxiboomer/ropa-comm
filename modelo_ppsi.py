#!/usr/bin/env python3
"""
modelo_ppsi.py — Campos e taxonomia do RoPA alinhados ao
Guia para Elaboração do Registro das Operações de Tratamento (PPSI 2.0, v1.0)
e ao controle 19 do framework do PPSI 2.0 (Portaria SGD/MGI nº 9.511/2025).

Compartilhado por app.py (web) e ropa.py (CLI) para evitar divergência.
Conteúdo mínimo (blocos 4.1–4.6 da Tabela 1 do Guia).
"""
import json
import os

# ── Situações do registro (Guia 4.1.5) ───────────────────────────────────────
SITUACOES = [
    ("em_andamento", "Em andamento"),
    ("em_revisao",   "Em revisão"),
    ("concluido",    "Concluído"),
    ("descontinuado","Descontinuado"),
    ("cancelado",    "Cancelado"),
]

# ── Taxonomia de categorias de dados compatível com o FCI da ANPD (Guia 4.2.3)
CATEGORIAS_DADOS_FCI = {
    "dados_basicos_identificacao":   "Dados básicos de identificação",
    "documentos_identificacao":      "Documentos de identificação oficial",
    "dados_contato":                 "Dados de contato",
    "dados_financeiros":             "Dados financeiros e meios de pagamento",
    "sigilo_legal_profissional":     "Dados protegidos por sigilo legal ou profissional",
    "dados_autenticacao":            "Dados de autenticação",
    "imagem_voz_localizacao":        "Imagem, voz e localização geográfica",
    "dados_biometricos":             "Dados biométricos",
    "dados_saude":                   "Dados de saúde",
    "outros":                        "Outros",
}

# ── Titulares que demandam proteção reforçada (Guia 4.2.2) ───────────────────
CATEGORIAS_PROTECAO_REFORCADA = [
    "criancas",
    "adolescentes",
    "idosos",
    "outros vulneráveis",
]

# ── Campos cujo valor é armazenado como JSON (multivalorado) ─────────────────
JSON_FIELDS = {
    "titulares_estimativa",            # {categoria: quantidade}
    "titulares_protecao_reforcada",    # [categoria, ...]
    "tipos_dados",                     # {categoria_FCI: [tipos, ...]}
    "tipos_dados_sensiveis",           # [tipo, ...]
    "origem_dados",                    # [fonte, ...]
    "controladores",                   # [linha, ...]
    "operadores",                      # [linha, ...]
    "compartilhamentos",               # [linha, ...]
    "transferencia_internacional",     # [linha, ...]
}

# ── Completude (soma = 100) alinhada ao conteúdo mínimo do Guia ──────────────
CAMPOS_VALIDACAO = {
    "nome_atividade":            ("Nome da atividade de tratamento", 8),
    "unidade_controladora":      ("Unidade administrativa responsável", 5),
    "responsavel_preenchimento": ("Responsável pelo preenchimento", 3),
    "situacao":                  ("Situação do registro", 3),
    "finalidade":                ("Finalidade do tratamento", 7),
    "base_legal":                ("Base legal", 8),
    "previsao_normativa":        ("Previsão normativa específica", 4),
    "categorias_titulares":      ("Categorias de titulares", 5),
    "titulares_protecao_reforcada": ("Titulares com proteção reforçada", 3),
    "categorias_dados":          ("Tipos de dados pessoais", 3),
    "tipos_dados_sensiveis":     ("Tipos de dados sensíveis", 3),
    "fluxo_tratamento":          ("Fluxo de tratamento dos dados", 6),
    "origem_dados":              ("Origem dos dados pessoais", 4),
    "local_armazenamento":       ("Local e meio de armazenamento", 4),
    "prazo_retencao":            ("Período de retenção", 5),
    "eliminacao_destinacao":     ("Forma de eliminação/destinação final", 4),
    "frequencia_tratamento":     ("Frequência do tratamento", 3),
    "controladores":             ("Controladores", 4),
    "operadores":                ("Operadores", 5),
    "destinatarios":             ("Compartilhamento", 5),
    "transferencia_internacional": ("Transferência internacional", 3),
    "medidas_seguranca":         ("Medidas de segurança", 5),
}
assert sum(p for _, p in CAMPOS_VALIDACAO.values()) == 100, "CAMPOS_VALIDACAO deve somar 100"


# ── Módulo RIPD (controles 23.3, 25.8, 25.10 do PPSI 2.0) ────────────────────

SITUACOES_RIPD = [
    ("rascunho",   "Rascunho"),
    ("em_revisao", "Em revisão"),
    ("aprovado",   "Aprovado"),
    ("publicado",  "Publicado"),
    ("desatualizado", "Desatualizado (revisar)"),
]

# 10 princípios do art. 6º da LGPD
PRINCIPIOS_LGPD = [
    ("finalidade", "Finalidade (art. 6º, I)"),
    ("adequacao", "Adequação (art. 6º, II)"),
    ("necessidade", "Necessidade (art. 6º, III)"),
    ("livre_acesso", "Livre acesso (art. 6º, IV)"),
    ("qualidade_dados", "Qualidade dos dados (art. 6º, V)"),
    ("transparencia", "Transparência (art. 6º, VI)"),
    ("seguranca", "Segurança (art. 6º, VII)"),
    ("prevencao", "Prevenção (art. 6º, VIII)"),
    ("nao_discriminacao", "Não discriminação (art. 6º, IX)"),
    ("responsabilizacao", "Responsabilização e prestação de contas (art. 6º, X)"),
]

# Direitos do titular (art. 18 LGPD)
DIREITOS_TITULARES = [
    ("confirmacao", "Confirmação de tratamento (art. 18, I)"),
    ("acesso", "Acesso aos dados (art. 18, II)"),
    ("correcao", "Correção de dados (art. 18, III)"),
    ("anonimizacao", "Anonimização/eliminação (art. 18, IV)"),
    ("portabilidade", "Portabilidade (art. 18, V)"),
    ("informacao", "Informação sobre compartilhamento (art. 18, VI)"),
    ("revogacao", "Revogação de consentimento (art. 18, VIII)"),
    ("oposicao", "Oposição a tratamento (art. 18, X)"),
]

CRITERIO_GERAL_LABELS = {
    "larga_escala": "Tratamento de dados em larga escala",
    "direitos_fundamentais": "Tratamento que afeta significativamente interesses e direitos fundamentais dos titulares",
}

CRITERIO_ESPECIFICO_LABELS = {
    "tecnologias_emergentes": "Uso de tecnologias emergentes ou inovadoras",
    "vigilancia": "Vigilância ou controle de zonas acessíveis ao público",
    "decisoes_automatizadas": "Decisões unicamente baseadas em tratamento automatizado (perfilamento)",
    "dados_sensiveis_vulneraveis": "Utilização de dados sensíveis ou de crianças, adolescentes ou idosos",
}

_LARGA_ESCALA_MIN = int(os.environ.get("ROPA_RIPD_LARGA_ESCALA_MIN", "10000"))


def calcular_risco(atividade) -> dict:
    """Avalia alto risco (RIPD) conforme Res. CD/ANPD nº 2/2022, art. 4º, e a boa
    prática do Guia de RIPD do PPSI 2.0 (2+ fatores). Alimenta o gatilho controle 19 → 23.3."""
    a = dict(atividade or {})

    # ── Critérios gerais ──
    geral = []
    total = 0
    try:
        est = json.loads(a.get("titulares_estimativa") or "{}")
        if isinstance(est, dict):
            for v in est.values():
                try:
                    num = int(str(v).replace(".", "").replace(",", "").strip() or 0)
                    total += num
                except Exception:
                    pass
    except Exception:
        pass
    if total >= _LARGA_ESCALA_MIN:
        geral.append("larga_escala")

    prot = parse_json(a.get("titulares_protecao_reforcada"))
    if (a.get("dados_sensiveis") or prot or
            a.get("decisoes_automatizadas") or a.get("tecnologias_emergentes") or
            a.get("vigilancia_zonas_publicas")):
        geral.append("direitos_fundamentais")

    # ── Critérios específicos ──
    especifico = []
    if a.get("tecnologias_emergentes"):
        especifico.append("tecnologias_emergentes")
    if a.get("vigilancia_zonas_publicas"):
        especifico.append("vigilancia")
    if a.get("decisoes_automatizadas"):
        especifico.append("decisoes_automatizadas")
    if a.get("dados_sensiveis") or any(x in prot for x in ("criancas", "adolescentes", "idosos")):
        especifico.append("dados_sensiveis_vulneraveis")

    fatores = list(dict.fromkeys(geral + especifico))
    alto_risco = bool(geral) and bool(especifico)
    recomenda = alto_risco or len(fatores) >= 2  # boa prática PPSI 2.0

    return {
        "geral": geral,
        "especifico": especifico,
        "fatores": fatores,
        "larga_escala_total": total,
        "alto_risco": alto_risco,
        "recomenda": recomenda,
    }


# ── Helpers JSON ──────────────────────────────────────────────────────────────

def _vazio(val) -> bool:
    """True se o valor está vazio para fins de completude."""
    if not val:
        return True
    s = str(val).strip()
    if not s or s.upper() in ("N/A", "NENHUM", "—", "NONE", "NULL", "[]", "{}"):
        return True
    if s in JSON_FIELDS or s in ("tipos_dados", "titulares_estimativa", "compartilhamentos"):
        pass
    return False


def preenchido(campo: str, val) -> bool:
    """Campo preenchido? (JSON é considerado preenchido se a estrutura não é vazia)."""
    if not val:
        return False
    s = str(val).strip()
    if not s or s.upper() in ("N/A", "NENHUM", "—", "NONE", "NULL"):
        return False
    if campo in JSON_FIELDS:
        try:
            parsed = json.loads(s)
            if isinstance(parsed, (list, dict)):
                return bool(parsed)
        except Exception:
            pass
    return True


def json_ou_vazio(val):
    """Normaliza um valor JSON para string, '' se vazio."""
    if val is None:
        return ""
    if isinstance(val, str):
        s = val.strip()
        if s in ("", "[]", "{}", "null"):
            return ""
        return s
    if isinstance(val, (list, dict)):
        return json.dumps(val, ensure_ascii=False) if val else ""
    return str(val)


def parse_json(val):
    """Converte JSON armazenado (str) em list/dict para uso em templates."""
    if isinstance(val, (list, dict)):
        return val
    if isinstance(val, str):
        try:
            return json.loads(val) if val else []
        except Exception:
            return []
    return []


def parse_lista(texto: str) -> list:
    """Cada linha não vazia vira um item da lista."""
    out = []
    for linha in (texto or "").splitlines():
        item = linha.strip().strip(";,")
        if item:
            out.append(item)
    return out


def parse_dict_tipos(texto: str) -> dict:
    """Formato 'Categoria: tipo1; tipo2; tipo3' por linha -> {categoria: [tipos]}."""
    out = {}
    for linha in (texto or "").splitlines():
        if ":" not in linha:
            continue
        chave, resto = linha.split(":", 1)
        chave = chave.strip()
        tipos = [t.strip() for t in resto.split(";") if t.strip()]
        if chave and tipos:
            out[chave] = tipos
    return out


def parse_estimativa(texto: str) -> dict:
    """Formato 'categoria: quantidade' por linha -> {categoria: quantidade}."""
    out = {}
    for linha in (texto or "").splitlines():
        if ":" not in linha:
            continue
        chave, valor = linha.split(":", 1)
        chave = chave.strip()
        valor = valor.strip()
        if chave and valor:
            out[chave] = valor
    return out


def lista_para_texto(raw) -> str:
    """JSON list -> texto (um item por linha) para preencher textarea."""
    if isinstance(raw, str):
        try:
            raw = json.loads(raw) if raw else []
        except Exception:
            return raw
    if not isinstance(raw, list):
        return ""
    return "\n".join(str(x) for x in raw)


def dict_tipos_para_texto(raw) -> str:
    """JSON {categoria: [tipos]} -> texto 'categoria: tipo1; tipo2' por linha."""
    if isinstance(raw, str):
        try:
            raw = json.loads(raw) if raw else {}
        except Exception:
            return raw
    if not isinstance(raw, dict):
        return ""
    linhas = []
    for cat, tipos in raw.items():
        if tipos:
            linhas.append(f"{cat}: {'; '.join(str(t) for t in tipos)}")
    return "\n".join(linhas)


def dict_estimativa_para_texto(raw) -> str:
    """JSON {categoria: quantidade} -> texto 'categoria: quantidade' por linha."""
    if isinstance(raw, str):
        try:
            raw = json.loads(raw) if raw else {}
        except Exception:
            return raw
    if not isinstance(raw, dict):
        return ""
    return "\n".join(f"{k}: {v}" for k, v in raw.items() if v)


# ── Migração de schema (aditiva, não destrutiva) ─────────────────────────────

NOVAS_COLUNAS = {
    "responsavel_preenchimento": "TEXT",
    "situacao":                  "TEXT",
    "versao":                    "TEXT",
    "titulares_estimativa":      "TEXT",
    "titulares_protecao_reforcada": "TEXT",
    "tipos_dados":               "TEXT",
    "tipos_dados_sensiveis":     "TEXT",
    "fluxo_tratamento":          "TEXT",
    "origem_dados":              "TEXT",
    "local_armazenamento":       "TEXT",
    "eliminacao_destinacao":     "TEXT",
    "frequencia_tratamento":     "TEXT",
    "previsao_normativa":        "TEXT",
    "controladores":             "TEXT",
    "operadores":                "TEXT",
    "compartilhamentos":         "TEXT",
    "transferencia_internacional": "TEXT",
    # Critérios de alto risco p/ gatilho de RIPD (Res. CD/ANPD 2/2022, art. 4º)
    "tecnologias_emergentes":    "INTEGER DEFAULT 0",
    "decisoes_automatizadas":    "INTEGER DEFAULT 0",
    "vigilancia_zonas_publicas": "INTEGER DEFAULT 0",
}


def migrar_schema(conn):
    """Adiciona colunas novas e tabela de versões, sem tocar nos dados atuais."""
    cols = {r[1] for r in conn.execute("PRAGMA table_info(atividades)")}
    for nome, tipo in NOVAS_COLUNAS.items():
        if nome not in cols:
            conn.execute(f"ALTER TABLE atividades ADD COLUMN {nome} {tipo}")

    conn.execute("""
    CREATE TABLE IF NOT EXISTS versoes (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        atividade_id  INTEGER,
        versao        TEXT,
        sintese       TEXT,
        responsavel   TEXT,
        snapshot      TEXT,
        criado_em     TEXT DEFAULT (datetime('now','localtime'))
    )""")

    # ── Módulo RIPD (controles 23.3, 25.8, 25.10 do PPSI 2.0) ──
    conn.execute("""
    CREATE TABLE IF NOT EXISTS ripds (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,
        atividade_id        INTEGER NOT NULL,
        titulo              TEXT,
        situacao            TEXT DEFAULT 'rascunho',
        versao              TEXT DEFAULT '1.0',
        justificativa       TEXT,
        criterio_geral      TEXT,
        criterio_especifico TEXT,
        fatores_risco       TEXT,
        alto_risco          INTEGER DEFAULT 0,
        descricao_operacoes TEXT,
        principios          TEXT,
        direitos_titulares  TEXT,
        riscos              TEXT,
        medidas_mitigacao   TEXT,
        riscos_residuais    TEXT,
        restricoes_publicacao TEXT,
        aprovado_por        TEXT,
        aprovado_em         TEXT,
        criado_em           TEXT DEFAULT (datetime('now','localtime')),
        atualizado_em       TEXT DEFAULT (datetime('now','localtime'))
    )""")
    conn.execute("""
    CREATE TABLE IF NOT EXISTS versoes_ripd (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        ripd_id       INTEGER,
        versao        TEXT,
        sintese       TEXT,
        responsavel   TEXT,
        snapshot      TEXT,
        criado_em     TEXT DEFAULT (datetime('now','localtime'))
    )""")

    # Registros legados (pré-PPSI 2.0) passam a "concluído" / versão 1.0.
    conn.execute("UPDATE atividades SET situacao='concluido' WHERE situacao IS NULL OR situacao=''")
    conn.execute("UPDATE atividades SET versao='1.0' WHERE versao IS NULL OR versao=''")

    # Semear versão 1.0 (snapshot) para registros ainda sem histórico de versões.
    rows = conn.execute("SELECT * FROM atividades").fetchall()
    for r in rows:
        n = conn.execute("SELECT COUNT(*) FROM versoes WHERE atividade_id=?", (r["id"],)).fetchone()[0]
        if n == 0:
            snap = dict(r)
            snap.pop("id", None)
            conn.execute("""
                INSERT INTO versoes (atividade_id, versao, sintese, responsavel, snapshot)
                VALUES (?,?,?,?,?)
            """, (r["id"], "1.0", "v1.0 – registro original (migração PPSI 2.0)",
                   "Migração PPSI 2.0", json.dumps(snap, ensure_ascii=False, default=str)))


def proxima_versao(versao_atual: str, alteracao_estrutural: bool) -> str:
    """Versionamento semântico: major para alterações estruturais, minor caso contrário."""
    try:
        major, minor = (versao_atual or "1.0").split(".")
        major = int(major)
        minor = int(minor)
    except Exception:
        major, minor = 1, 0
    if alteracao_estrutural:
        return f"{major + 1}.0"
    return f"{major}.{minor + 1}"


def campos_estruturais() -> set:
    """Alterações nestes campos geram nova versão MAJOR."""
    return {"finalidade", "base_legal", "categorias_dados", "tipos_dados",
            "operadores", "controladores", "fluxo_tratamento", "prazo_retencao"}

