"""
Eelメインファイル
PythonバックエンドとJavaScriptフロントエンドを接続
"""
import eel
import json
from data_loader import DataLoader
from calculator import LifePlanCalculator
from scenario_db import ScenarioDatabase

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
        return {
            "success": False,
            "error": str(e)
        }


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
        return {
            "success": False,
            "error": str(e)
        }


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
        return {
            "success": False,
            "error": str(e)
        }


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
        return {
            "success": False,
            "error": str(e)
        }


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
        return {
            "success": False,
            "error": str(e)
        }


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
        return {
            "success": False,
            "error": str(e)
        }


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
        return {
            "success": False,
            "error": str(e)
        }


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
        return {
            "success": False,
            "error": str(e)
        }


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
        return {
            "success": False,
            "error": str(e)
        }


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
        return {
            "success": False,
            "error": str(e)
        }


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
        return {
            "success": False,
            "error": str(e)
        }


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
        return {
            "success": False,
            "error": str(e)
        }


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
        return {
            "success": False,
            "error": str(e)
        }


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
        return {
            "success": False,
            "error": str(e)
        }


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
