"""
履歴ログサービス
CSV形式で各種操作履歴を記録
"""
import csv
from pathlib import Path
from datetime import datetime
from typing import Optional


class HistoryLogger:
    """履歴ログクラス"""
    
    def __init__(self, log_dir: Path):
        """
        初期化
        
        Args:
            log_dir: ログディレクトリのパス
        """
        self.log_dir = log_dir
        self.log_dir.mkdir(exist_ok=True)
        
        # 各履歴ファイルのパス
        self.matrix_history_file = log_dir / "matrix_history.csv"
        self.modification_history_file = log_dir / "modification_history.csv"
        self.qa_history_file = log_dir / "qa_history.csv"
        
        # CSVヘッダー初期化
        self._init_csv_files()
    
    def _init_csv_files(self):
        """CSVファイルにヘッダーを作成（ファイルが存在しない場合）"""
        # マトリクス生成履歴
        if not self.matrix_history_file.exists():
            with open(self.matrix_history_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'job_title', 'job_domain'])
        
        # 修正依頼履歴
        if not self.modification_history_file.exists():
            with open(self.modification_history_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'modification_type', 'request_summary'])
        
        # Q&A履歴
        if not self.qa_history_file.exists():
            with open(self.qa_history_file, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['timestamp', 'question', 'answer_summary'])
    
    def log_matrix_generation(self, job_title: str, job_domain: str):
        """
        マトリクス生成を記録
        
        Args:
            job_title: 職種名
            job_domain: 業務領域
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.matrix_history_file, 'a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, job_title, job_domain])
    
    def log_modification(self, modification_type: str, request: str):
        """
        修正依頼を記録
        
        Args:
            modification_type: 修正タイプ（personas/axes/matrix等）
            request: 修正依頼内容
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        request_summary = request[:200] if len(request) > 200 else request
        with open(self.modification_history_file, 'a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, modification_type, request_summary])
    
    def log_qa(self, question: str, answer: str):
        """
        Q&Aを記録
        
        Args:
            question: 質問内容
            answer: 回答内容
        """
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        question_summary = question[:200] if len(question) > 200 else question
        answer_summary = answer[:200] if len(answer) > 200 else answer
        with open(self.qa_history_file, 'a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, question_summary, answer_summary])
