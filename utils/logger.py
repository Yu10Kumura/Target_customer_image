"""
ログ設定ユーティリティ
"""
import logging
from pathlib import Path
from config import Config


def setup_logger(name: str = __name__) -> logging.Logger:
    """
    ログ設定を初期化
    
    Args:
        name: ロガー名
        
    Returns:
        設定済みロガー
    """
    # ログディレクトリ作成
    Config.LOG_DIR.mkdir(exist_ok=True)
    
    # ロガー設定
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    
    # ハンドラーが既に設定されている場合はスキップ
    if logger.handlers:
        return logger
    
    # ファイルハンドラー
    file_handler = logging.FileHandler(
        Config.LOG_DIR / Config.LOG_FILE,
        encoding='utf-8'
    )
    file_handler.setFormatter(logging.Formatter(Config.LOG_FORMAT))
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(Config.LOG_FORMAT))
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# デフォルトロガー
logger = setup_logger()
