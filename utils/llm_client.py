"""
LLMクライアント
OpenAI API呼び出しラッパー（GPT-5-mini対応）
"""
import json
import time
from typing import Dict, Any, Optional
from openai import OpenAI
from config import Config
from utils.logger import logger


class LLMClient:
    """OpenAI API呼び出しクライアント"""
    
    def __init__(self, api_key: str = None):
        """
        初期化
        
        Args:
            api_key: OpenAI API Key（Noneの場合はConfig.OPENAI_API_KEYを使用）
        """
        self.api_key = api_key or Config.OPENAI_API_KEY
        self.client = OpenAI(api_key=self.api_key)
        self.model = Config.OPENAI_MODEL
        
        # トークン使用量ログファイル
        self.token_log_path = Config.LOG_DIR / 'token_usage.log'
        Config.LOG_DIR.mkdir(exist_ok=True)
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        system_message: str = None
    ) -> str:
        """
        基本的なテキスト生成
        
        Args:
            prompt: プロンプト
            max_tokens: 最大トークン数（内部でmax_completion_tokensに変換）
            temperature: temperature値
            system_message: システムメッセージ
            
        Returns:
            LLMの応答テキスト
            
        Raises:
            Exception: API呼び出し失敗時
        """
        try:
            logger.info(f"LLM呼び出し開始（モデル: {self.model}）")
            
            # システムメッセージのデフォルト
            if system_message is None:
                system_message = "あなたは採用コンサルタントです。指示に従って正確に回答してください。"
            
            # API呼び出し（GPT-5ではmax_completion_tokensを使用）
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=max_tokens,
                temperature=temperature
            )
            
            # finish_reasonチェック
            finish_reason = response.choices[0].finish_reason
            result = response.choices[0].message.content
            
            # トークン制限警告（応答がある場合は警告のみ）
            if finish_reason == "length":
                logger.warning(
                    f"⚠️ トークン制限に達しました (max_completion_tokens={max_tokens})。"
                    f"応答が不完全な可能性があります。"
                )
                # 応答が空でない場合は継続
                if result and result.strip():
                    logger.info(f"トークン制限に達しましたが、部分的な応答を返します（文字数: {len(result)}）")
                    self._log_token_usage(response, len(prompt))
                    return result
            
            # 応答チェック（空の場合のみエラー）
            if result is None or not result.strip():
                logger.error(f"応答が空です。finish_reason: {finish_reason}")
                raise Exception(f"応答が空です。finish_reason: {finish_reason}")
            
            # トークン使用量ログ
            self._log_token_usage(response, len(prompt))
            
            logger.info(f"LLM呼び出し成功（応答文字数: {len(result)}）")
            return result
            
        except Exception as e:
            logger.error(f"LLM呼び出しエラー: {str(e)}")
            raise
    
    def generate_json(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        system_message: str = None
    ) -> Dict[str, Any]:
        """
        JSON形式での生成
        
        Args:
            prompt: プロンプト
            max_tokens: 最大トークン数
            temperature: temperature値
            system_message: システムメッセージ
            
        Returns:
            パース済みのJSON（辞書型）
            
        Raises:
            Exception: JSON解析失敗時
        """
        # システムメッセージにJSON指示を追加
        if system_message is None:
            system_message = (
                "あなたは採用コンサルタントです。出力は厳密にJSONのみとし、"
                "説明文・マークダウン・注釈を一切含めないでください。"
            )
        
        # テキスト生成
        response_text = self.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            system_message=system_message
        )
        
        # JSON解析
        return self._parse_json(response_text)
    
    def generate_with_retry(
        self,
        prompt: str,
        max_tokens: int = 2000,
        temperature: float = 0.7,
        system_message: str = None,
        max_retries: int = None
    ) -> str:
        """
        リトライ機能付き生成
        
        Args:
            prompt: プロンプト
            max_tokens: 最大トークン数
            temperature: temperature値
            system_message: システムメッセージ
            max_retries: 最大リトライ回数
            
        Returns:
            LLMの応答テキスト
            
        Raises:
            Exception: 全リトライ失敗時
        """
        if max_retries is None:
            max_retries = Config.MAX_RETRIES
        
        for attempt in range(max_retries):
            try:
                logger.info(f"試行 {attempt + 1}/{max_retries}")
                return self.generate(
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system_message=system_message
                )
            except Exception as e:
                error_msg = str(e)
                
                # レート制限エラーの処理
                if "rate_limit" in error_msg.lower():
                    if attempt < max_retries - 1:
                        wait_time = 2 ** attempt  # 指数バックオフ
                        logger.warning(f"レート制限発生。{wait_time}秒後にリトライします")
                        time.sleep(wait_time)
                        continue
                    else:
                        logger.error("レート制限により処理を中断しました")
                        raise Exception("OpenAI APIのレート制限により処理を中断しました")
                
                # その他のエラー
                if attempt < max_retries - 1:
                    logger.warning(f"エラー: {error_msg}。リトライします...")
                    time.sleep(Config.RETRY_DELAY)
                    continue
                else:
                    logger.error(f"全リトライ失敗: {error_msg}")
                    raise
        
        raise Exception("予期しないエラー: 最大リトライ回数に到達しました")
    
    def _parse_json(self, response_text: str, max_retries: int = 3) -> Dict[str, Any]:
        """
        JSON解析（クリーニング機能付き）
        
        Args:
            response_text: JSON文字列
            max_retries: 最大リトライ回数
            
        Returns:
            パース済みのJSON（辞書型）
            
        Raises:
            Exception: JSON解析失敗時
        """
        original_text = response_text
        
        for attempt in range(max_retries):
            try:
                logger.info(f"JSON解析試行 {attempt + 1}/{max_retries}")
                result = json.loads(response_text)
                logger.info("JSON解析成功")
                return result
                
            except json.JSONDecodeError as e:
                # Extra dataエラーの場合、最初のJSONオブジェクトのみを抽出
                if "Extra data" in str(e):
                    try:
                        decoder = json.JSONDecoder()
                        result, idx = decoder.raw_decode(response_text)
                        logger.info(f"JSON解析成功（最初のオブジェクトのみ抽出、位置: {idx}）")
                        return result
                    except Exception as extract_error:
                        logger.warning(f"最初のJSONオブジェクト抽出に失敗: {str(extract_error)}")
                
                if attempt < max_retries - 1:
                    # マークダウンコードブロック除去
                    cleaned = response_text.strip()
                    
                    if cleaned.startswith("```json"):
                        cleaned = cleaned[7:]
                    elif cleaned.startswith("```"):
                        cleaned = cleaned[3:]
                    
                    if cleaned.endswith("```"):
                        cleaned = cleaned[:-3]
                    
                    response_text = cleaned.strip()
                    logger.warning(f"JSON解析失敗。クリーニング後に再試行します")
                    continue
                else:
                    logger.error(f"JSON解析に失敗しました: {str(e)}")
                    logger.error(f"応答内容: {response_text[:500]}...")
                    
                    # 最後の手段: 最初の'{...}'を抽出
                    try:
                        text = original_text
                        start = text.find('{')
                        if start != -1:
                            depth = 0
                            in_string = False
                            escape = False
                            for i in range(start, len(text)):
                                ch = text[i]
                                if ch == '\\' and not escape:
                                    escape = True
                                    continue
                                if ch == '"' and not escape:
                                    in_string = not in_string
                                escape = False
                                if not in_string:
                                    if ch == '{':
                                        depth += 1
                                    elif ch == '}':
                                        depth -= 1
                                        if depth == 0:
                                            candidate = text[start:i+1]
                                            result = json.loads(candidate)
                                            logger.info("JSON解析成功（候補抽出後）")
                                            return result
                    except Exception as e2:
                        logger.error(f"抽出後のJSON解析も失敗: {str(e2)}")
                    
                    raise Exception(
                        f"JSON解析に失敗しました: {str(e)}\n"
                        f"応答: {original_text[:200]}..."
                    )
        
        raise Exception("予期しないエラー: JSON解析の最大リトライ回数に到達しました")
    
    def _log_token_usage(self, response: Any, prompt_len: int) -> None:
        """
        トークン使用量をログに記録
        
        Args:
            response: OpenAI APIレスポンス
            prompt_len: プロンプトの文字数
        """
        try:
            usage = response.usage if hasattr(response, 'usage') else response.get('usage', None)
            if not usage:
                return
            
            # トークン数取得
            try:
                p_t = usage.get('prompt_tokens') if isinstance(usage, dict) else getattr(usage, 'prompt_tokens', None)
                c_t = usage.get('completion_tokens') if isinstance(usage, dict) else getattr(usage, 'completion_tokens', None)
                t_t = usage.get('total_tokens') if isinstance(usage, dict) else getattr(usage, 'total_tokens', None)
            except Exception:
                p_t = c_t = t_t = None
            
            logger.info(f"トークン使用量: prompt={p_t}, completion={c_t}, total={t_t}")
            
            # ログファイルに記録
            try:
                log_data = {
                    'model': self.model,
                    'prompt_len': prompt_len,
                    'prompt_tokens': p_t,
                    'completion_tokens': c_t,
                    'total_tokens': t_t,
                }
                with open(self.token_log_path, 'a', encoding='utf-8') as fh:
                    fh.write(json.dumps(log_data, ensure_ascii=False) + "\n")
            except Exception as e:
                logger.debug(f"トークン使用ログの書き込みに失敗: {str(e)}")
                
        except Exception as e:
            logger.debug(f"トークン使用量の取得に失敗: {str(e)}")
