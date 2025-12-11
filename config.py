"""
設定ファイル
GPT-5-mini対応版
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# config.envファイルの読み込み（明示的にファイル名指定）
BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / 'config.env')


class Config:
    """システム設定"""
    
    # ==================== プロジェクト設定 ====================
    BASE_DIR = Path(__file__).parent
    LOG_DIR = BASE_DIR / "logs"
    PROMPTS_DIR = BASE_DIR / "prompts"
    
    # ==================== OpenAI API設定 ====================
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = "gpt-5-mini"  # GPT-5 mini正式版
    
    # ==================== トークン制限(ステップ別）====================
    # GPT-5-miniは最大出力16,384トークン対応
    MAX_TOKENS_STEP1 = 3000      # 求人票分析（詳細抽出）
    MAX_TOKENS_STEP2 = 4000      # ペルソナ生成（3パターン×詳細）
    MAX_TOKENS_STEP3 = 6000      # 分析軸生成（4カテゴリ×各5-10項目 = 20-40軸）
    MAX_TOKENS_STEP4 = 16384     # マトリクス評価（9行×多数列、物理的最大値）
    MAX_TOKENS_STEP4_5 = 6000    # セルフレビュー（包括的チェック）
    MAX_TOKENS_STEP5 = 5000      # 論点抽出（3論点×詳細）
    MAX_TOKENS_STEP6 = 1000      # 確認メッセージ
    MAX_TOKENS_QA = 3000         # Q&A（詳細回答）
    MAX_TOKENS_MODIFICATION = 4000  # 修正依頼（再生成）
    
    # ==================== Temperature設定（ステップ別）====================
    # GPT-5-miniはtemperature=1.0固定（カスタム値は未サポート）
    TEMP_STEP1 = 1.0    # 分析
    TEMP_STEP2 = 1.0    # ペルソナ生成
    TEMP_STEP3 = 1.0    # 分析軸
    TEMP_STEP4 = 1.0    # 評価
    TEMP_STEP4_5 = 1.0  # レビュー
    TEMP_STEP5 = 1.0    # 論点
    TEMP_STEP6 = 1.0    # メッセージ
    TEMP_QA = 1.0       # Q&A
    TEMP_MODIFICATION = 1.0  # 修正
    
    # ==================== リトライ設定 ====================
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # 秒
    
    # ==================== ログ設定 ====================
    LOG_LEVEL = "INFO"
    LOG_FILE = "system.log"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # ==================== 元プロンプトの固定値 ====================
    DEFAULT_NUM_PERSONAS = 3  # 初回は必ず3パターン
    DEFAULT_AGE_RANGES = ["25-29", "30-39", "40-49"]  # 年齢レンジ固定
    MATRIX_ROWS = 9  # 3ペルソナ × 3年齢 = 9行
    
    # ==================== 評価記号（元プロンプトに準拠）====================
    EVALUATION_SYMBOLS = {
        "high": "〇",      # やってる
        "medium": "△",    # やってるかも
        "low": "▲",       # やっていない
        "none": ""        # 関連なし
    }
    
    # ==================== カテゴリ（元プロンプトに準拠）====================
    CATEGORIES = ["フロー", "役割", "使用技術", "経験例"]
    
    # ==================== ファイル設定 ====================
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    SUPPORTED_FILE_TYPES = ["txt", "csv", "tsv", "docx", "pdf"]
    
    # ==================== Q&A設定 ====================
    MAX_QA_HISTORY = 20
    QA_HISTORY_MAX_ITEMS = 10
    QA_HISTORY_MAX_CHARS = 10000
    
    # ==================== コスト情報（参考）====================
    # GPT-5-mini料金（2025年12月現在）
    INPUT_COST_PER_1M = 0.250   # $0.250 / 1M tokens
    OUTPUT_COST_PER_1M = 2.000  # $2.000 / 1M tokens
    CACHED_INPUT_COST_PER_1M = 0.025  # $0.025 / 1M tokens (キャッシュ)
    
    @classmethod
    def get_summary(cls) -> dict:
        """設定のサマリーを取得"""
        return {
            "model": cls.OPENAI_MODEL,
            "default_personas": cls.DEFAULT_NUM_PERSONAS,
            "age_ranges": cls.DEFAULT_AGE_RANGES,
            "matrix_rows": cls.MATRIX_ROWS,
            "categories": cls.CATEGORIES,
            "max_retries": cls.MAX_RETRIES,
            "log_level": cls.LOG_LEVEL
        }
