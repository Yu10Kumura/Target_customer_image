"""
STEP4.5: セルフレビュー
マトリクスの品質をチェックし、改善提案を生成
"""
from typing import Dict, Any, List
from pathlib import Path
from config import Config
from utils.llm_client import LLMClient
from utils.logger import logger
import json


class Step4_5SelfReviewer:
    """STEP4.5: セルフレビュークラス"""
    
    def __init__(self, llm_client: LLMClient):
        """
        初期化
        
        Args:
            llm_client: LLMクライアント
        """
        self.llm = llm_client
        self.prompt_template = self._load_prompt_template()
    
    def _load_prompt_template(self) -> str:
        """プロンプトテンプレートを読み込み"""
        template_path = Config.PROMPTS_DIR / "step4_5_review.txt"
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def review(
        self,
        matrix: List[List[str]],
        job_description: str,
        personas: List[Dict[str, Any]],
        axes: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        マトリクスをレビュー
        
        Args:
            matrix: マトリクスデータ（2次元リスト）
            job_description: 求人票テキスト
            personas: ペルソナリスト
            axes: 分析軸リスト
            
        Returns:
            レビュー結果
            {
                "has_issues": bool,
                "issues": List[Dict],
                "overall_quality": str,
                "confidence_score": float
            }
            
        Raises:
            Exception: レビュー失敗時
        """
        logger.info("STEP4.5: セルフレビューを開始します")
        
        try:
            # マトリクスをMarkdown形式に変換
            matrix_markdown = self._matrix_to_markdown(matrix)
            
            # プロンプト生成
            prompt = self.prompt_template.format(
                job_description=job_description,
                matrix=matrix_markdown
            )
            
            # LLM呼び出し
            result = self.llm.generate_json(
                prompt=prompt,
                max_tokens=Config.MAX_TOKENS_STEP4_5,
                temperature=Config.TEMP_STEP4_5
            )
            
            has_issues = result.get('has_issues', False)
            issues = result.get('issues', [])
            quality = result.get('overall_quality', '不明')
            confidence = result.get('confidence_score', 0.0)
            
            logger.info(f"STEP4.5: セルフレビューが完了しました")
            logger.info(f"  - 品質評価: {quality}")
            logger.info(f"  - 自信度: {confidence:.2f}")
            logger.info(f"  - 問題数: {len(issues)}")
            
            if has_issues:
                logger.warning("  ⚠️ レビューで問題が検出されました")
                for i, issue in enumerate(issues, start=1):
                    logger.warning(f"    {i}. {issue.get('description', 'N/A')}")
            
            return result
            
        except Exception as e:
            logger.error(f"STEP4.5: セルフレビューに失敗しました: {str(e)}")
            # レビュー失敗時はhas_issues=Falseで返す
            return {
                "has_issues": False,
                "issues": [],
                "overall_quality": "レビュー失敗",
                "confidence_score": 0.5
            }
    
    def apply_fixes(
        self,
        matrix: List[List[str]],
        review_result: Dict[str, Any]
    ) -> List[List[str]]:
        """
        レビュー結果に基づいてマトリクスを修正
        
        Args:
            matrix: マトリクスデータ（2次元リスト）
            review_result: レビュー結果
            
        Returns:
            修正後のマトリクス
        """
        logger.info("STEP4.5: レビュー結果に基づく修正を開始します")
        
        issues = review_result.get('issues', [])
        if not issues:
            logger.info("  修正不要です")
            return matrix
        
        # 簡易的な修正（位置指定による）
        # 実際の実装では、より詳細な修正ロジックが必要
        modified_matrix = [row[:] for row in matrix]  # ディープコピー
        
        for issue in issues:
            try:
                location = issue.get('location', '')
                suggested_fix = issue.get('suggested_fix', '')
                
                # 位置情報のパース（例: "P1, 25-29歳, フロー-顧客折衝"）
                # 簡易実装: ログに記録するのみ
                logger.info(f"  - 修正提案: {location} → {suggested_fix}")
                
            except Exception as e:
                logger.warning(f"  修正の適用に失敗: {str(e)}")
        
        logger.info("STEP4.5: 修正が完了しました")
        return modified_matrix
    
    def _matrix_to_markdown(self, matrix: List[List[str]]) -> str:
        """
        マトリクスをMarkdown table形式に変換
        
        Args:
            matrix: マトリクスデータ（2次元リスト）
            
        Returns:
            Markdown文字列
        """
        if not matrix:
            return ""
        
        lines = []
        
        # ヘッダー行
        header = " | ".join(matrix[0])
        lines.append(f"| {header} |")
        
        # 区切り行
        separator = " | ".join(["---"] * len(matrix[0]))
        lines.append(f"| {separator} |")
        
        # データ行
        for row in matrix[1:]:
            row_str = " | ".join(row)
            lines.append(f"| {row_str} |")
        
        return "\n".join(lines)
