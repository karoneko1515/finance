"""
Eelメインファイル
PythonバックエンドとJavaScriptフロントエンドを接続
"""
import eel
import json
import logging
from data_loader import DataLoader
from calculator import LifePlanCalculator
from scenario_db import ScenarioDatabase

# 内部エラーをファイルにログ（フロントエンドには詳細を返さない）
logging.basicConfig(
    filename='app.log',
    level=logging.ERROR,
    format='%(asctime)s %(levelname)s %(message)s'
)

def _api_error(e):
    """内部エラーをログに記録し、汎用エラーメッセージを返す（詳細情報を外部に漏らさない）"""
    logging.error("APIエラー: %s", e, exc_info=True)
    return {"success": False, "error": "処理中にエラーが発生しました"}


# Eelの初期化
eel.init('web')

# グローバルインスタンス
data_loader = DataLoader()
calculator = LifePlanCalculator(data_loader)
scenario_db = ScenarioDatabase()  # シナリオデータベース


@eel.expose
def run_simulation():
    """
    シミュレーションを実行

    Returns:
        dict: 計算結果
    """
    try:
        monthly_data, yearly_data = calculator.simulate_30_years()
        return {
            "success": True,
            "data": calculator.export_to_dict()
        }
    except Exception as e:
        return _api_error(e)


@eel.expose
def get_age_detail(age):
    """
    特定年齢の12ヶ月分詳細データを取得

    Args:
        age: 年齢

    Returns:
        dict: 月次データ
    """
    try:
        monthly_details = calculator.get_age_detail(age)
        return {
            "success": True,
            "data": monthly_details
        }
    except Exception as e:
        return _api_error(e)


@eel.expose
def get_age_assets_detail(age):
    """
    特定年齢の資産詳細情報を取得

    Args:
        age: 年齢

    Returns:
        dict: 資産詳細情報
    """
    try:
        detail = calculator.get_age_assets_detail(age)
        return {
            "success": True,
            "data": detail
        }
    except Exception as e:
        return _api_error(e)


@eel.expose
def get_education_summary():
    """
    教育費の詳細サマリーを取得

    Returns:
        dict: 教育費サマリー
    """
    try:
        summary = calculator.get_education_summary()
        return {
            "success": True,
            "data": summary
        }
    except Exception as e:
        return _api_error(e)


@eel.expose
def get_dividend_summary():
    """
    配当金の詳細サマリーを取得

    Returns:
        dict: 配当金サマリー
    """
    try:
        summary = calculator.get_dividend_summary()
        return {
            "success": True,
            "data": summary
        }
    except Exception as e:
        return _api_error(e)


@eel.expose
def get_plan_data():
    """
    現在のプラン設定を取得

    Returns:
        dict: プラン設定
    """
    try:
        return {
            "success": True,
            "data": data_loader.get_all_data()
        }
    except Exception as e:
        return _api_error(e)


@eel.expose
def update_plan_data(plan_json):
    """
    プラン設定を更新

    Args:
        plan_json: JSON文字列またはdict

    Returns:
        dict: 更新結果
    """
    try:
        if isinstance(plan_json, str):
            plan_data = json.loads(plan_json)
        else:
            plan_data = plan_json

        data_loader.save_user_plan(plan_data)

        # 計算機を再初期化
        global calculator
        calculator = LifePlanCalculator(data_loader)

        return {
            "success": True,
            "message": "プラン設定を更新しました"
        }
    except Exception as e:
        return _api_error(e)


@eel.expose
def reset_plan_to_default():
    """
    プラン設定をデフォルトに戻す

    Returns:
        dict: リセット結果
    """
    try:
        data_loader.reset_to_default()

        # 計算機を再初期化
        global calculator
        calculator = LifePlanCalculator(data_loader)

        return {
            "success": True,
            "message": "デフォルト設定に戻しました"
        }
    except Exception as e:
        return _api_error(e)


@eel.expose
def export_data_csv():
    """
    データをCSV形式でエクスポート

    Returns:
        dict: CSV文字列
    """
    try:
        import pandas as pd

        # 年次データをDataFrameに変換
        df_yearly = pd.DataFrame(calculator.yearly_data)

        # CSV文字列に変換
        csv_string = df_yearly.to_csv(index=False, encoding='utf-8-sig')

        return {
            "success": True,
            "data": csv_string
        }
    except Exception as e:
        return _api_error(e)


