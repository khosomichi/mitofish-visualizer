# 🐟 MitoFish Visualizer

環境DNA魚類検出結果（MitoFish出力）を可視化するためのStreamlitアプリケーションです。

## 機能

- **積み上げ棒グラフ**: サンプルごとの魚種構成（相対存在量/リード数）
- **ヒートマップ**: サンプル×魚種のマトリックス表示
- **多様性指標**: 種数、Shannon指数、Simpson指数の計算・表示
- **データエクスポート**: 処理済みデータのCSVダウンロード

## スクリーンショット

アップロード後、以下のような可視化が可能です：

- 各サンプルの魚種構成を積み上げ棒グラフで表示
- 上位N種を選択し、残りを「その他」にまとめる機能
- 複数のカラースキームから選択可能

## ローカルでの実行

### 必要要件

- Python 3.9以上
- pip

### インストール

```bash
# リポジトリをクローン（またはファイルをダウンロード）
git clone https://github.com/yourusername/mitofish-visualizer.git
cd mitofish-visualizer

# 仮想環境を作成（推奨）
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存パッケージをインストール
pip install -r requirements.txt
```

### 実行

```bash
streamlit run app.py
```

ブラウザで `http://localhost:8501` が自動的に開きます。

## Streamlit Cloudへのデプロイ

### 手順

1. **GitHubリポジトリを作成**
   - `app.py` と `requirements.txt` をリポジトリにプッシュ

2. **Streamlit Cloudにアクセス**
   - https://share.streamlit.io/ にアクセス
   - GitHubアカウントでサインイン

3. **新しいアプリをデプロイ**
   - 「New app」をクリック
   - リポジトリ、ブランチ、メインファイル（`app.py`）を選択
   - 「Deploy」をクリック

4. **完了**
   - 数分でアプリが公開されます
   - URLを共有して他のユーザーも使用可能に

### Streamlit Cloud設定例

```
Repository: yourusername/mitofish-visualizer
Branch: main
Main file path: app.py
```

## 対応ファイル形式

### MitoFish標準出力

```
TaxonIDs,Species,Class,Order,Family,...,sample1.fastq,sample2.fastq,...
```

- カンマ区切り（CSV）
- タブ区切り（TSV）
- UTF-8, UTF-8-BOM, Shift-JIS エンコーディング対応

### 列の自動検出

- **魚種列**: `Species`, `species`, `種名` などの列名を自動検出
- **サンプル列**: `.fastq` を含む列名、または数値列を自動検出

## カスタマイズ

### カラースキームの追加

`app.py` の `color_sequences` 辞書に新しいカラースキームを追加できます：

```python
color_sequences = {
    'MyCustom': ['#ff0000', '#00ff00', '#0000ff', ...],
    ...
}
```

### 多様性指標の追加

`create_diversity_chart` 関数内で新しい指標を計算・追加できます。

## ライセンス

MIT License

## 作者

Tokyo University of Pharmacy and Life Sciences  
Laboratory of Computational Genomics

## 参考

- [MitoFish](https://mitofish.aori.u-tokyo.ac.jp/) - 魚類ミトコンドリアゲノムデータベース（東京大学大気海洋研究所）
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Plotly Python](https://plotly.com/python/)
