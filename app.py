"""
MitoFish Visualizer - 環境DNA魚類検出結果の可視化ツール
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from io import BytesIO

# ページ設定
st.set_page_config(
    page_title="MitoFish Visualizer",
    page_icon="🐟",
    layout="wide"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ヘッダー
st.markdown('<p class="main-header">🐟 MitoFish Visualizer</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">環境DNA魚類検出結果の可視化ツール</p>', unsafe_allow_html=True)

def parse_mitfish_csv(df):
    """MitoFish CSVファイルを解析してデータを抽出"""
    # サンプル列を特定（.fastqを含む列名）
    sample_cols = [col for col in df.columns if '.fastq' in col.lower()]
    
    if not sample_cols:
        # .fastqがない場合、数値列を探す
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        # 既知のメタデータ列を除外
        exclude_patterns = ['Identity', 'Max', 'Positive', 'TaxonID']
        sample_cols = [col for col in numeric_cols 
                      if not any(pat.lower() in col.lower() for pat in exclude_patterns)]
    
    if not sample_cols:
        st.error("サンプル列が見つかりませんでした。")
        return None, None, None
    
    # 魚種情報を取得
    species_col = None
    for col in ['Species', 'species', 'SPECIES', '種名']:
        if col in df.columns:
            species_col = col
            break
    
    if species_col is None:
        species_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
    
    # データを抽出
    species_names = df[species_col].fillna('Unknown').astype(str).tolist()
    abundance_data = df[sample_cols].fillna(0).astype(float)
    
    # サンプル名をクリーンアップ
    clean_sample_names = []
    for col in sample_cols:
        # ファイル名からサンプル名を抽出
        name = col.replace('.fastq', '').replace('.FASTQ', '')
        # 数字-数字-名前-数字 のパターンを処理 (例: 1-1-tamagawa-6000)
        parts = name.split('-')
        if len(parts) >= 3:
            # サイト名と番号を組み合わせて一意にする (例: tamagawa-1)
            site_name = '-'.join(parts[2:-1]) if len(parts) > 3 else parts[2]
            sample_num = parts[0] if parts[0].isdigit() else ''
            name = f"{site_name}-{sample_num}" if sample_num else site_name
        
        # 重複チェック - 既に同じ名前があれば番号を付ける
        base_name = name
        counter = 1
        while name in clean_sample_names:
            counter += 1
            name = f"{base_name}_{counter}"
        
        clean_sample_names.append(name)
    
    return species_names, abundance_data, clean_sample_names


def create_stacked_bar_chart(species, abundance_df, sample_names, show_percentage=True, 
                              top_n=None, color_scheme='Plotly'):
    """積み上げ棒グラフを作成"""
    
    df = abundance_df.copy()
    df.columns = sample_names
    
    # 各種の合計を計算してソート
    species_totals = df.sum(axis=1)
    sorted_indices = species_totals.argsort()[::-1]
    
    # 上位N種に絞る
    if top_n and top_n < len(species):
        top_indices = sorted_indices[:top_n]
        other_sum = df.iloc[sorted_indices[top_n:]].sum()
        
        df_top = df.iloc[top_indices].copy()
        species_top = [species[i] for i in top_indices]
        
        # その他を追加
        df_top.loc['Other'] = other_sum
        species_top.append('その他 (Other)')
        
        df = df_top
        species = species_top
    else:
        df = df.iloc[sorted_indices]
        species = [species[i] for i in sorted_indices]
    
    # パーセンテージ計算
    if show_percentage:
        col_sums = df.sum()
        df_plot = df.div(col_sums) * 100
        df_plot = df_plot.fillna(0)
        y_label = "相対存在量 (%)"
    else:
        df_plot = df
        y_label = "リード数"
    
    # プロット用にデータを転置・整形
    df_plot_t = df_plot.T
    df_plot_t.index.name = 'Sample'
    df_plot_t = df_plot_t.reset_index()
    
    # 長形式に変換
    df_long = df_plot_t.melt(id_vars=['Sample'], var_name='Species', value_name='Abundance')
    
    # カラースキームの選択
    color_sequences = {
        'Plotly': px.colors.qualitative.Plotly,
        'D3': px.colors.qualitative.D3,
        'Set1': px.colors.qualitative.Set1,
        'Set2': px.colors.qualitative.Set2,
        'Set3': px.colors.qualitative.Set3,
        'Pastel': px.colors.qualitative.Pastel,
        'Bold': px.colors.qualitative.Bold,
        'Vivid': px.colors.qualitative.Vivid,
    }
    
    fig = px.bar(
        df_long,
        x='Sample',
        y='Abundance',
        color='Species',
        color_discrete_sequence=color_sequences.get(color_scheme, px.colors.qualitative.Plotly),
        labels={'Abundance': y_label, 'Sample': 'サンプル', 'Species': '魚種'},
    )
    
    fig.update_layout(
        barmode='stack',
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.5,
            xanchor="center",
            x=0.5,
            font=dict(size=10)
        ),
        xaxis_tickangle=-45,
        height=600,
        margin=dict(b=150)
    )
    
    return fig


def create_heatmap(species, abundance_df, sample_names, log_scale=False):
    """ヒートマップを作成"""
    
    df = abundance_df.copy()
    df.columns = sample_names
    
    # 各種の合計でソート
    species_totals = df.sum(axis=1)
    sorted_indices = species_totals.argsort()[::-1]
    df = df.iloc[sorted_indices]
    sorted_species = [species[i] for i in sorted_indices]
    
    # 対数スケール
    if log_scale:
        df = np.log10(df + 1)
        colorbar_title = "Log10(リード数+1)"
    else:
        colorbar_title = "リード数"
    
    fig = go.Figure(data=go.Heatmap(
        z=df.values,
        x=sample_names,
        y=sorted_species,
        colorscale='YlOrRd',
        colorbar=dict(title=colorbar_title)
    ))
    
    fig.update_layout(
        xaxis_title="サンプル",
        yaxis_title="魚種",
        height=max(400, len(species) * 25),
        xaxis_tickangle=-45
    )
    
    return fig


def create_diversity_chart(species, abundance_df, sample_names):
    """多様性指標のチャートを作成"""
    
    df = abundance_df.copy()
    df.columns = sample_names
    
    # 各サンプルの指標を計算
    metrics = []
    for col in df.columns:
        counts = df[col].values
        counts = counts[counts > 0]  # ゼロを除外
        
        # 種数
        richness = len(counts)
        
        # シャノン指数
        if len(counts) > 0:
            total = counts.sum()
            proportions = counts / total
            shannon = -np.sum(proportions * np.log(proportions + 1e-10))
        else:
            shannon = 0
        
        # シンプソン指数
        if len(counts) > 1:
            total = counts.sum()
            simpson = 1 - np.sum((counts * (counts - 1)) / (total * (total - 1) + 1e-10))
        else:
            simpson = 0
        
        metrics.append({
            'Sample': col,
            'Species Richness': richness,
            'Shannon Index': shannon,
            'Simpson Index': simpson
        })
    
    metrics_df = pd.DataFrame(metrics)
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='種数 (Species Richness)',
        x=metrics_df['Sample'],
        y=metrics_df['Species Richness'],
        yaxis='y',
        offsetgroup=1
    ))
    
    fig.add_trace(go.Scatter(
        name='Shannon Index',
        x=metrics_df['Sample'],
        y=metrics_df['Shannon Index'],
        yaxis='y2',
        mode='lines+markers',
        line=dict(color='red', width=2),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        xaxis=dict(title='サンプル', tickangle=-45),
        yaxis=dict(title='種数', side='left'),
        yaxis2=dict(title='Shannon Index', side='right', overlaying='y'),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='center', x=0.5),
        height=500,
        barmode='group'
    )
    
    return fig, metrics_df


# サイドバー
with st.sidebar:
    st.header("📁 データ入力")
    
    uploaded_file = st.file_uploader(
        "MitoFish結果CSVをアップロード",
        type=['csv', 'tsv', 'txt'],
        help="MitoFishの出力ファイル（tax-results.csvなど）をアップロードしてください"
    )
    
    st.divider()
    
    st.header("⚙️ 表示設定")
    
    chart_type = st.selectbox(
        "グラフタイプ",
        ["積み上げ棒グラフ", "ヒートマップ", "多様性指標"]
    )
    
    if chart_type == "積み上げ棒グラフ":
        show_percentage = st.checkbox("相対存在量（%）で表示", value=True)
        top_n = st.slider("表示する上位種数", 5, 30, 15, 
                         help="上位N種を表示し、残りは「その他」にまとめます")
        color_scheme = st.selectbox(
            "カラースキーム",
            ["Plotly", "D3", "Set1", "Set2", "Set3", "Pastel", "Bold", "Vivid"]
        )
    
    elif chart_type == "ヒートマップ":
        log_scale = st.checkbox("対数スケールで表示", value=True)
    
    st.divider()
    
    st.header("ℹ️ About")
    st.markdown("""
    **MitoFish Visualizer**は、MitoFishパイプラインの出力結果を
    可視化するためのツールです。
    
    - 積み上げ棒グラフ
    - ヒートマップ
    - 多様性指標
    
    などの可視化に対応しています。
    """)


# メインコンテンツ
if uploaded_file is not None:
    # ファイル読み込み
    try:
        # エンコーディングを試行
        for encoding in ['utf-8', 'utf-8-sig', 'shift-jis', 'cp932']:
            try:
                uploaded_file.seek(0)
                df = pd.read_csv(uploaded_file, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        
        st.success(f"✅ ファイルを読み込みました: {uploaded_file.name}")
        
        # データ解析
        species, abundance_df, sample_names = parse_mitfish_csv(df)
        
        if species is not None:
            # メトリクス表示
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("検出種数", len(species))
            with col2:
                st.metric("サンプル数", len(sample_names))
            with col3:
                st.metric("総リード数", f"{int(abundance_df.sum().sum()):,}")
            with col4:
                avg_per_sample = abundance_df.sum().mean()
                st.metric("平均リード数/サンプル", f"{int(avg_per_sample):,}")
            
            st.divider()
            
            # グラフ表示
            if chart_type == "積み上げ棒グラフ":
                fig = create_stacked_bar_chart(
                    species, abundance_df, sample_names,
                    show_percentage=show_percentage,
                    top_n=top_n,
                    color_scheme=color_scheme
                )
                st.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "ヒートマップ":
                fig = create_heatmap(species, abundance_df, sample_names, log_scale=log_scale)
                st.plotly_chart(fig, use_container_width=True)
            
            elif chart_type == "多様性指標":
                fig, metrics_df = create_diversity_chart(species, abundance_df, sample_names)
                st.plotly_chart(fig, use_container_width=True)
                
                st.subheader("📊 多様性指標テーブル")
                st.dataframe(metrics_df.round(3), use_container_width=True)
            
            # データテーブル表示
            with st.expander("📋 生データを表示"):
                display_df = abundance_df.copy()
                display_df.insert(0, 'Species', species)
                display_df.columns = ['Species'] + sample_names
                st.dataframe(display_df, use_container_width=True)
                
                # CSVダウンロード
                csv = display_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button(
                    label="📥 CSVダウンロード",
                    data=csv,
                    file_name="mitfish_processed.csv",
                    mime="text/csv"
                )
    
    except Exception as e:
        st.error(f"ファイルの読み込みに失敗しました: {str(e)}")
        st.info("MitoFishの標準出力形式（tax-results.csv）をアップロードしてください。")

else:
    # デモデータ
    st.info("👈 サイドバーからCSVファイルをアップロードしてください")
    
    with st.expander("📖 使い方"):
        st.markdown("""
        ### 使用方法
        
        1. **ファイルをアップロード**: MitoFishの出力ファイル（`tax-results*.csv`）をアップロード
        2. **グラフタイプを選択**: 積み上げ棒グラフ、ヒートマップ、多様性指標から選択
        3. **表示設定を調整**: 相対存在量/リード数の切替、表示種数の調整など
        
        ### 対応ファイル形式
        
        - MitoFish標準出力（`tax-results.csv`）
        - カンマ区切り（CSV）、タブ区切り（TSV）
        - UTF-8, Shift-JIS エンコーディング
        
        ### 出力グラフ
        
        - **積み上げ棒グラフ**: サンプルごとの魚種構成を表示
        - **ヒートマップ**: サンプル×魚種のマトリックス表示
        - **多様性指標**: 種数、Shannon指数、Simpson指数を計算・表示
        """)
    
    with st.expander("📊 サンプルデータでデモを見る"):
        # デモ用サンプルデータ
        demo_species = ['コイ/モツゴ類', 'ボラ', 'ギンブナ/キンギョ', 'ニゴイ', 'オイカワ', 
                       'ゲンゴロウブナ', 'モロコ類', 'チチブ類', 'メダカ', 'ナマズ']
        demo_samples = ['多摩川-1', '多摩川-2', '二ヶ領用水-1', '無尽ヶ池-1', '二ヶ領用水-2']
        demo_data = np.array([
            [14, 77, 19, 84, 30],
            [10, 69, 11, 103, 27],
            [0, 31, 0, 57, 23],
            [0, 19, 9, 44, 10],
            [10, 41, 0, 90, 20],
            [0, 0, 8, 20, 0],
            [0, 16, 0, 36, 20],
            [0, 24, 0, 56, 15],
            [0, 0, 0, 458, 0],
            [0, 11, 0, 18, 0],
        ])
        
        demo_df = pd.DataFrame(demo_data)
        
        fig = create_stacked_bar_chart(
            demo_species, demo_df, demo_samples,
            show_percentage=True, top_n=10, color_scheme='Set2'
        )
        st.plotly_chart(fig, use_container_width=True)


# フッター
st.divider()
st.markdown("""
<div style="text-align: center; color: #888; font-size: 0.8rem;">
    MitoFish Visualizer | Built with Streamlit & Plotly<br>
    For environmental DNA fish detection analysis
</div>
""", unsafe_allow_html=True)
