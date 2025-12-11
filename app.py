"""
採用ターゲット分析マトリクス生成システム
Streamlitメインアプリケーション
"""
import streamlit as st
import time
from datetime import datetime
from pathlib import Path
from config import Config
from utils.llm_client import LLMClient
from utils.formatters import matrix_to_tsv, matrix_to_html, personas_to_markdown, axes_to_markdown, matrix_to_excel_bytes
from utils.logger import logger
from core.step1_job_analysis import Step1JobAnalyzer
from core.step2_persona_generation import Step2PersonaGenerator
from core.step3_axes_generation import Step3AxesGenerator
from core.step4_matrix_evaluation import Step4MatrixEvaluator
from core.step4_5_self_review import Step4_5SelfReviewer
from core.step5_discussion import Step5DiscussionExtractor
from core.step6_confirmation import Step6ConfirmationGenerator
from services.persona_service import PersonaService
from services.modification_service import ModificationService
from services.qa_service import QAService


# ページ設定
st.set_page_config(
    page_title="採用ターゲット分析マトリクス生成",
    page_icon="🎯",
    layout="wide"
)


def initialize_session_state():
    """セッションステートの初期化"""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = True
        st.session_state.job_description = ""
        st.session_state.step1_result = None
        st.session_state.personas = None
        st.session_state.axes = None
        st.session_state.matrix = None
        st.session_state.discussion_points = None
        st.session_state.qa_history = []
        st.session_state.modification_history = []
        st.session_state.processing = False
        st.session_state.matrix_updated_at = None


def initialize_components():
    """コンポーネントの初期化"""
    # LLMクライアント
    llm = LLMClient()
    
    # コアコンポーネント
    step1 = Step1JobAnalyzer(llm)
    step2 = Step2PersonaGenerator(llm)
    step3 = Step3AxesGenerator(llm)
    step4 = Step4MatrixEvaluator(llm)
    step4_5 = Step4_5SelfReviewer(llm)
    step5 = Step5DiscussionExtractor(llm)
    step6 = Step6ConfirmationGenerator()
    
    # サービス
    persona_service = PersonaService(step2, step3, step4, step4_5, step5)
    modification_service = ModificationService(llm)
    qa_service = QAService(llm)
    
    return {
        'llm': llm,
        'step1': step1,
        'step2': step2,
        'step3': step3,
        'step4': step4,
        'step4_5': step4_5,
        'step5': step5,
        'step6': step6,
        'persona_service': persona_service,
        'modification_service': modification_service,
        'qa_service': qa_service
    }


def render_header():
    """ヘッダー表示"""
    st.title("🎯 採用ターゲット分析マトリクス生成システム")
    st.markdown("---")


def render_input_section(components):
    """入力セクションの表示"""
    st.header("📝 求人票入力")
    
    # タブ
    input_tab1, input_tab2 = st.tabs(["📄 テキスト入力", "📎 ファイルアップロード"])
    
    with input_tab1:
        job_text = st.text_area(
            "求人票を入力してください",
            height=300,
            placeholder="求人票の内容を貼り付けてください..."
        )
        if job_text:
            st.session_state.job_description = job_text
    
    with input_tab2:
        uploaded_file = st.file_uploader(
            "求人票ファイルをアップロード",
            type=["txt", "pdf", "docx", "csv", "tsv"]
        )
        if uploaded_file:
            # ファイル読み込み（簡易実装）
            try:
                content = uploaded_file.read().decode('utf-8')
                st.session_state.job_description = content
                st.success(f"✅ ファイルを読み込みました: {uploaded_file.name}")
            except Exception as e:
                st.error(f"❌ ファイル読み込みエラー: {str(e)}")
    
    # 生成ボタン
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🚀 マトリクス生成（3パターン）", type="primary", use_container_width=True):
            if not st.session_state.job_description:
                st.error("❌ 求人票を入力してください")
            else:
                generate_initial_matrix(components)


