"""
STEP4: マトリクス評価
3ペルソナ × 3年齢層 = 9行のマトリクスを生成
"""
from typing import Dict, Any, List
from pathlib import Path
from config import Config
from utils.llm_client import LLMClient
from utils.validators import validate_matrix
from utils.logger import logger
import json


class Step4MatrixEvaluator:
    """STEP4: マトリクス評価クラス"""
    
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
        template_path = Config.PROMPTS_DIR / "step4_matrix.txt"
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def evaluate_matrix(
        self,
        personas: List[Dict[str, Any]],
        axes: List[Dict[str, Any]],
        analysis: Dict[str, Any],
        job_description: str,
        age_ranges: List[str] = None
    ) -> List[List[str]]:
        """
        マトリクスを評価
        
        Args:
            personas: ペルソナリスト
            axes: 分析軸リスト
            analysis: STEP1の分析結果
            job_description: 求人票テキスト
            age_ranges: 年齢レンジリスト（デフォルトは25-29, 30-39, 40-49）
            
        Returns:
            マトリクスデータ（2次元リスト）
            [
                ["ペルソナID/年齢", "業界", "職種", "在籍企業イメージ", "分析軸1", "分析軸2", ...],
                ["P1/25-29", "FA業界", "制御エンジニア", "ファナック、安川電機...", "〇", "△", ...],
                ...
            ]
            
        Raises:
            Exception: 評価失敗時
        """
        if age_ranges is None:
            age_ranges = Config.DEFAULT_AGE_RANGES
        
        logger.info(f"STEP4: マトリクス評価を開始します")
        logger.info(f"  - ペルソナ数: {len(personas)}")
        logger.info(f"  - 年齢レンジ: {len(age_ranges)}")
        logger.info(f"  - 分析軸数: {len(axes)}")
        logger.info(f"  - 期待行数: {len(personas) * len(age_ranges)}")
        logger.info(f"  - 処理方式: ペルソナごとに分割生成（トークン制限対策）")
        
        try:
            # ペルソナごとに分割してマトリクスを生成
            all_matrix_data = []
            
            for idx, persona in enumerate(personas):
                logger.info(f"  - ペルソナ {idx + 1}/{len(personas)} を処理中: {persona.get('industry', 'N/A')}")
                
                # 単一ペルソナのリストを作成
                single_persona = [persona]
                
                # プロンプト生成（1ペルソナ分のみ）
                prompt = self.prompt_template.format(
                    personas=json.dumps(single_persona, ensure_ascii=False, indent=2),
                    axes=json.dumps(axes, ensure_ascii=False, indent=2)
                )
                
                # LLM呼び出し（1ペルソナ × 3年齢 = 3行のマトリクス）
                result = self.llm.generate_json(
                    prompt=prompt,
                    max_tokens=Config.MAX_TOKENS_STEP4,
                    temperature=Config.TEMP_STEP4
                )
                
                # マトリクスデータ抽出
                matrix_data = result.get('matrix', [])
                all_matrix_data.extend(matrix_data)
                
                logger.info(f"    → {len(matrix_data)}行生成完了")
            
            # 全ペルソナのマトリクスデータを2次元リストに変換
            matrix = self._convert_to_2d_list(all_matrix_data, personas, axes, age_ranges)
            
            # バリデーション
            expected_rows = len(personas) * len(age_ranges)
            validate_matrix(matrix, expected_rows=expected_rows)
            
            logger.info(f"STEP4: マトリクス評価が完了しました")
            logger.info(f"  - 生成された行数: {len(matrix) - 1}（ヘッダー除く）")
            logger.info(f"  - 列数: {len(matrix[0])}")
            
            return matrix
            
        except Exception as e:
            logger.error(f"STEP4: マトリクス評価に失敗しました: {str(e)}")
            raise
    
    def _convert_to_2d_list(
        self,
        matrix_data: List[Dict[str, Any]],
        personas: List[Dict[str, Any]],
        axes: List[Dict[str, Any]],
        age_ranges: List[str]
    ) -> List[List[str]]:
        """
        JSON形式のマトリクスデータを2次元リストに変換
        
        Args:
            matrix_data: LLMが生成したマトリクスデータ
            personas: ペルソナリスト
            axes: 分析軸リスト
            age_ranges: 年齢レンジリスト
            
        Returns:
            2次元リストのマトリクス
        """
        # ヘッダー行を作成
        header = ["ペルソナID/年齢", "業界", "職種", "在籍企業イメージ"]
        
        # 分析軸の列ヘッダーを追加
        for axis in axes:
            column_name = f"{axis['category']} - {axis['item']}"
            header.append(column_name)
        
        # データ行を作成
        rows = [header]
        
        for row_data in matrix_data:
            persona_id = row_data.get('persona_id', '')
            age_range = row_data.get('age_range', '')
            industry = row_data.get('industry', '')
            job_type = row_data.get('job_type', '')
            companies = row_data.get('companies', '')
            
            # 企業リストを文字列に変換
            if isinstance(companies, list):
                companies = "、".join(companies)
            
            # 基本情報カラム
            row = [
                f"{persona_id}/{age_range}",
                industry,
                job_type,
                companies
            ]
            
            # 評価カラム
            evaluations = row_data.get('evaluations', {})
            for axis in axes:
                column_name = f"{axis['category']} - {axis['item']}"
                evaluation = evaluations.get(column_name, "")
                row.append(evaluation)
            
            rows.append(row)
        
        return rows
