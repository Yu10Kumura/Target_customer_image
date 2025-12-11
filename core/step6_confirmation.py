"""
STEP6: 確認メッセージ生成
ユーザーへの最終確認メッセージを生成
"""
from typing import List
from pathlib import Path
from config import Config
from utils.logger import logger


class Step6ConfirmationGenerator:
    """STEP6: 確認メッセージ生成クラス"""
    
    def __init__(self):
        """初期化"""
        self.message_template = self._load_message_template()
    
    def _load_message_template(self) -> str:
        """メッセージテンプレートを読み込み"""
        template_path = Config.PROMPTS_DIR / "step6_confirmation.txt"
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def generate_confirmation_message(
        self,
        matrix: List[List[str]],
        discussion_points: str
    ) -> str:
        """
        確認メッセージを生成
        
        Args:
            matrix: マトリクスデータ（2次元リスト）
            discussion_points: 論点ガイド（Markdown）
            
        Returns:
            確認メッセージ（Markdown形式）
        """
        logger.info("STEP6: 確認メッセージを生成します")
        
        try:
            # マトリクスをMarkdown形式に変換
            matrix_markdown = self._matrix_to_markdown(matrix)
            
            # メッセージ生成
            message = self.message_template.format(
                matrix_markdown=matrix_markdown,
                discussion_points=discussion_points
            )
            
            logger.info("STEP6: 確認メッセージが生成されました")
            return message
            
        except Exception as e:
            logger.error(f"STEP6: 確認メッセージ生成に失敗しました: {str(e)}")
            # フォールバック
            return "エラーが発生しました。生成結果を確認してください。"
    
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
