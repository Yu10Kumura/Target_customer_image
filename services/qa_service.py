"""
Q&Aサービス
マトリクスやペルソナに関する質問に回答
"""
from typing import Dict, Any, List, Optional
from config import Config
from utils.llm_client import LLMClient
from utils.logger import logger
import json


class QAService:
    """Q&Aサービスクラス"""
    
    def __init__(self, llm_client: LLMClient):
        """
        初期化
        
        Args:
            llm_client: LLMクライアント
        """
        self.llm = llm_client
    
    def answer_question(
        self,
        question: str,
        context: Dict[str, Any],
        history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        質問に回答
        
        Args:
            question: ユーザーの質問
            context: コンテキスト（ペルソナ、マトリクスなど）
            history: 会話履歴（{'q': str, 'a': str}のリスト）
            
        Returns:
            {
                'answer': str,
                'updated_history': List[Dict[str, str]]
            }
            
        Raises:
            Exception: 回答生成失敗時
        """
        logger.info(f"Q&A: 質問を受け付けました: {question[:50]}...")
        
        if history is None:
            history = []
        
        try:
            # 履歴をトリム
            history = self._trim_qa_history(history)
            
            # コンテキストをJSON化
            try:
                context_json = json.dumps(context, ensure_ascii=False, indent=2)
            except Exception:
                context_json = str(context)
            
            # プロンプト生成
            system_msg = (
                "あなたは採用領域に詳しいアシスタントです。以下の提供コンテキストを参照して、"
                "日本語で簡潔に答えてください。必ず根拠（参照した項目名）を一言で示してください。"
            )
            
            # 履歴を会話文として整形
            history_text = ""
            if history:
                pairs = []
                for turn in history:
                    q = turn.get('q', '')
                    a = turn.get('a', '')
                    pairs.append(f"Q: {q}\nA: {a}")
                history_text = "\n\n".join(pairs)
            
            user_prompt = (
                f"CONTEXT_JSON:\n{context_json}\n\n"
                f"HISTORY:\n{history_text}\n\n"
                f"QUESTION:\n{question}\n\n"
                "---\n"
                "制約: 回答は日本語で簡潔に。長くても2000文字以内。不要な注釈やコードブロックは付けない。"
            )
            
            # LLM呼び出し
            answer = self.llm.generate(
                prompt=user_prompt,
                max_tokens=Config.MAX_TOKENS_QA,
                temperature=Config.TEMP_QA,
                system_message=system_msg
            )
            
            # 履歴に追加
            new_entry = {'q': question, 'a': answer.strip()}
            history.append(new_entry)
            history = self._trim_qa_history(history)
            
            logger.info(f"Q&A: 回答を生成しました（{len(answer)}文字）")
            
            # 履歴記録
            from utils.history_logger import HistoryLogger
            history_logger = HistoryLogger(Config.LOG_DIR)
            history_logger.log_qa(
                question=question,
                answer=answer.strip()
            )
            
            return {'answer': answer.strip(), 'updated_history': history}
            
        except Exception as e:
            logger.error(f"Q&A: 回答生成に失敗しました: {str(e)}")
            raise
    
    def _trim_qa_history(self, history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        会話履歴を上限に合わせてトリム
        
        Args:
            history: 会話履歴
            
        Returns:
            トリム後の履歴
        """
        if not history:
            return []
        
        # 最新から切り取る
        max_items = Config.QA_HISTORY_MAX_ITEMS
        max_chars = Config.QA_HISTORY_MAX_CHARS
        
        trimmed = history[-max_items:]
        
        # 文字数が多ければ先頭から削る
        total = sum(len(json.dumps(item, ensure_ascii=False)) for item in trimmed)
        while total > max_chars and trimmed:
            trimmed.pop(0)
            total = sum(len(json.dumps(item, ensure_ascii=False)) for item in trimmed)
        
        return trimmed
