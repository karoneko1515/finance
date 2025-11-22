# 40年間ライフプラン・資産形成シミュレーター

Python + Eel で構築した、25歳から65歳までの40年間（480ヶ月）の詳細な資産形成シミュレーションアプリケーションです。

## 特徴

- 480ヶ月の詳細な月次計算
- NISA（つみたて + 成長投資枠）対応
- 教育費・住宅購入・年金を含む総合シミュレーション
- シナリオ比較機能（SQLiteデータベース）
- Raspberry Pi対応（ネットワークサーバー運用可能）

## インストール

```bash
git clone https://github.com/karoneko1515/finance.git
cd finance/life_plan_simulator
python -m venv venv
source venv/bin/activate
pip install eel plotly pandas
```

## 起動

```bash
python main.py
```

ブラウザで http://localhost:8880 にアクセス

## ライセンス

MIT License
