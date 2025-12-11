# 採用ターゲット分析マトリクス生成システム

採用担当者が求人票を入力すると、採用ターゲットの解像度を上げるための「ターゲット分析マトリクス」と「すり合わせミーティング用の論点ガイド」を自動生成するシステム。

## 概要

このシステムは、求人票から以下を自動生成します：

1. **ターゲットペルソナ（3パターン）**: 業界・職種・在籍企業イメージ
2. **分析軸（4カテゴリ）**: フロー・役割・使用技術・経験例
3. **評価マトリクス（9行）**: 3ペルソナ × 3年齢層の評価表
4. **論点ガイド**: すり合わせミーティング用の議論ポイント

## 主要機能

- ✅ 多様な求人票入力（テキスト入力 + ファイルアップロード）
- ✅ 元プロンプトに基づく6ステップ処理
- ✅ セルフレビューによる品質向上
- ✅ 段階的なペルソナ追加機能
- ✅ 修正依頼機能（対話型確認フロー）
- ✅ Q&A機能（対話的な調整）
- ✅ TSV形式でのエクスポート

## 技術スタック

- **フロントエンド**: Streamlit
- **バックエンド**: Python
- **LLM**: OpenAI GPT-4o-mini（将来的にGPT-5-miniに対応予定）
- **データ処理**: Pandas

## セットアップ

### 1. 環境準備

```bash
cd /Users/yutokumura/Desktop/Python/Target_customer_image
python -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate
```

### 2. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 3. 環境変数の設定

`config.env.example` をコピーして `config.env` を作成し、OpenAI API Keyを設定：

```bash
cp config.env.example config.env
```

`config.env` を編集：

```
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. アプリケーションの起動

```bash
streamlit run app.py
```

ブラウザで `http://localhost:8501` にアクセスしてください。

## 使い方

### 基本的な流れ

1. **求人票入力**: テキストエリアに求人票を貼り付けるか、ファイルをアップロード
2. **マトリクス生成**: 「マトリクス生成（3パターン）」ボタンをクリック
3. **結果確認**: 生成されたマトリクスと論点ガイドを確認
4. **TSV出力**: 「OK - TSV出力」ボタンでエクスポート

### 追加機能

#### ペルソナ追加
- 「ペルソナ追加」タブから追加数を指定して生成
- 既存のペルソナとは異なるターゲット層が生成されます

#### 修正依頼
- 「修正依頼」タブから自然言語で修正内容を指示
- 例: "P1の業界を「半導体製造装置業界」に変更してください"

#### Q&A
- 「Q&A」タブからマトリクスやペルソナについて質問
- 例: "P1とP2の違いは何ですか？"

## プロジェクト構造

```
Target_customer_image/
├── app.py                          # Streamlitメインアプリ
├── config.py                       # 設定ファイル
├── requirements.txt                # 依存パッケージ
├── README.md                       # このファイル
│
├── core/                           # コアロジック
│   ├── step1_job_analysis.py      # STEP1: 求人票分析
│   ├── step2_persona_generation.py # STEP2: ペルソナ推論
│   ├── step3_axes_generation.py   # STEP3: 分析軸推論
│   ├── step4_matrix_evaluation.py # STEP4: マトリクス評価
│   ├── step4_5_self_review.py     # STEP4.5: セルフレビュー
│   ├── step5_discussion.py        # STEP5: 論点抽出
│   └── step6_confirmation.py      # STEP6: 確認メッセージ
│
├── services/                       # サービス層
│   ├── persona_service.py         # ペルソナ追加生成
│   ├── modification_service.py    # 修正依頼処理
│   └── qa_service.py              # Q&A機能
│
├── utils/                          # ユーティリティ
│   ├── llm_client.py              # LLM呼び出しラッパー
│   ├── validators.py              # バリデーション関数
│   ├── formatters.py              # フォーマット変換
│   └── logger.py                  # ログ設定
│
├── prompts/                        # プロンプトテンプレート
│   ├── step1_job_analysis.txt     # STEP1プロンプト
│   ├── step2_persona.txt          # STEP2プロンプト
│   ├── step3_axes.txt             # STEP3プロンプト
│   ├── step4_matrix.txt           # STEP4プロンプト
│   ├── step4_5_review.txt         # STEP4.5プロンプト
│   ├── step5_discussion.txt       # STEP5プロンプト
│   └── step6_confirmation.txt     # STEP6プロンプト
│
└── logs/                           # ログファイル
    ├── system.log                  # システムログ
    └── token_usage.log             # トークン使用量ログ
```

## 設定

### config.py

主要な設定項目：

- `OPENAI_MODEL`: 使用するLLMモデル（デフォルト: `gpt-4o-mini`）
- `MAX_TOKENS_STEP*`: 各ステップの最大トークン数
- `TEMP_STEP*`: 各ステップのtemperature値
- `DEFAULT_NUM_PERSONAS`: 初回生成ペルソナ数（固定: 3）
- `DEFAULT_AGE_RANGES`: 年齢レンジ（固定: 25-29, 30-39, 40-49）

### ログ設定

ログは `logs/` ディレクトリに出力されます：

- `system.log`: システムログ（INFO, WARNING, ERROR）
- `token_usage.log`: トークン使用量ログ（コスト計算用）

## 処理フロー

### 初回生成（STEP1-6）

```
STEP1: 求人票分析
  ↓
STEP2: ペルソナ推論（3パターン）
  ↓
STEP3: 分析軸推論（4カテゴリ）
  ↓
STEP4: マトリクス評価（9行）
  ↓
STEP4.5: セルフレビュー
  ↓
STEP5: 論点抽出
  ↓
STEP6: 確認メッセージ
```

## コスト見積もり

### GPT-4o-mini使用時

- **初回生成（3ペルソナ、9行マトリクス）**: 約$0.01-0.02（約1.5-3円）
- **追加生成（2ペルソナ追加）**: 約$0.01（約1.5円）
- **Q&A（1回）**: 約$0.002-0.005（約0.3-0.8円）

※実際のコストは求人票の長さや生成内容により変動します

## トラブルシューティング

### エラー: "応答が空です"

- OpenAI API Keyが正しく設定されているか確認
- `config.env` ファイルが存在するか確認
- トークン制限（`MAX_TOKENS_STEP*`）を増やしてみる

### エラー: "JSON解析に失敗しました"

- LLMの応答が不安定な場合があります
- `temperature` 値を下げる（`config.py`）
- 再試行してください

### マトリクスが生成されない

- 求人票の内容が十分か確認（最低200文字程度推奨）
- ログファイル（`logs/system.log`）を確認

## ライセンス

このプロジェクトは内部利用のみを想定しています。

## 更新履歴

### v1.0.0 (2025-12-06)
- 初回リリース
- 6ステップ処理の実装
- ペルソナ追加、修正依頼、Q&A機能の実装
- TSV出力機能の実装
