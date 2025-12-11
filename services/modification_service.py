"""
修正依頼サービス
ユーザーの自然言語による修正依頼を処理
"""
from typing import Dict, Any, List
from config import Config
from utils.llm_client import LLMClient
from utils.logger import logger
import json
import copy


class ModificationService:
    """修正依頼サービスクラス"""
    
    def __init__(self, llm_client: LLMClient):
        """
        初期化
        
        Args:
            llm_client: LLMクライアント
        """
        self.llm = llm_client
    
    def process_modification_request(
        self,
        request: str,
        current_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        修正依頼を処理
        
        Args:
            request: 修正依頼（自然言語）
            current_data: 現在のデータ（ペルソナ、マトリクスなど）
            
        Returns:
            {
                'modified_data': Dict[str, Any],
                'change_summary': str
            }
            
        Raises:
            Exception: 修正処理失敗時
        """
        logger.info(f"修正依頼を受け付けました: {request[:50]}...")
        
        try:
            # プロンプト生成
            prompt = self._build_modification_prompt(request, current_data)
            
            # LLM呼び出し
            result = self.llm.generate_json(
                prompt=prompt,
                max_tokens=Config.MAX_TOKENS_MODIFICATION,
                temperature=Config.TEMP_MODIFICATION
            )
            
            # 修正タイプに応じて差分を適用
            modification_type = result.get('modification_type', 'general')
            modified_data = result.get('modified_data', {})
            change_summary = result.get('change_summary', '変更内容不明')
            
            # 元データに差分をマージ
            updated_data = self._apply_modifications(
                modification_type,
                modified_data,
                current_data
            )
            
            logger.info(f"修正完了: {change_summary}")
            
            # 履歴記録
            from utils.history_logger import HistoryLogger
            history_logger = HistoryLogger(Config.LOG_DIR)
            history_logger.log_modification(
                modification_type=modification_type,
                request=request
            )
            
            return {
                'modified_data': updated_data,
                'change_summary': change_summary
            }
            
        except Exception as e:
            logger.error(f"修正依頼の処理に失敗しました: {str(e)}")
            raise
    
    def _build_modification_prompt(
        self,
        request: str,
        current_data: Dict[str, Any]
    ) -> str:
        """
        修正依頼用のプロンプトを構築
        修正対象を自動判定して最適なプロンプトを生成
        
        Args:
            request: 修正依頼
            current_data: 現在のデータ
            
        Returns:
            プロンプト文字列
        """
        # 1. 修正対象を推定
        modification_target = self._detect_modification_target(request)
        
        # 2. 対象に応じて必要最小限のデータを抽出
        minimal_data = self._extract_minimal_data(modification_target, current_data)
        
        # 3. ペルソナ修正の場合の特別な指示
        persona_constraints = ""
        if modification_target['type'] == 'personas':
            persona_count = len(minimal_data.get('personas', []))
            persona_ids = [p['id'] for p in minimal_data.get('personas', [])]
            persona_constraints = f"""
【重要な制約】
- ペルソナの総数は必ず{persona_count}件のまま維持してください
- 既存のペルソナID({', '.join(persona_ids)})は絶対に変更しないでください
- 「企業を増やす」「在籍企業イメージを増やす」という依頼の場合は、既存ペルソナのcompanies配列に企業を追加してください
- 新規ペルソナ（P4, P5等）は絶対に作成しないでください
- 各ペルソナのcompanies配列は3-10社の範囲内で調整してください

【出力例（企業を増やす場合）】
{{
  "modification_type": "personas",
  "modified_data": {{
    "personas": [
      {{"id": "P1", "companies": ["企業A", "企業B", "企業C", "企業D", "企業E", "企業F"]}},
      {{"id": "P2", "companies": ["企業G", "企業H", "企業I", "企業J", "企業K"]}},
      {{"id": "P3", "companies": ["企業M", "企業N", "企業O", "企業P", "企業Q", "企業R"]}}
    ]
  }},
  "change_summary": "既存のP1～P3のcompanies配列を拡張しました"
}}
"""
        
        # 4. プロンプト生成
        prompt = f"""
以下の修正依頼に従って、データを修正してください。

【修正対象】{modification_target['type']}
【現在のデータ】
{json.dumps(minimal_data, ensure_ascii=False, indent=2)}

【修正依頼】
{request}
{persona_constraints}

【出力形式】
変更が必要な部分のみを含むJSON:
{{
  "modification_type": "{modification_target['type']}",
  "modified_data": {{
    // 修正対象のデータのみ（例: personas, axes, specific_cells等）
  }},
  "change_summary": "変更内容の説明"
}}

注意:
- 修正依頼で指定されていない部分は含めない
- データ構造は現在のフォーマットを維持
- {modification_target['constraints']}
"""
        
        return prompt
    
    def _detect_modification_target(self, request: str) -> Dict[str, str]:
        """
        修正依頼の内容から修正対象を推定
        
        Args:
            request: 修正依頼文
            
        Returns:
            {
                'type': 'personas' | 'axes' | 'matrix_cells' | 'discussion_points',
                'constraints': '制約事項の説明文'
            }
        """
        # ペルソナ関連のキーワード
        persona_keywords = ['企業', 'ペルソナ', '業界', '職種', 'companies', '候補']
        if any(kw in request for kw in persona_keywords):
            return {
                'type': 'personas',
                'constraints': 'companies配列は各ペルソナ3-10社の範囲内で維持、企業名のバリエーションを増やす場合は既存企業を置き換える、既存のペルソナIDは維持'
            }
        
        # 分析軸関連
        axes_keywords = ['分析軸', '軸', 'カテゴリ', 'フロー', '役割', '使用技術', '経験例']
        if any(kw in request for kw in axes_keywords):
            return {
                'type': 'axes',
                'constraints': 'カテゴリは["フロー", "役割", "使用技術", "経験例"]のいずれか、合計20-30軸に収める'
            }
        
        # マトリクス評価関連
        matrix_keywords = ['評価', 'マトリクス', '〇', '△', '▲', 'セル', '行', '列']
        if any(kw in request for kw in matrix_keywords):
            return {
                'type': 'matrix_cells',
                'constraints': '評価記号は〇/△/▲のいずれか、ペルソナIDと年齢、分析軸を明示'
            }
        
        # 論点関連
        discussion_keywords = ['論点', 'ディスカッション', '議論', '確認']
        if any(kw in request for kw in discussion_keywords):
            return {
                'type': 'discussion_points',
                'constraints': '3つの論点を維持、Markdown形式'
            }
        
        # デフォルト: 全体修正
        return {
            'type': 'general',
            'constraints': '既存の構造を維持しつつ、指定された箇所のみ変更'
        }
    
    def _extract_minimal_data(
        self,
        modification_target: Dict[str, str],
        current_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        修正対象に応じて必要最小限のデータを抽出
        
        Args:
            modification_target: 修正対象情報
            current_data: 現在の全データ
            
        Returns:
            最小限のデータ
        """
        target_type = modification_target['type']
        
        if target_type == 'personas':
            # ペルソナ修正: ペルソナリストのみ
            return {
                'personas': current_data.get('personas', [])
            }
        
        elif target_type == 'axes':
            # 分析軸修正: 分析軸リストとペルソナ概要
            return {
                'axes': current_data.get('axes', []),
                'personas_summary': [
                    {'id': p['id'], 'industry': p['industry']} 
                    for p in current_data.get('personas', [])
                ]
            }
        
        elif target_type == 'matrix_cells':
            # マトリクス評価修正: ヘッダーと概要のみ
            matrix = current_data.get('matrix', [])
            if not matrix:
                return {'matrix': []}
            
            return {
                'matrix_header': matrix[0] if matrix else [],
                'personas': [p['id'] for p in current_data.get('personas', [])],
                'age_ranges': ['25-29', '30-39', '40-49'],
                'axes_count': len(current_data.get('axes', [])),
                'note': 'マトリクス全体は含まれていません。変更対象のセルを指定してください。'
            }
        
        elif target_type == 'discussion_points':
            # 論点修正: 論点のみ
            return {
                'discussion_points': current_data.get('discussion_points', '')
            }
        
        else:  # general
            # 全体修正: サマリーのみ
            return {
                'personas_count': len(current_data.get('personas', [])),
                'axes_count': len(current_data.get('axes', [])),
                'matrix_size': f"{len(current_data.get('matrix', []))}行",
                'has_discussion_points': bool(current_data.get('discussion_points')),
                'warning': '具体的な修正対象を指定してください'
            }
    
    def _apply_modifications(
        self,
        modification_type: str,
        modified_data: Dict[str, Any],
        current_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        修正内容を元データにマージ
        
        Args:
            modification_type: 修正タイプ
            modified_data: 修正されたデータ
            current_data: 元データ
            
        Returns:
            マージ後のデータ
        """
        result = copy.deepcopy(current_data)
        
        if modification_type == 'personas':
            # ペルソナの差分適用
            modified_personas = modified_data.get('personas', [])
            logger.info(f"🔍 [DEBUG] 修正対象ペルソナ数: {len(modified_personas)}")
            
            for mod_p in modified_personas:
                logger.info(f"🔍 [DEBUG] 修正内容: ID={mod_p.get('id')}, キー={list(mod_p.keys())}")
                if 'companies' in mod_p:
                    logger.info(f"🔍 [DEBUG] companies数: {len(mod_p.get('companies', []))}")
                    logger.info(f"🔍 [DEBUG] companies内容: {mod_p.get('companies', [])}")
                
                for i, orig_p in enumerate(result['personas']):
                    if orig_p['id'] == mod_p['id']:
                        before_companies = len(orig_p.get('companies', []))
                        result['personas'][i].update(mod_p)
                        after_companies = len(result['personas'][i].get('companies', []))
                        logger.info(f"✅ [DEBUG] {mod_p['id']}: companies {before_companies}社 → {after_companies}社")
                        logger.info(f"✅ [DEBUG] 更新後のcompanies: {result['personas'][i].get('companies', [])}")
                        break
        
        elif modification_type == 'axes':
            # 分析軸の置き換え（全体更新）
            if 'axes' in modified_data:
                result['axes'] = modified_data['axes']
        
        elif modification_type == 'matrix_cells':
            # 特定セルの評価変更
            cell_updates = modified_data.get('cell_updates', [])
            matrix = result.get('matrix', [])
            
            for update in cell_updates:
                row_idx = update.get('row_index')
                col_idx = update.get('col_index')
                new_value = update.get('value')
                
                if row_idx and col_idx and row_idx < len(matrix):
                    matrix[row_idx][col_idx] = new_value
        
        elif modification_type == 'discussion_points':
            # 論点の置き換え
            if 'discussion_points' in modified_data:
                result['discussion_points'] = modified_data['discussion_points']
        
        return result
