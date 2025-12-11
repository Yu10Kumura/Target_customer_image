"""
STEP3: 分析軸生成
フロー、役割、使用技術、経験例の4カテゴリの分析軸を生成
"""
from typing import Dict, Any, List
from pathlib import Path
from config import Config
from utils.llm_client import LLMClient
from utils.validators import validate_axes
from utils.logger import logger
import json


class Step3AxesGenerator:
    """STEP3: 分析軸生成クラス"""
    
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
        template_path = Config.PROMPTS_DIR / "step3_axes.txt"
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def generate_axes(
        self,
        job_description: str,
        analysis: Dict[str, Any],
        personas: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        分析軸を生成
        
        Args:
            job_description: 求人票テキスト
            analysis: STEP1の分析結果
            personas: STEP2のペルソナリスト
            
        Returns:
            分析軸リスト
            [
                {
                    "category": "フロー",
                    "item": "顧客折衝"
                },
                ...
            ]
            
        Raises:
            Exception: 生成失敗時
        """
        logger.info("STEP3: 分析軸生成を開始します")
        
        try:
            # プロンプト生成
            prompt = self.prompt_template.format(
                job_description=job_description,
                analysis=json.dumps(analysis, ensure_ascii=False, indent=2),
                personas=json.dumps(personas, ensure_ascii=False, indent=2)
            )
            
            # LLM呼び出し
            result = self.llm.generate_json(
                prompt=prompt,
                max_tokens=Config.MAX_TOKENS_STEP3,
                temperature=Config.TEMP_STEP3
            )
            
            # 分析軸リスト抽出
            axes = result.get('axes', [])
            
            # バリデーション
            validate_axes(axes)
            
            # カテゴリ別集計
            category_count = {}
            for axis in axes:
                category = axis.get('category', 'その他')
                category_count[category] = category_count.get(category, 0) + 1
            
            logger.info(f"STEP3: 分析軸生成が完了しました（合計: {len(axes)}軸）")
            for category, count in category_count.items():
                logger.info(f"  - {category}: {count}軸")
            
            return axes
            
        except Exception as e:
            logger.error(f"STEP3: 分析軸生成に失敗しました: {str(e)}")
            raise
    
    def update_axes(
        self,
        existing_axes: List[Dict[str, Any]],
        new_personas: List[Dict[str, Any]],
        job_description: str
    ) -> List[Dict[str, Any]]:
        """
        新規ペルソナ追加時に分析軸を更新（必要に応じて追加）
        
        Args:
            existing_axes: 既存の分析軸リスト
            new_personas: 新規追加されたペルソナリスト
            job_description: 求人票テキスト
            
        Returns:
            更新後の分析軸リスト
            
        Raises:
            Exception: 更新失敗時
        """
        logger.info("STEP3: 分析軸の更新を開始します")
        
        try:
            # 追加が必要かLLMに判断させる
            prompt = f"""
以下の新規ペルソナが追加されました。
既存の分析軸で十分評価できるか、それとも新しい分析軸の追加が必要か判断してください。

【新規ペルソナ】
{json.dumps(new_personas, ensure_ascii=False, indent=2)}

【既存の分析軸】
{json.dumps(existing_axes, ensure_ascii=False, indent=2)}

【求人票】
{job_description}

追加が必要な場合は、以下のJSON形式で返してください:
{{
  "needs_update": true,
  "additional_axes": [
    {{
      "category": "カテゴリ名",
      "item": "項目名"
    }}
  ]
}}

追加不要の場合は:
{{
  "needs_update": false,
  "additional_axes": []
}}
"""
            
            result = self.llm.generate_json(
                prompt=prompt,
                max_tokens=Config.MAX_TOKENS_STEP3,
                temperature=Config.TEMP_STEP3
            )
            
            if result.get('needs_update', False):
                additional_axes = result.get('additional_axes', [])
                updated_axes = existing_axes + additional_axes
                logger.info(f"STEP3: 分析軸を更新しました（{len(additional_axes)}軸追加）")
                return updated_axes
            else:
                logger.info("STEP3: 分析軸の更新は不要と判断されました")
                return existing_axes
            
        except Exception as e:
            logger.error(f"STEP3: 分析軸の更新に失敗しました: {str(e)}")
            # エラー時は既存軸をそのまま返す
            return existing_axes
