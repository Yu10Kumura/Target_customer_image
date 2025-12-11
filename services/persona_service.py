"""
ペルソナサービス
ペルソナの追加生成を管理
"""
from typing import Dict, Any, List
from config import Config
from utils.logger import logger
from core.step2_persona_generation import Step2PersonaGenerator
from core.step3_axes_generation import Step3AxesGenerator
from core.step4_matrix_evaluation import Step4MatrixEvaluator
from core.step4_5_self_review import Step4_5SelfReviewer
from core.step5_discussion import Step5DiscussionExtractor


class PersonaService:
    """ペルソナサービスクラス"""
    
    def __init__(
        self,
        step2_generator: Step2PersonaGenerator,
        step3_generator: Step3AxesGenerator,
        step4_evaluator: Step4MatrixEvaluator,
        step4_5_reviewer: Step4_5SelfReviewer,
        step5_extractor: Step5DiscussionExtractor
    ):
        """
        初期化
        
        Args:
            step2_generator: STEP2ペルソナ生成器
            step3_generator: STEP3分析軸生成器
            step4_evaluator: STEP4マトリクス評価器
            step4_5_reviewer: STEP4.5レビュー器
            step5_extractor: STEP5論点抽出器
        """
        self.step2 = step2_generator
        self.step3 = step3_generator
        self.step4 = step4_evaluator
        self.step4_5 = step4_5_reviewer
        self.step5 = step5_extractor
    
    def add_personas(
        self,
        current_state: Dict[str, Any],
        additional_count: int
    ) -> Dict[str, Any]:
        """
        ペルソナを追加生成し、マトリクス・論点を再生成
        
        Args:
            current_state: 現在の状態（ペルソナ、分析軸、マトリクスなど）
            additional_count: 追加するペルソナ数
            
        Returns:
            更新後の状態
            {
                'personas': List[Dict],
                'axes': List[Dict],
                'matrix': List[List[str]],
                'discussion_points': str
            }
            
        Raises:
            Exception: 追加生成失敗時
        """
        logger.info(f"ペルソナを{additional_count}件追加します")
        
        try:
            # STEP2: 追加ペルソナ生成
            new_personas = self.step2.generate_additional_personas(
                job_description=current_state['job_description'],
                analysis=current_state['analysis'],
                existing_personas=current_state['personas'],
                additional_count=additional_count
            )
            
            # 全ペルソナリスト
            all_personas = current_state['personas'] + new_personas
            
            # STEP3: 分析軸の更新
            updated_axes = self.step3.update_axes(
                existing_axes=current_state['axes'],
                new_personas=new_personas,
                job_description=current_state['job_description']
            )
            
            # STEP4: マトリクス再生成
            matrix = self.step4.evaluate_matrix(
                personas=all_personas,
                axes=updated_axes,
                analysis=current_state['analysis'],
                job_description=current_state['job_description']
            )
            
            # STEP4.5: セルフレビュー
            review_result = self.step4_5.review(
                matrix=matrix,
                job_description=current_state['job_description'],
                personas=all_personas,
                axes=updated_axes
            )
            
            if review_result.get('has_issues', False):
                matrix = self.step4_5.apply_fixes(matrix, review_result)
            
            # STEP5: 論点抽出
            discussion_points = self.step5.extract_discussion_points(
                matrix=matrix,
                job_description=current_state['job_description'],
                personas=all_personas,
                axes=updated_axes
            )
            
            logger.info(f"ペルソナ追加が完了しました（合計: {len(all_personas)}件）")
            
            return {
                'personas': all_personas,
                'axes': updated_axes,
                'matrix': matrix,
                'discussion_points': discussion_points
            }
            
        except Exception as e:
            logger.error(f"ペルソナ追加に失敗しました: {str(e)}")
            raise
