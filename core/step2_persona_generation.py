"""
STEP2: ペルソナ生成
求人票から3パターンのターゲットペルソナを推論
"""
from typing import Dict, Any, List
from pathlib import Path
from config import Config
from utils.llm_client import LLMClient
from utils.validators import validate_personas
from utils.logger import logger
import json


class Step2PersonaGenerator:
    """STEP2: ペルソナ生成クラス"""
    
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
        template_path = Config.PROMPTS_DIR / "step2_persona.txt"
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def generate_personas(
        self,
        job_description: str,
        analysis: Dict[str, Any],
        num_personas: int = None
    ) -> List[Dict[str, Any]]:
        """
        ペルソナを生成
        
        Args:
            job_description: 求人票テキスト
            analysis: STEP1の分析結果
            num_personas: 生成するペルソナ数（デフォルトは3）
            
        Returns:
            ペルソナリスト
            [
                {
                    "id": "P1",
                    "industry": "FA・ロボット業界",
                    "job_type": "制御エンジニア",
                    "companies": ["ファナック", "安川電機", "三菱電機", "オムロン"]
                },
                ...
            ]
            
        Raises:
            Exception: 生成失敗時
        """
        if num_personas is None:
            num_personas = Config.DEFAULT_NUM_PERSONAS
        
        logger.info(f"STEP2: ペルソナ生成を開始します（目標: {num_personas}パターン）")
        
        try:
            # プロンプト生成
            prompt = self.prompt_template.format(
                job_description=job_description,
                analysis=json.dumps(analysis, ensure_ascii=False, indent=2)
            )
            
            # LLM呼び出し
            result = self.llm.generate_json(
                prompt=prompt,
                max_tokens=Config.MAX_TOKENS_STEP2,
                temperature=Config.TEMP_STEP2
            )
            
            # ペルソナリスト抽出
            personas = result.get('personas', [])
            
            # バリデーション
            validate_personas(personas, expected_count=num_personas)
            
            logger.info(f"STEP2: ペルソナ生成が完了しました（{len(personas)}パターン）")
            for i, persona in enumerate(personas, start=1):
                logger.info(f"  {i}. {persona['id']}: {persona['industry']} / {persona['job_type']}")
            
            return personas
            
        except Exception as e:
            logger.error(f"STEP2: ペルソナ生成に失敗しました: {str(e)}")
            raise
    
    def generate_additional_personas(
        self,
        job_description: str,
        analysis: Dict[str, Any],
        existing_personas: List[Dict[str, Any]],
        additional_count: int
    ) -> List[Dict[str, Any]]:
        """
        追加ペルソナを生成（既存との重複を避ける）
        
        Args:
            job_description: 求人票テキスト
            analysis: STEP1の分析結果
            existing_personas: 既存ペルソナリスト
            additional_count: 追加するペルソナ数
            
        Returns:
            追加ペルソナリスト
            
        Raises:
            Exception: 生成失敗時
        """
        logger.info(f"STEP2: 追加ペルソナ生成を開始します（{additional_count}パターン）")
        
        try:
            # 既存ペルソナの業界・職種を抽出
            existing_summary = []
            for p in existing_personas:
                existing_summary.append(
                    f"- {p['industry']} / {p['job_type']}"
                )
            
            # プロンプト調整（既存との差別化を指示）
            prompt = self.prompt_template.format(
                job_description=job_description,
                analysis=json.dumps(analysis, ensure_ascii=False, indent=2)
            )
            
            # 既存ペルソナ情報を追加
            prompt += f"\n\n【既存ペルソナ（これらとは異なるパターンを生成してください）】\n"
            prompt += "\n".join(existing_summary)
            prompt += f"\n\n上記とは異なる{additional_count}パターンのペルソナを生成してください。"
            
            # LLM呼び出し
            result = self.llm.generate_json(
                prompt=prompt,
                max_tokens=Config.MAX_TOKENS_STEP2,
                temperature=Config.TEMP_STEP2  # GPT-5-miniは1.0のみサポート
            )
            
            # ペルソナリスト抽出
            new_personas = result.get('personas', [])
            
            # ID調整（P4, P5, ...）
            start_id = len(existing_personas) + 1
            for i, persona in enumerate(new_personas):
                persona['id'] = f"P{start_id + i}"
            
            # バリデーション
            validate_personas(new_personas, expected_count=additional_count)
            
            logger.info(f"STEP2: 追加ペルソナ生成が完了しました（{len(new_personas)}パターン）")
            for i, persona in enumerate(new_personas, start=1):
                logger.info(f"  {i}. {persona['id']}: {persona['industry']} / {persona['job_type']}")
            
            return new_personas
            
        except Exception as e:
            logger.error(f"STEP2: 追加ペルソナ生成に失敗しました: {str(e)}")
            raise