@eel.expose
def save_scenario_to_db(name, settings, result_data):
    """
    シナリオをデータベースに保存

    Args:
        name: シナリオ名
        settings: 設定データ
        result_data: 計算結果データ

    Returns:
        dict: 保存結果
    """
    try:
        result = scenario_db.save_scenario(name, settings, result_data)
        return result
    except Exception as e:
        return _api_error(e)


@eel.expose
def load_scenario_from_db(name):
    """
    データベースからシナリオを読み込み

    Args:
        name: シナリオ名

    Returns:
        dict: シナリオデータ
    """
    try:
        scenario = scenario_db.load_scenario(name)
        if scenario:
            return {
                "success": True,
                "data": scenario
            }
        else:
            return {
                "success": False,
                "error": "シナリオが見つかりません"
            }
    except Exception as e:
        return _api_error(e)


@eel.expose
def list_saved_scenarios():
    """
    保存されているシナリオのリストを取得

    Returns:
        dict: シナリオリスト
    """
    try:
        scenarios = scenario_db.list_scenarios()
        return {
            "success": True,
            "data": scenarios
        }
    except Exception as e:
        return _api_error(e)


@eel.expose
def delete_scenario_from_db(name):
    """
    データベースからシナリオを削除

    Args:
        name: シナリオ名

    Returns:
        dict: 削除結果
    """
    try:
        result = scenario_db.delete_scenario(name)
        return result
    except Exception as e:
        return _api_error(e)


@eel.expose
def calculate_scenario_comparison(scenarios):
    """
    複数シナリオを比較計算

    Args:
        scenarios: シナリオ設定のリスト

    Returns:
        dict: 比較結果
    """
    try:
        results = []

        for scenario in scenarios:
            # シナリオごとに一時的なDataLoaderとCalculatorを作成
            temp_loader = DataLoader()
            plan_data = temp_loader.get_all_data()

            # シナリオ設定を適用
            if "investment_return" in scenario:
                plan_data["investment_settings"]["nisa"]["expected_return"] = scenario["investment_return"]

            if "spouse_income" in scenario:
                if scenario["spouse_income"] == "なし":
                    plan_data["spouse_income"]["28-47"] = 0
                    plan_data["spouse_income"]["48-55"] = 0
                elif scenario["spouse_income"] == "増額":
                    plan_data["spouse_income"]["28-47"] = 120000
                    plan_data["spouse_income"]["48-55"] = 150000

            if "salary_growth" in scenario:
                if scenario["salary_growth"] == "+10%":
                    for age_key in plan_data["income_progression"]:
                        plan_data["income_progression"][age_key]["base_salary"] *= 1.1
                elif scenario["salary_growth"] == "-10%":
                    for age_key in plan_data["income_progression"]:
                        plan_data["income_progression"][age_key]["base_salary"] *= 0.9

            # 計算実行
            temp_loader.plan_data = plan_data
            temp_calc = LifePlanCalculator(temp_loader)
            monthly, yearly = temp_calc.simulate_30_years()

            results.append({
                "scenario_name": scenario.get("name", "シナリオ"),
                "yearly_data": yearly,
                "final_assets": yearly[-1]["assets_end"] if yearly else 0
            })

        return {
            "success": True,
            "data": results
        }
    except Exception as e:
        return _api_error(e)


# ==================== 実績管理 API ====================

@eel.expose
def save_actual_record(record_year, record_month, age,
                       income_actual, expenses_actual,
                       investment_actual, cash_balance_actual, notes=""):
    """
    月次実績データを保存

    Args:
        record_year:  記録年（例: 2025）
        record_month: 記録月 (1-12)
        age:          その月の年齢
        income_actual:       実際の収入（円）
        expenses_actual:     実際の支出（円）
        investment_actual:   実際の投資（円）
        cash_balance_actual: 月末現金残高（円）
        notes:               メモ（オプション）

    Returns:
        dict: 保存結果
    """
    try:
        if not (1 <= int(record_month) <= 12):
            return {"success": False, "error": "月は1〜12で指定してください"}
        return scenario_db.save_actual_record(
            record_year, record_month, age,
            income_actual, expenses_actual,
            investment_actual, cash_balance_actual, notes
        )
    except Exception as e:
        return _api_error(e)