def generate_initial_matrix(components):
    """初回マトリクス生成（STEP1-6）"""
    st.session_state.processing = True
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # STEP1: 求人票分析
        status_text.text("⏳ STEP1: 求人票を分析中...")
        step1_result = components['step1'].analyze(st.session_state.job_description)
        st.session_state.step1_result = step1_result
        progress_bar.progress(15)
        
        # STEP2: ペルソナ生成
        status_text.text("⏳ STEP2: ターゲットペルソナを推論中...")
        personas = components['step2'].generate_personas(
            st.session_state.job_description,
            step1_result,
            num_personas=3
        )
        st.session_state.personas = personas
        progress_bar.progress(30)
        
        # STEP3: 分析軸生成
        status_text.text("⏳ STEP3: 分析軸を生成中...")
        axes = components['step3'].generate_axes(
            st.session_state.job_description,
            step1_result,
            personas
        )
        st.session_state.axes = axes
        progress_bar.progress(50)
        
        # STEP4: マトリクス評価
        status_text.text("⏳ STEP4: マトリクスを評価中...")
        matrix = components['step4'].evaluate_matrix(
            personas,
            axes,
            step1_result,
            st.session_state.job_description
        )
        st.session_state.matrix = matrix
        progress_bar.progress(70)
        
        # STEP4.5: セルフレビュー
        status_text.text("⏳ STEP4.5: 品質チェック中...")
        review_result = components['step4_5'].review(
            matrix,
            st.session_state.job_description,
            personas,
            axes
        )
        if review_result.get('has_issues', False):
            matrix = components['step4_5'].apply_fixes(matrix, review_result)
            st.session_state.matrix = matrix
        progress_bar.progress(85)
        
        # STEP5: 論点抽出
        status_text.text("⏳ STEP5: すり合わせ論点を抽出中...")
        discussion_points = components['step5'].extract_discussion_points(
            matrix,
            st.session_state.job_description,
            personas,
            axes
        )
        st.session_state.discussion_points = discussion_points
        progress_bar.progress(100)
        
        status_text.text("✅ 生成完了！")
        time.sleep(0.5)
        progress_bar.empty()
        status_text.empty()
        st.session_state.matrix_updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        st.success("🎉 マトリクス生成が完了しました！")
        st.rerun()
        
    except Exception as e:
        st.error(f"❌ エラーが発生しました: {str(e)}")
        logger.error(f"マトリクス生成エラー: {str(e)}")
    finally:
        st.session_state.processing = False


