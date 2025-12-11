"""
フォーマット変換ユーティリティ
TSV出力、表示用HTML生成など
"""
import csv
from typing import List, Dict, Any
from io import StringIO, BytesIO
import pandas as pd
from config import Config
from utils.logger import logger


def matrix_to_tsv(matrix: List[List[str]]) -> str:
    """
    マトリクスデータをTSV形式に変換
    
    Args:
        matrix: マトリクスデータ（2次元リスト）
        
    Returns:
        TSV形式の文字列
    """
    output = StringIO()
    writer = csv.writer(output, delimiter='\t', lineterminator='\n')
    
    for row in matrix:
        writer.writerow(row)
    
    tsv_content = output.getvalue()
    output.close()
    
    logger.info(f"マトリクスをTSV形式に変換しました（{len(matrix)}行）")
    return tsv_content


def matrix_to_excel_bytes(matrix: List[List[str]]) -> bytes:
    """マトリクスデータをExcelファイルバイト列に変換"""
    if not matrix:
        logger.warning("空のマトリクスをExcelに変換しようとしました")
        df = pd.DataFrame()
    else:
        # 先頭行をヘッダーとしてDataFrame化
        df = pd.DataFrame(matrix[1:], columns=matrix[0])

    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="matrix")

    excel_bytes = output.getvalue()
    output.close()
    logger.info(f"マトリクスをExcel形式に変換しました（{len(matrix)}行）")
    return excel_bytes


def matrix_to_html(matrix: List[List[str]], highlight_symbols: bool = True) -> str:
    """
    マトリクスデータをHTML tableに変換
    
    Args:
        matrix: マトリクスデータ（2次元リスト）
        highlight_symbols: 評価記号に色を付けるか
        
    Returns:
        HTML文字列
    """
    if not matrix:
        return "<p>マトリクスデータがありません</p>"
    
    html = ['<table style="border-collapse: collapse; width: 100%;">']
    
    # ヘッダー行
    html.append('<thead><tr>')
    for cell in matrix[0]:
        html.append(f'<th style="border: 1px solid #ddd; padding: 8px; background-color: #f2f2f2;">{cell}</th>')
    html.append('</tr></thead>')
    
    # データ行
    html.append('<tbody>')
    for row in matrix[1:]:
        html.append('<tr>')
        for cell in row:
            # 評価記号のハイライト
            cell_html = cell
            if highlight_symbols:
                if cell == "〇":
                    cell_html = f'<span style="color: #2ecc71; font-weight: bold;">{cell}</span>'
                elif cell == "△":
                    cell_html = f'<span style="color: #f39c12; font-weight: bold;">{cell}</span>'
                elif cell == "▲":
                    cell_html = f'<span style="color: #e74c3c; font-weight: bold;">{cell}</span>'
            
            html.append(f'<td style="border: 1px solid #ddd; padding: 8px;">{cell_html}</td>')
        html.append('</tr>')
    html.append('</tbody>')
    
    html.append('</table>')
    
    logger.info(f"マトリクスをHTML形式に変換しました（{len(matrix)}行）")
    return ''.join(html)


def personas_to_markdown(personas: List[Dict[str, Any]]) -> str:
    """
    ペルソナリストをMarkdown形式に変換
    
    Args:
        personas: ペルソナリスト
        
    Returns:
        Markdown文字列
    """
    md = ["## ペルソナ一覧\n"]
    
    for i, persona in enumerate(personas, start=1):
        md.append(f"### {i}. {persona.get('id', f'P{i}')}\n")
        md.append(f"- **業界**: {persona.get('industry', 'N/A')}\n")
        md.append(f"- **職種**: {persona.get('job_type', 'N/A')}\n")
        
        companies = persona.get('companies', [])
        if isinstance(companies, list):
            companies_str = "、".join(companies)
        else:
            companies_str = str(companies)
        md.append(f"- **在籍企業イメージ**: {companies_str}\n")
        md.append("\n")
    
    logger.info(f"{len(personas)}件のペルソナをMarkdown形式に変換しました")
    return ''.join(md)


def axes_to_markdown(axes: List[Dict[str, Any]]) -> str:
    """
    分析軸リストをMarkdown形式に変換
    
    Args:
        axes: 分析軸リスト
        
    Returns:
        Markdown文字列
    """
    md = ["## 分析軸一覧\n"]
    
    # カテゴリごとにグループ化
    categories = {}
    for axis in axes:
        category = axis.get('category', 'その他')
        if category not in categories:
            categories[category] = []
        categories[category].append(axis.get('item', 'N/A'))
    
    for category in Config.CATEGORIES:
        if category in categories:
            md.append(f"### 【{category}】\n")
            for item in categories[category]:
                md.append(f"- {item}\n")
            md.append("\n")
    
    # その他のカテゴリ
    for category, items in categories.items():
        if category not in Config.CATEGORIES:
            md.append(f"### 【{category}】\n")
            for item in items:
                md.append(f"- {item}\n")
            md.append("\n")
    
    logger.info(f"{len(axes)}件の分析軸をMarkdown形式に変換しました")
    return ''.join(md)


def format_confidence_score(score: float) -> tuple:
    """
    自信度スコアを色分けとメッセージに変換
    
    Args:
        score: 自信度スコア（0.0-1.0）
        
    Returns:
        (色, メッセージ) のタプル
    """
    if score >= 0.8:
        return ("green", "高信頼")
    elif score >= 0.65:
        return ("blue", "標準")
    else:
        return ("orange", "要確認")