@eel.expose
def get_actual_records():
    """
    全実績レコードを取得

    Returns:
        dict: 実績レコードリスト
    """
    try:
        records = scenario_db.get_all_actual_records()
        return {"success": True, "data": records}
    except Exception as e:
        return _api_error(e)


@eel.expose
def delete_actual_record(record_year, record_month):
    """
    指定年月の実績を削除

    Args:
        record_year:  記録年
        record_month: 記録月

    Returns:
        dict: 削除結果
    """
    try:
        return scenario_db.delete_actual_record(record_year, record_month)
    except Exception as e:
        return _api_error(e)


@eel.expose
def get_plan_vs_actual():
    """
    計画値と実績値の比較データを生成

    Returns:
        dict: 比較データ（計画・実績・乖離）
    """
    try:
        if not calculator.yearly_data:
            return {"success": False, "error": "先にシミュレーションを実行してください"}

        records = scenario_db.get_all_actual_records()

        # 月次実績をキーにした辞書 {(year, month): record}
        actual_map = {(r["year"], r["month"]): r for r in records}

        # 計画値の月次データを年単位に集計し、実績と照合
        comparison = []
        start_year = 2025  # TODO: basic_infoから取得
        start_age = calculator.basic_info.get("start_age", 25)

        for yd in calculator.yearly_data:
            age = yd["age"]
            sim_year = start_year + (age - start_age)

            # 12ヶ月分の実績を合計
            actual_income = 0
            actual_expenses = 0
            actual_investment = 0
            actual_cash = None
            months_entered = 0

            for m in range(1, 13):
                key = (sim_year, m)
                if key in actual_map:
                    r = actual_map[key]
                    actual_income += r["income_actual"]
                    actual_expenses += r["expenses_actual"]
                    actual_investment += r["investment_actual"]
                    actual_cash = r["cash_balance_actual"]  # 最終月の残高
                    months_entered += 1

            entry = {
                "age": age,
                "year": sim_year,
                "plan_income": yd.get("income_total", 0),
                "plan_expenses": yd.get("expenses_total", 0),
                "plan_investment": yd.get("investment_total", 0),
                "plan_assets": yd.get("assets_end", 0),
                "actual_income": actual_income if months_entered > 0 else None,
                "actual_expenses": actual_expenses if months_entered > 0 else None,
                "actual_investment": actual_investment if months_entered > 0 else None,
                "actual_cash": actual_cash,
                "months_entered": months_entered,
            }

            # 乖離計算（実績がある場合のみ）
            if months_entered == 12:
                entry["income_diff"] = actual_income - yd.get("income_total", 0)
                entry["expenses_diff"] = actual_expenses - yd.get("expenses_total", 0)
                entry["investment_diff"] = actual_investment - yd.get("investment_total", 0)
            else:
                entry["income_diff"] = None
                entry["expenses_diff"] = None
                entry["investment_diff"] = None

            comparison.append(entry)

        return {"success": True, "data": comparison}
    except Exception as e:
        return _api_error(e)


def main():
    """メイン関数"""
    import gc

    print("=" * 60)
    print("30年間ライフプラン・資産形成シミュレーター")
    print("=" * 60)
    print("サーバーを起動しています...")
    print("終了するには、Ctrl+C を押してください。")
    print("=" * 60)

    # メモリ最適化
    gc.collect()

    # 初回シミュレーション実行（キャッシュ作成）
    print("\n初期シミュレーションを実行中...")
    calculator.simulate_30_years()
    print("完了！\n")

    print("アクセスURL: http://localhost:8880")
    print("ネットワーク内アクセス: http://[ラズパイのIP]:8880")
    print("=" * 60 + "\n")

    # Eelアプリ起動（ラズパイ最適化設定）
    try:
        eel.start('index.html',
                  host='0.0.0.0',  # すべてのネットワークインターフェースからアクセス可能
                  port=8880,        # ポート8880に変更
                  size=(1400, 900),
                  mode=None,        # ブラウザ自動起動無効（サーバーモード）
                  close_callback=lambda *args: None)
    except (SystemExit, KeyboardInterrupt):
        print("\nアプリケーションを終了しました。")
        gc.collect()  # 終了時にメモリクリーンアップ


if __name__ == "__main__":
    main()
