"""
STEP5: 論点抽出
すり合わせミーティング用の論点ガイドを生成
"""
from typing import Dict, Any, List
from pathlib import Path
from config import Config
from utils.llm_client import LLMClient
from utils.validators import validate_discussion_points
from utils.logger import logger
import json


class Step5DiscussionExtractor:
    """STEP5: 論点抽出クラス"""
    
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
        template_path = Config.PROMPTS_DIR / "step5_discussion.txt"
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def extract_discussion_points(
        self,
        matrix: List[List[str]],
        job_description: str,
        personas: List[Dict[str, Any]],
        axes: List[Dict[str, Any]]
    ) -> str:
        """
        論点を抽出
        
        Args:
            matrix: マトリクスデータ（2次元リスト）
            job_description: 求人票テキスト
            personas: ペルソナリスト
            axes: 分析軸リスト
            
        Returns:
            論点ガイド（Markdown形式）
            
        Raises:
            Exception: 抽出失敗時
        """
        logger.info("STEP5: 論点抽出を開始します")
        
        try:
            # マトリクスをMarkdown形式に変換
            matrix_markdown = self._matrix_to_markdown(matrix)
            
            # プロンプト生成
            prompt = self.prompt_template.format(
                job_description=job_description,
                matrix_markdown=matrix_markdown,
                personas=json.dumps(personas, ensure_ascii=False, indent=2),
                axes=json.dumps(axes, ensure_ascii=False, indent=2)
            )
            
            # LLM呼び出し（Markdown出力なのでgenerate_jsonではなくgenerate）
            discussion_points = self.llm.generate(
                prompt=prompt,
                max_tokens=Config.MAX_TOKENS_STEP5,
                temperature=Config.TEMP_STEP5
            )
            
            # バリデーション
            validate_discussion_points(discussion_points)
            
            logger.info("STEP5: 論点抽出が完了しました")
            
            # 論点数をカウント
            point_count = discussion_points.count("【論点】")
            logger.info(f"  - 抽出された論点数: {point_count}")
            
            return discussion_points
            
        except Exception as e:
            logger.error(f"STEP5: 論点抽出に失敗しました: {str(e)}")
            raise
    
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
