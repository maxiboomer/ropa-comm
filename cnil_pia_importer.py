#!/usr/bin/env python3
"""
CNIL PIA JSON Importer for RoPA
LGPD compliance

Converts CNIL Privacy Impact Assessment (PIA) JSON format to RoPA/LGPD activities.
Maps GDPR-style PIA fields to Brazilian LGPD compliance requirements.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ── Configuration ──────────────────────────────────────────────────────────────

DB_PATH = Path(__file__).parent / "ropa.db"

# LGPD Legal Basis mapping from GDPR/CNIL equivalents
LEGAL_BASIS_MAPPING = {
    "consentimento": "I",
    "consentement": "I",
    "consent": "I",

    "obrigacao_legal": "II",
    "obligation_légale": "II",
    "legal_obligation": "II",

    "executar_politicas_publicas": "III",
    "exécution_politiques_publiques": "III",
    "public_policy": "III",

    "pesquisa": "IV",
    "recherche": "IV",
    "research": "IV",

    "executar_contrato": "V",
    "exécution_contrat": "V",
    "contract_execution": "V",

    "exercicio_direitos": "VI",
    "exercice_droits": "VI",
    "legitimate_exercise_rights": "VI",

    "protecao_vida": "VII",
    "protection_vie": "VII",
    "vital_interests": "VII",

    "tutela_saude": "VIII",
    "tutelle_santé": "VIII",
    "health_protection": "VIII",

    "legitimo_interesse": "IX",
    "légitime_intérêt": "IX",
    "legitimate_interest": "IX",

    "protecao_credito": "X",
    "protection_crédit": "X",
    "credit_protection": "X",

    "dados_sensiveis_consentimento": "S-I",
    "données_sensibles_consentement": "S-I",

    "dados_sensiveis_obrigacao": "S-II",
    "données_sensibles_obligation": "S-II",
}


def get_conn() -> sqlite3.Connection:
    """Create database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def fix_encoding(text: str) -> str:
    """
    Fix common encoding issues (mojibake from Latin-1/UTF-8 mismatch).

    Args:
        text: Text potentially with encoding issues

    Returns:
        Properly encoded text
    """
    if not isinstance(text, str):
        return text

    # Try to detect and fix Latin-1 encoded as UTF-8
    try:
        # If text contains mojibake patterns, try to fix it
        if "Ã¡" in text or "Ã§" in text or "Ã£" in text:
            # Likely Latin-1 text interpreted as UTF-8
            fixed = text.encode('latin-1').decode('utf-8', errors='ignore')
            return fixed
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass

    return text


def parse_cnil_json(file_content: str) -> Dict[str, Any]:
    """
    Parse and validate CNIL PIA JSON content.
    Supports multiple PIA formats (simple and assessment system).
    Handles encoding issues automatically.

    Args:
        file_content: JSON string from file (may be UTF-8 or Latin-1)

    Returns:
        Parsed JSON dict

    Raises:
        ValueError: If JSON is invalid
    """
    # Fix encoding issues if present
    file_content = fix_encoding(file_content)

    try:
        data = json.loads(file_content)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON inválido: {str(e)}")

    if not isinstance(data, dict):
        raise ValueError("JSON deve ser um objeto (não array)")

    return data


def detect_pia_format(pia_data: Dict[str, Any]) -> str:
    """
    Detect which PIA format is being used.

    Args:
        pia_data: Parsed JSON dict

    Returns:
        "simple" (has 'atividades'), "assessment" (has 'pia' and 'answers'), or "unknown"
    """
    if "atividades" in pia_data:
        return "simple"
    elif "pia" in pia_data and "answers" in pia_data:
        return "assessment"
    return "unknown"