def render_result_section(components):
    """結果表示セクション"""
    if st.session_state.matrix is None:
        st.info("👆 まず求人票を入力して、マトリクスを生成してください")
        return
    
    st.header("📊 ターゲット分析マトリクス")
    
    # マトリクス表示
    st.markdown("### マトリクス")
    if st.session_state.matrix_updated_at:
        st.caption(f"最終更新: {st.session_state.matrix_updated_at}")
    matrix_html = matrix_to_html(st.session_state.matrix)
    st.markdown(matrix_html, unsafe_allow_html=True)

    st.markdown("### 最新ペルソナ概要")
    personas_md = personas_to_markdown(st.session_state.personas)
    # UIに渡すMarkdownの先頭部分をログに出力（内部検証用）
    logger.info(f"[UI DEBUG] personas_to_markdown 先頭100文字: {personas_md[:100]}")
    st.markdown(personas_md)
    
    # 論点ガイド
    st.markdown("---")
    st.markdown("### すり合わせ論点ガイド")
    st.markdown(st.session_state.discussion_points)
    
    # 確認メッセージ（STEP6）
    st.markdown("---")
    st.info("""
    💬 **上記内容でよろしければ、エクセルorスプレッドシートで出力可能な形式（TSV）でお渡しします。**
    
    出力してよければ下の「OK - TSV出力」ボタンをクリックしてください。
    修正依頼や質問があれば、以下のタブから指示してください。
    """)
    
    # TSV出力ボタン
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("✅ OK - TSV出力", type="primary", use_container_width=True):
            tsv_content = matrix_to_tsv(st.session_state.matrix)
            st.download_button(
                label="📥 TSVファイルをダウンロード",
                data=tsv_content,
                file_name="target_matrix.tsv",
                mime="text/tab-separated-values",
                use_container_width=True
            )
            excel_bytes = matrix_to_excel_bytes(st.session_state.matrix)
            st.download_button(
                label="📥 Excelファイルをダウンロード",
                data=excel_bytes,
                file_name="target_matrix.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
    
    # 追加操作タブ
    st.markdown("---")
    st.markdown("**または、以下で調整・修正できます:**")
    
    tab1, tab2, tab3 = st.tabs(["➕ ペルソナ追加", "✏️ 修正依頼", "💬 Q&A"])
    
    with tab1:
        render_persona_addition_tab(components)
    
    with tab2:
        render_modification_tab(components)
    
    with tab3:
        render_qa_tab(components)


def render_persona_addition_tab(components):
    """ペルソナ追加タブ"""
    st.markdown("#### 追加ペルソナ生成")
    st.markdown("現在のペルソナとは異なる、新しいターゲット層を追加生成します。")
    
    additional_count = st.number_input(
        "追加するペルソナ数",
        min_value=1,
        max_value=5,
        value=2,
        step=1
    )
    
    if st.button("➕ ペルソナを追加生成", use_container_width=True):
        try:
            with st.spinner("追加生成中..."):
                current_state = {
                    'job_description': st.session_state.job_description,
                    'analysis': st.session_state.step1_result,
                    'personas': st.session_state.personas,
                    'axes': st.session_state.axes
                }
                
                updated = components['persona_service'].add_personas(
                    current_state,
                    additional_count
                )
                
                st.session_state.personas = updated['personas']
                st.session_state.axes = updated['axes']
                st.session_state.matrix = updated['matrix']
                st.session_state.discussion_points = updated['discussion_points']
                
                st.success(f"✅ {additional_count}件のペルソナを追加しました！")

        except Exception as e:
            st.error(f"❌ エラー: {str(e)}")


def render_modification_tab(components):
    """修正依頼タブ"""
    st.markdown("#### 修正依頼")
    st.markdown("自然言語で修正内容を指示してください。")
    
    # 修正履歴表示
    if st.session_state.modification_history:
        st.markdown("##### 修正履歴")
        for i, history in enumerate(st.session_state.modification_history, start=1):
            with st.expander(f"修正{i}: {history['request'][:50]}..."):
                st.markdown(f"**依頼:** {history['request']}")
                st.markdown(f"**変更内容:** {history['summary']}")
    
    modification_request = st.text_area(
        "修正内容を入力",
        placeholder="例: P1の業界を「半導体製造装置業界」に変更してください",
        height=100
    )
    
    if st.button("✏️ 修正を実行", use_container_width=True):
        if not modification_request:
            st.warning("修正内容を入力してください")
        else:
            try:
                with st.spinner("修正中..."):
                    current_data = {
                        'personas': st.session_state.personas,
                        'axes': st.session_state.axes,
                        'matrix': st.session_state.matrix
                    }
                    
                    result = components['modification_service'].process_modification_request(
                        modification_request,
                        current_data
                    )
                    
                                        # ========== ここから追加 ==========
                    # 🔍 デバッグログ: 修正結果の内容を確認
                    logger.info(f"🔍 [APP DEBUG] result['modified_data']のキー: {list(result['modified_data'].keys())}")
                    logger.info(f"🔍 [APP DEBUG] personas存在: {'personas' in result['modified_data']}")
                    if 'personas' in result['modified_data']:
                        logger.info(f"🔍 [APP DEBUG] personas数: {len(result['modified_data']['personas'])}")
                        if result['modified_data']['personas']:
                            logger.info(f"🔍 [APP DEBUG] P1 companies数: {len(result['modified_data']['personas'][0].get('companies', []))}")
                            logger.info(f"🔍 [APP DEBUG] P1 companies[0]: {result['modified_data']['personas'][0].get('companies', [])[0] if result['modified_data']['personas'][0].get('companies') else 'なし'}")
                    # ========== ここまで追加 ==========


                    # 修正結果をsession_stateに反映
                    st.session_state.personas = result['modified_data'].get('personas', st.session_state.personas)
                    st.session_state.axes = result['modified_data'].get('axes', st.session_state.axes)
                    st.session_state.matrix = result['modified_data'].get('matrix', st.session_state.matrix)
                    st.session_state.discussion_points = result['modified_data'].get('discussion_points', st.session_state.discussion_points)

                    # 修正内容を表へ反映（再計算）
                    recalc_status = st.empty()
                    try:
                        recalc_status.info("STEP4: マトリクスを再評価しています…")
                        st.session_state.matrix = components['step4'].evaluate_matrix(
                            st.session_state.personas,
                            st.session_state.axes,
                            st.session_state.step1_result,
                            st.session_state.job_description
                        )
                        recalc_status.info("STEP4.5: 品質チェックを実行中…")
                        review_result = components['step4_5'].review(
                            st.session_state.matrix,
                            st.session_state.job_description,
                            st.session_state.personas,
                            st.session_state.axes
                        )
                        if review_result.get('has_issues', False):
                            st.session_state.matrix = components['step4_5'].apply_fixes(st.session_state.matrix, review_result)
                        recalc_status.info("STEP5: すり合わせ論点を更新中…")
                        st.session_state.discussion_points = components['step5'].extract_discussion_points(
                            st.session_state.matrix,
                            st.session_state.job_description,
                            st.session_state.personas,
                            st.session_state.axes
                        )
                        st.session_state.matrix_updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        recalc_status.success("再計算が完了しました")
                    except Exception as e:
                        recalc_status.error("表の再計算に失敗しました。時間をおいて再実行してください。")
                        st.warning(f"⚠️ 表の再計算に失敗しました: {str(e)}")
                    
                    # 修正履歴に追加
                    st.session_state.modification_history.append({
                        'request': modification_request,
                        'summary': result['change_summary']
                    })
                    
                    st.success(f"✅ 修正完了: {result['change_summary']}")
                    st.rerun()

            except Exception as e:
                st.error(f"❌ エラー: {str(e)}")


def render_qa_tab(components):
    """Q&Aタブ"""
    st.markdown("#### Q&A")
    st.markdown("マトリクスやペルソナについて質問できます。")
    
    # 会話履歴表示
    if st.session_state.qa_history:
        st.markdown("##### 会話履歴")
        for i, turn in enumerate(st.session_state.qa_history, start=1):
            with st.expander(f"Q{i}: {turn['q'][:50]}..."):
                st.markdown(f"**Q:** {turn['q']}")
                st.markdown(f"**A:** {turn['a']}")
    
    # 質問入力
    question = st.text_area(
        "質問を入力",
        placeholder="例: P1とP2の違いは何ですか？",
        height=100
    )
    
    if st.button("💬 質問する", use_container_width=True):
        if not question:
            st.warning("質問を入力してください")
        else:
            try:
                with st.spinner("回答生成中..."):
                    context = {
                        'personas': st.session_state.personas,
                        'axes': st.session_state.axes,
                        'matrix': st.session_state.matrix,
                        'discussion_points': st.session_state.discussion_points
                    }
                    
                    result = components['qa_service'].answer_question(
                        question,
                        context,
                        st.session_state.qa_history
                    )
                    
                    st.session_state.qa_history = result['updated_history']
                    
                    st.markdown("##### 回答")
                    st.markdown(result['answer'])

            except Exception as e:
                st.error(f"❌ エラー: {str(e)}")


def main():
    """メイン関数"""
    initialize_session_state()
    components = initialize_components()
    
    render_header()
    
    # 入力セクション（結果がない場合のみ表示）
    if st.session_state.matrix is None:
        render_input_section(components)
    else:
        # 結果表示セクション
        render_result_section(components)
        
        # サイドバーに入力セクション
        with st.sidebar:
            st.header("📝 新規生成")
            if st.button("🔄 最初から生成し直す"):
                for key in list(st.session_state.keys()):
                    if key != 'initialized':
                        del st.session_state[key]
                st.rerun()


if __name__ == "__main__":
    main()
