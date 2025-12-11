"""
バリデーション関数
データ構造の検証
"""
from typing import Dict, Any, List
from config import Config
from utils.logger import logger


def validate_persona(persona: Dict[str, Any]) -> bool:
    """
    ペルソナデータのバリデーション
    
    Args:
        persona: ペルソナデータ
        
    Returns:
        バリデーション成功時はTrue
        
    Raises:
        ValueError: バリデーション失敗時
    """
    required_keys = ["id", "industry", "job_type", "companies"]
    
    for key in required_keys:
        if key not in persona:
            raise ValueError(f"ペルソナに必須項目 '{key}' が欠落しています")
    
    # 企業リストのチェック
    companies = persona.get("companies", [])
    if not isinstance(companies, list):
        raise ValueError("companiesはリスト型である必要があります")
    
    if len(companies) < 3 or len(companies) > 10:
        raise ValueError(f"企業数は3-10社である必要があります（現在: {len(companies)}社）")
    
    logger.info(f"ペルソナ '{persona['id']}' のバリデーション成功")
    return True


def validate_personas(personas: List[Dict[str, Any]], expected_count: int = None) -> bool:
    """
    複数ペルソナのバリデーション
    
    Args:
        personas: ペルソナリスト
        expected_count: 期待されるペルソナ数（Noneの場合はチェックしない）
        
    Returns:
        バリデーション成功時はTrue
        
    Raises:
        ValueError: バリデーション失敗時
    """
    if expected_count is not None and len(personas) != expected_count:
        raise ValueError(
            f"ペルソナ数が期待値と異なります（期待: {expected_count}、実際: {len(personas)}）"
        )
    
    for persona in personas:
        validate_persona(persona)
    
    logger.info(f"{len(personas)}件のペルソナのバリデーション成功")
    return True


def validate_axes(axes: List[Dict[str, Any]]) -> bool:
    """
    分析軸データのバリデーション
    
    Args:
        axes: 分析軸リスト
        
    Returns:
        バリデーション成功時はTrue
        
    Raises:
        ValueError: バリデーション失敗時
    """
    if not axes:
        raise ValueError("分析軸が空です")
    
    required_keys = ["category", "item"]
    
    for i, axis in enumerate(axes):
        for key in required_keys:
            if key not in axis:
                raise ValueError(f"分析軸[{i}]に必須項目 '{key}' が欠落しています")
        
        # カテゴリチェック
        category = axis.get("category", "")
        if category not in Config.CATEGORIES:
            logger.warning(
                f"分析軸[{i}]のカテゴリ '{category}' が標準カテゴリに含まれていません。"
                f"標準: {Config.CATEGORIES}"
            )
    
    logger.info(f"{len(axes)}件の分析軸のバリデーション成功")
    return True


def validate_matrix(matrix: List[List[str]], expected_rows: int = None) -> bool:
    """
    マトリクスデータのバリデーション
    
    Args:
        matrix: マトリクスデータ（2次元リスト）
        expected_rows: 期待される行数（Noneの場合はチェックしない）
        
    Returns:
        バリデーション成功時はTrue
        
    Raises:
        ValueError: バリデーション失敗時
    """
    if not matrix:
        raise ValueError("マトリクスが空です")
    
    # ヘッダー行を含む行数チェック
    if expected_rows is not None:
        actual_rows = len(matrix)
        if actual_rows != expected_rows + 1:  # ヘッダー+データ行
            raise ValueError(
                f"マトリクスの行数が期待値と異なります（期待: {expected_rows + 1}、実際: {actual_rows}）"
            )
    
    # 列数の一貫性チェック
    if matrix:
        header_cols = len(matrix[0])
        for i, row in enumerate(matrix[1:], start=1):
            if len(row) != header_cols:
                raise ValueError(
                    f"マトリクスの行[{i}]の列数が不正です（期待: {header_cols}、実際: {len(row)}）"
                )
    
    logger.info(f"マトリクスのバリデーション成功（{len(matrix)}行 × {len(matrix[0]) if matrix else 0}列）")
    return True


def validate_discussion_points(discussion_points: str) -> bool:
    """
    論点データのバリデーション
    
    Args:
        discussion_points: 論点テキスト（Markdown）
        
    Returns:
        バリデーション成功時はTrue
        
    Raises:
        ValueError: バリデーション失敗時
    """
    if not discussion_points or not discussion_points.strip():
        raise ValueError("論点が空です")
    
    # 3つの論点が含まれているかチェック（簡易版）
    required_sections = ["論点】", "仮説と根拠", "確認したい論点"]
    for section in required_sections:
        if section not in discussion_points:
            logger.warning(f"論点に '{section}' セクションが見つかりません")
    
    logger.info("論点のバリデーション成功")
    return True


def validate_step1_result(result: Dict[str, Any]) -> bool:
    """
    STEP1結果のバリデーション
    
    Args:
        result: STEP1の分析結果
        
    Returns:
        バリデーション成功時はTrue
        
    Raises:
        ValueError: バリデーション失敗時
    """
    required_keys = ["job_title", "key_skills", "job_domain", "role"]
    
    for key in required_keys:
        if key not in result:
            raise ValueError(f"STEP1結果に必須項目 '{key}' が欠落しています")
    
    logger.info("STEP1結果のバリデーション成功")
    return True
