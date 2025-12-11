"""
STEP1: 求人票分析
求人票から職務内容、スキル、役割、業務領域を抽出
"""
from typing import Dict, Any
from pathlib import Path
from config import Config
from utils.llm_client import LLMClient
from utils.validators import validate_step1_result
from utils.logger import logger


class Step1JobAnalyzer:
    """STEP1: 求人票分析クラス"""
    
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
        template_path = Config.PROMPTS_DIR / "step1_job_analysis.txt"
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def analyze(self, job_description: str) -> Dict[str, Any]:
        """
        求人票を分析
        
        Args:
            job_description: 求人票テキスト
            
        Returns:
            分析結果（辞書型）
            {
                "job_title": str,
                "key_skills": List[str],
                "job_domain": str,
                "role": str,
                "must_requirements": List[str],
                "want_requirements": List[str],
                "business_scope": str
            }
            
        Raises:
            Exception: 分析失敗時
        """
        logger.info("STEP1: 求人票分析を開始します")
        
        try:
            # プロンプト生成
            prompt = self.prompt_template.format(
                job_description=job_description
            )
            
            # LLM呼び出し
            result = self.llm.generate_json(
                prompt=prompt,
                max_tokens=Config.MAX_TOKENS_STEP1,
                temperature=Config.TEMP_STEP1
            )
            
            # バリデーション
            validate_step1_result(result)
            
            logger.info("STEP1: 求人票分析が完了しました")
            logger.info(f"  - 職種: {result.get('job_title', 'N/A')}")
            logger.info(f"  - 業務領域: {result.get('job_domain', 'N/A')}")
            logger.info(f"  - 主要スキル数: {len(result.get('key_skills', []))}")
            
            # 履歴記録
            from utils.history_logger import HistoryLogger
            history_logger = HistoryLogger(Config.LOG_DIR)
            history_logger.log_matrix_generation(
                job_title=result.get('job_title', 'N/A'),
                job_domain=result.get('job_domain', 'N/A')
            )
            
            return result
            
        except Exception as e:
            logger.error(f"STEP1: 求人票分析に失敗しました: {str(e)}")
            raise
