from typing import List, Dict, Any

from utils.logger import logger


def sync_matrix_companies_with_personas(
    matrix: List[List[str]],
    personas: List[Dict[str, Any]],
) -> List[List[str]]:
    """マトリクスの在籍企業イメージ列をペルソナのcompaniesと同期する。

    - ヘッダーから「ペルソナID/年齢」「在籍企業イメージ」列を特定
    - 各行のペルソナIDに対応するpersonas[*].companiesを結合して上書き
    - 評価セルなどその他の列は一切変更しない
    """

    if not matrix or len(matrix) < 2:
        return matrix

    header = matrix[0]
    try:
        id_col = header.index("ペルソナID/年齢")
        companies_col = header.index("在籍企業イメージ")
    except ValueError:
        # 想定の列がない場合は何もしない
        return matrix

    persona_companies: Dict[str, Any] = {}
    for p in personas or []:
        pid = p.get("id")
        if not pid:
            continue
        persona_companies[pid] = p.get("companies", [])

    updated_rows = 0
    for row in matrix[1:]:
        if len(row) <= max(id_col, companies_col):
            continue

        cell = row[id_col]
        persona_id = (cell.split("/", 1)[0] or "").strip()
        if not persona_id:
            continue

        companies = persona_companies.get(persona_id)
        if companies is None:
            continue

        if isinstance(companies, list):
            companies_str = "、".join(str(c) for c in companies)
        else:
            companies_str = str(companies)

        row[companies_col] = companies_str
        updated_rows += 1

    if updated_rows > 0:
        logger.info(f"🔄 [SYNC] 在籍企業イメージ列を同期しました（{updated_rows}行）")

    return matrix