def validate_cnil_pia_schema(pia_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate CNIL PIA JSON structure.
    Supports both simple format (atividades array) and assessment system format.

    Args:
        pia_data: Parsed JSON dict

    Returns:
        (is_valid, error_messages)
    """
    errors = []
    format_type = detect_pia_format(pia_data)

    if format_type == "unknown":
        errors.append("Formato PIA não reconhecido. Esperado: 'atividades' (simples) ou 'pia'+'answers' (assessment)")
        return False, errors

    # Validate simple format
    if format_type == "simple":
        if not isinstance(pia_data.get("atividades"), list):
            errors.append("'atividades' deve ser um array")
        elif not pia_data["atividades"]:
            errors.append("'atividades' não pode estar vazio")
        else:
            for idx, activity in enumerate(pia_data["atividades"]):
                if not isinstance(activity, dict):
                    errors.append(f"Atividade [{idx}] deve ser um objeto")
                elif "traitement" not in activity or "nom" not in activity.get("traitement", {}):
                    errors.append(f"Atividade [{idx}] requer traitement.nom")

    # Validate assessment format
    elif format_type == "assessment":
        if not isinstance(pia_data.get("pia"), dict):
            errors.append("'pia' deve ser um objeto")
        elif not pia_data["pia"].get("name"):
            errors.append("'pia.name' obrigatório")

        if not isinstance(pia_data.get("answers"), list):
            errors.append("'answers' deve ser um array")

    return len(errors) == 0, errors


def map_legal_basis(cnil_basis: Optional[str]) -> str:
    """
    Map CNIL/GDPR legal basis to LGPD Art. 7 basis code.

    Args:
        cnil_basis: CNIL legal basis string (may be French/English/Portuguese)

    Returns:
        LGPD basis code (I, II, ..., S-I, S-II) or "IX" (default: legitimate interest)
    """
    if not cnil_basis:
        return "IX"  # Default to legitimate interest

    basis_lower = str(cnil_basis).lower().strip()

    # Direct lookup in mapping
    if basis_lower in LEGAL_BASIS_MAPPING:
        return LEGAL_BASIS_MAPPING[basis_lower]

    # Substring matching for fuzzy matches
    for key, code in LEGAL_BASIS_MAPPING.items():
        if key.replace("_", " ") in basis_lower or basis_lower in key:
            return code

    return "IX"  # Fallback


def join_array_or_string(value: Any, sep: str = ";") -> str:
    """
    Join array values or convert single string to text.
    Fixes encoding issues in the process.

    Args:
        value: String, list, or other
        sep: Separator for joining

    Returns:
        Joined string or original string, stripped
    """
    if isinstance(value, list):
        return sep.join(fix_encoding(str(v)).strip() for v in value if v)
    elif value:
        return fix_encoding(str(value)).strip()
    return ""


def sanitize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fix encoding issues in all text fields of a record.

    Args:
        record: RoPA activity record

    Returns:
        Record with fixed encoding
    """
    sanitized = {}
    for key, val in record.items():
        if isinstance(val, str):
            sanitized[key] = fix_encoding(val)
        else:
            sanitized[key] = val
    return sanitized


def map_assessment_pia_to_ropa(pia_obj: Dict[str, Any], answers: List[Dict[str, Any]],
                                measures: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Transform PIA Assessment System format to RoPA/LGPD format.

    Args:
        pia_obj: PIA object from assessment system
        answers: List of answer objects from assessment
        measures: List of measure objects from assessment

    Returns:
        Dict with RoPA field names and values
    """
    # Extract data from answers by reference_to code
    answer_map = {}
    for answer in answers:
        ref = answer.get("reference_to", "")
        data = answer.get("data", {})
        answer_map[ref] = data

    # Extract purpose from answer 111 or use category
    purpose = answer_map.get("111", {}).get("text", "")
    if not purpose:
        purpose = pia_obj.get("category", "")

    # Extract legal basis from answer 211/212
    legal_basis_text = answer_map.get("212", {}).get("text", "")
    base_legal = map_legal_basis(legal_basis_text) if legal_basis_text else "II"  # Default to legal obligation

    # Extract data subjects and categories
    data_subjects = answer_map.get("2.1.11", {}).get("text", "")
    data_categories = answer_map.get("121", {}).get("text", "")

    # Extract security measures
    measures_text = []
    for measure in measures:
        if measure.get("title") and measure.get("content"):
            measures_text.append(f"{measure['title']}: {measure['content']}")

    # Build RoPA record
    ropa_activity = {
        "nome_atividade": pia_obj.get("name", ""),
        "finalidade": purpose,
        "base_legal": base_legal,
        "categorias_titulares": data_subjects or join_array_or_string(
            answer_map.get("212", {}).get("list", []), ";"
        ),
        "categorias_dados": data_categories or join_array_or_string(
            answer_map.get("121", {}).get("list", []), ";"
        ),
        "dados_sensiveis": 1 if any(
            "sensível" in str(ans).lower() or "sensibles" in str(ans).lower()
            for ans in answer_map.values()
        ) else 0,
        "destinatarios": join_array_or_string(
            answer_map.get("112", {}).get("list", []), ";"
        ) or answer_map.get("112", {}).get("text", ""),
        "transferencia_inter": "N/A",
        "prazo_retencao": answer_map.get("215", {}).get("text", ""),
        "medidas_seguranca": join_array_or_string(measures_text, ";"),
        "unidade_controladora": pia_obj.get("category", ""),
        "observacoes": f"PIA Assessment System | {pia_obj.get('dpo_opinion', '')}",
        "sistema_sei": "",
    }

    return ropa_activity


def map_cnil_to_ropa(pia_activity: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform CNIL PIA activity to RoPA/LGPD format.

    Args:
        pia_activity: Single activity from CNIL PIA JSON

    Returns:
        Dict with RoPA field names and values
    """
    traitement = pia_activity.get("traitement", {})
    fondement = pia_activity.get("fondement_legal", {})
    personnes = pia_activity.get("personnes", {})
    donnees = pia_activity.get("donnees", {})
    responsable = pia_activity.get("responsable", {})

    # Extract legal basis (can be dict with "type" or direct string)
    legal_basis_raw = fondement.get("type") if isinstance(fondement, dict) else fondement

    ropa_activity = {
        "nome_atividade": join_array_or_string(traitement.get("nom", "")),
        "finalidade": join_array_or_string(traitement.get("finalites", []), ";"),
        "base_legal": map_legal_basis(legal_basis_raw),
        "categorias_titulares": join_array_or_string(personnes.get("categories", []), ";"),
        "categorias_dados": join_array_or_string(donnees.get("type", []), ";"),
        "dados_sensiveis": 1 if donnees.get("sensibles") else 0,
        "destinatarios": join_array_or_string(pia_activity.get("destinataires", []), ";"),
        "transferencia_inter": join_array_or_string(
            pia_activity.get("transferts_intl", {}).get("pays", []), ","
        ) or "N/A",
        "prazo_retencao": join_array_or_string(pia_activity.get("duree_conservation", "")),
        "medidas_seguranca": join_array_or_string(
            pia_activity.get("mesures_securite", []), ";"
        ),
        "unidade_controladora": join_array_or_string(responsable.get("nom", "")),
        "observacoes": join_array_or_string(pia_activity.get("description", "")),
        "sistema_sei": "",  # CNIL doesn't have SEI reference
    }

    return ropa_activity


def import_activities(
    ropa_records: List[Dict[str, Any]],
    conflict_strategy: str = "skip"
) -> Tuple[int, int, int, List[str]]:
    """
    Bulk insert RoPA activities with conflict resolution.

    Args:
        ropa_records: List of transformed RoPA activity dicts
        conflict_strategy: "skip" | "merge" | "overwrite"

    Returns:
        (inserted_count, skipped_count, error_count, error_messages)
    """
    inserted = 0
    skipped = 0
    errors = 0
    error_msgs = []

    conn = get_conn()
    try:
        for idx, record in enumerate(ropa_records):
            try:
                # Validate required field
                if not record.get("nome_atividade"):
                    errors += 1
                    error_msgs.append(f"Registro [{idx}] sem nome_atividade")
                    continue

                # Check for duplicate
                existing = conn.execute(
                    "SELECT id FROM atividades WHERE nome_atividade = ? AND ativo = 1",
                    (record["nome_atividade"],)
                ).fetchone()

                if existing:
                    if conflict_strategy == "skip":
                        skipped += 1
                        continue
                    elif conflict_strategy == "overwrite":
                        # Mark old as inactive
                        old_id = existing["id"]
                        conn.execute(
                            "UPDATE atividades SET ativo = 0 WHERE id = ?",
                            (old_id,)
                        )
                        # Log in historico
                        conn.execute(
                            """INSERT INTO historico (atividade_id, campo, valor_antigo, valor_novo)
                               VALUES (?, ?, ?, ?)""",
                            (old_id, "_status", "ativo", "inativo (substituído por CNIL_PIA import)")
                        )
                    elif conflict_strategy == "merge":
                        # Update with non-empty CNIL values only
                        updates = []
                        values = []
                        for key, val in record.items():
                            if val and val.strip() if isinstance(val, str) else val:
                                updates.append(f"{key} = ?")
                                values.append(val)

                        if updates:
                            values.append(existing["id"])
                            conn.execute(
                                f"UPDATE atividades SET {', '.join(updates)}, atualizado_em = datetime('now','localtime') "
                                f"WHERE id = ?",
                                values
                            )
                            # Log merge in historico
                            conn.execute(
                                """INSERT INTO historico (atividade_id, campo, valor_antigo, valor_novo)
                                   VALUES (?, ?, ?, ?)""",
                                (existing["id"], "_source", "original", "merged_with_CNIL_PIA")
                            )
                        skipped += 1
                        continue

                # Insert new activity
                cursor = conn.execute(
                    """INSERT INTO atividades
                       (nome_atividade, finalidade, base_legal, categorias_titulares,
                        categorias_dados, dados_sensiveis, destinatarios, transferencia_inter,
                        prazo_retencao, medidas_seguranca, unidade_controladora, observacoes)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        record["nome_atividade"],
                        record.get("finalidade", ""),
                        record.get("base_legal", "IX"),
                        record.get("categorias_titulares", ""),
                        record.get("categorias_dados", ""),
                        record.get("dados_sensiveis", 0),
                        record.get("destinatarios", ""),
                        record.get("transferencia_inter", "N/A"),
                        record.get("prazo_retencao", ""),
                        record.get("medidas_seguranca", ""),
                        record.get("unidade_controladora", ""),
                        record.get("observacoes", ""),
                    )
                )

                # Get inserted activity ID for audit trail (from cursor)
                new_id = cursor.lastrowid

                # Log import in historico
                conn.execute(
                    """INSERT INTO historico (atividade_id, campo, valor_antigo, valor_novo)
                       VALUES (?, ?, ?, ?)""",
                    (new_id, "_source", "null", "CNIL_PIA_IMPORT")
                )

                inserted += 1
                conn.commit()

            except Exception as e:
                errors += 1
                error_msgs.append(f"Registro [{idx}] erro: {str(e)}")
                conn.rollback()
    finally:
        conn.close()

    return inserted, skipped, errors, error_msgs


def import_from_content(
    content: str,
    conflict_strategy: str = "skip"
) -> Tuple[int, int, int, List[str]]:
    """
    Import CNIL PIA JSON from string content.
    Supports both simple format and assessment system format.

    Args:
        content: JSON string content
        conflict_strategy: "skip" | "merge" | "overwrite"

    Returns:
        (inserted, skipped, errors, error_messages)
    """
    # Parse and validate JSON
    try:
        pia_data = parse_cnil_json(content)
    except ValueError as e:
        return 0, 0, 1, [str(e)]

    # Validate schema
    is_valid, validation_errors = validate_cnil_pia_schema(pia_data)
    if not is_valid:
        return 0, 0, 1, validation_errors

    # Detect format and transform
    format_type = detect_pia_format(pia_data)
    ropa_records = []
    transform_errors = []

    if format_type == "simple":
        # Simple format: array of activities
        atividades = pia_data.get("atividades", [])
        for idx, activity in enumerate(atividades):
            try:
                ropa_record = map_cnil_to_ropa(activity)
                ropa_record = sanitize_record(ropa_record)  # Fix encoding
                ropa_records.append(ropa_record)
            except Exception as e:
                transform_errors.append(f"Atividade simples [{idx}] transformação falhou: {str(e)}")

    elif format_type == "assessment":
        # Assessment system format: single PIA with answers and measures
        try:
            pia_obj = pia_data.get("pia", {})
            answers = pia_data.get("answers", [])
            measures = pia_data.get("measures", [])

            ropa_record = map_assessment_pia_to_ropa(pia_obj, answers, measures)
            ropa_record = sanitize_record(ropa_record)  # Fix encoding
            ropa_records.append(ropa_record)
        except Exception as e:
            transform_errors.append(f"Avaliação de impacto (assessment) transformação falhou: {str(e)}")

    # Import to database
    inserted, skipped, errors, import_errors = import_activities(ropa_records, conflict_strategy)

    all_errors = transform_errors + import_errors

    return inserted, skipped, len(all_errors), all_errors


def import_from_file(
    file_path: str,
    conflict_strategy: str = "skip"
) -> Tuple[int, int, int, List[str]]:
    """
    Import CNIL PIA JSON from file path.
    Auto-detects file encoding (UTF-8, Latin-1, etc).

    Args:
        file_path: Path to .json file
        conflict_strategy: "skip" | "merge" | "overwrite"

    Returns:
        (inserted, skipped, errors, error_messages)
    """
    content = None
    encodings = ["utf-8", "latin-1", "iso-8859-1", "cp1252"]

    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding) as f:
                content = f.read()
            break  # Success
        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception as e:
            return 0, 0, 1, [f"Erro ao ler arquivo: {str(e)}"]

    if content is None:
        return 0, 0, 1, ["Não foi possível decodificar arquivo. Tente com UTF-8 ou Latin-1."]

    return import_from_content(content, conflict_strategy)
