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
def get_monthly_breakdown_detail(age):
    """
    特定年齢のボーナス月・非ボーナス月の詳細内訳を取得

    Args:
        age: 年齢

    Returns:
        dict: ボーナス月・非ボーナス月の詳細内訳
    """
    try:
        # シミュレーションが実行されていない場合は先に実行
        if not calculator.monthly_data:
            calculator.simulate_30_years()

        detail = calculator.get_monthly_breakdown_detail(age)
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
def run_retirement_simulation():
    """
    退職後シミュレーション（65-90歳）を実行

    Returns:
        dict: 計算結果
    """
    try:
        retirement_data, summary = calculator.simulate_retirement()
        return {
            "success": True,
            "data": {
                "retirement_data": retirement_data,
                "summary": summary
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@eel.expose
def run_monte_carlo_simulation(num_simulations=1000):
    """
    モンテカルロシミュレーションを実行

    Args:
        num_simulations: シミュレーション回数

    Returns:
        dict: 計算結果
    """
    try:
        result = calculator.run_monte_carlo(num_simulations=num_simulations)
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@eel.expose
def run_monte_carlo_advanced_simulation(num_simulations=1000):
    """
    本格的なモンテカルロシミュレーションを実行
    年ごとに異なるリターンを適用してsequence-of-returnsリスクを考慮

    Args:
        num_simulations: シミュレーション回数

    Returns:
        dict: 計算結果
    """
    try:
        result = calculator.run_monte_carlo_advanced(num_simulations=num_simulations)
        return {
            "success": True,
            "data": result
        }
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


@eel.expose
def get_alerts_and_risk_score():
    """
    アラートとリスクスコアを取得

    Returns:
        dict: アラートとリスクスコア
    """
    try:
        monthly, yearly = calculator.simulate_30_years()

        # アラート生成
        alerts = calculator.generate_alerts(yearly)

        # リスクスコア計算
        risk_score = calculator.calculate_risk_score(yearly)

        return {
            "success": True,
            "data": {
                "alerts": alerts,
                "risk_score": risk_score
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@eel.expose
def calculate_furusato_nozei(gross_annual_income, dependents=0):
    """
    ふるさと納税限度額を計算

    Args:
        gross_annual_income: 年間総収入
        dependents: 扶養家族数

    Returns:
        dict: ふるさと納税情報
    """
    try:
        result = calculator.calculate_furusato_nozei_limit(gross_annual_income, dependents)

        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@eel.expose
def calculate_medical_deduction(medical_expenses, gross_annual_income):
    """
    医療費控除を計算

    Args:
        medical_expenses: 年間医療費
        gross_annual_income: 年間総収入

    Returns:
        dict: 医療費控除情報
    """
    try:
        result = calculator.calculate_medical_deduction(medical_expenses, gross_annual_income)

        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@eel.expose
def run_optimization_analysis(num_patterns=5):
    """
    最適化提案AIを実行

    Args:
        num_patterns: 生成する改善パターン数

    Returns:
        dict: 最適化提案結果
    """
    try:
        result = calculator.run_optimization_analysis(num_patterns)

        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@eel.expose
def calculate_pension_deferral_analysis(start_ages):
    """
    年金繰上げ/繰下げの損益分岐点分析

    Args:
        start_ages: 分析する受給開始年齢のリスト（例: [60, 65, 70, 75]）

    Returns:
        dict: 各受給開始年齢での分析結果
    """
    try:
        results = []

        for start_age in start_ages:
            # 年金額を計算
            monthly_amount, spouse_amount = calculator.calculate_pension_amount_detailed(start_age)

            # 累積受給額を計算（90歳まで）
            years_receiving = 90 - start_age
            total_received = (monthly_amount + spouse_amount) * 12 * years_receiving

            results.append({
                "start_age": start_age,
                "monthly_amount": monthly_amount,
                "spouse_amount": spouse_amount,
                "total_monthly": monthly_amount + spouse_amount,
                "years_receiving": years_receiving,
                "total_received": total_received,
                "adjustment_rate": (monthly_amount / 180000 - 1) * 100  # 65歳基準からの変化率
            })

        # 損益分岐点を計算
        base_65 = next((r for r in results if r["start_age"] == 65), None)

        if base_65:
            for result in results:
                if result["start_age"] != 65:
                    # 損益分岐年齢を計算
                    # 65歳受給との累積差額がゼロになる年齢
                    monthly_diff = result["total_monthly"] - base_65["total_monthly"]
                    if monthly_diff != 0:
                        months_to_breakeven = abs((65 - result["start_age"]) * base_65["total_monthly"] * 12 / monthly_diff)
                        breakeven_age = result["start_age"] + months_to_breakeven / 12
                        result["breakeven_age"] = round(breakeven_age, 1)
                    else:
                        result["breakeven_age"] = None

        return {
            "success": True,
            "data": {
                "analysis": results,
                "recommendation": "70歳繰下げで受給額が42%増加します。" if len(results) > 0 else ""
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@eel.expose
def get_custom_events():
    """
    カスタム大きな買い物イベント一覧を取得

    Returns:
        dict: イベント一覧
    """
    try:
        events = calculator.get_custom_events()
        return {
            "success": True,
            "data": events
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@eel.expose
def add_custom_event(event_data):
    """
    新しいカスタムイベントを追加

    Args:
        event_data: イベント情報（dict）

    Returns:
        dict: 追加結果
    """
    try:
        plan_data = data_loader.get_all_data()

        if "custom_large_purchase_events" not in plan_data:
            plan_data["custom_large_purchase_events"] = {
                "enabled": True,
                "events": [],
                "categories": {
                    "vehicle": "車両",
                    "travel": "旅行",
                    "home_improvement": "住宅改修",
                    "hobby": "趣味",
                    "education": "教育",
                    "other": "その他"
                }
            }

        # イベントIDを自動生成
        import uuid
        event_data["id"] = str(uuid.uuid4())[:8]

        # デフォルト値を設定
        if "enabled" not in event_data:
            event_data["enabled"] = True
        if "auto_saving" not in event_data:
            event_data["auto_saving"] = {
                "enabled": False,
                "start_age": max(25, event_data["age"] - 5),
                "monthly_amount": 0
            }

        plan_data["custom_large_purchase_events"]["events"].append(event_data)

        # プラン保存
        data_loader.save_user_plan(plan_data)

        # 計算機を再初期化
        global calculator
        calculator = LifePlanCalculator(data_loader)

        return {
            "success": True,
            "message": "イベントを追加しました",
            "event_id": event_data["id"]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@eel.expose
def update_custom_event(event_id, event_data):
    """
    既存のカスタムイベントを更新

    Args:
        event_id: イベントID
        event_data: 更新するイベント情報（dict）

    Returns:
        dict: 更新結果
    """
    try:
        plan_data = data_loader.get_all_data()

        if "custom_large_purchase_events" not in plan_data:
            return {
                "success": False,
                "error": "カスタムイベント設定が見つかりません"
            }

        events = plan_data["custom_large_purchase_events"]["events"]
        event_found = False

        for i, event in enumerate(events):
            if event["id"] == event_id:
                # イベントデータを更新（IDは保持）
                event_data["id"] = event_id
                events[i] = event_data
                event_found = True
                break

        if not event_found:
            return {
                "success": False,
                "error": "指定されたイベントが見つかりません"
            }

        # プラン保存
        data_loader.save_user_plan(plan_data)

        # 計算機を再初期化
        global calculator
        calculator = LifePlanCalculator(data_loader)

        return {
            "success": True,
            "message": "イベントを更新しました"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@eel.expose
def delete_custom_event(event_id):
    """
    カスタムイベントを削除

    Args:
        event_id: イベントID

    Returns:
        dict: 削除結果
    """
    try:
        plan_data = data_loader.get_all_data()

        if "custom_large_purchase_events" not in plan_data:
            return {
                "success": False,
                "error": "カスタムイベント設定が見つかりません"
            }

        events = plan_data["custom_large_purchase_events"]["events"]
        original_count = len(events)

        # イベントを削除
        plan_data["custom_large_purchase_events"]["events"] = [
            event for event in events if event["id"] != event_id
        ]

        if len(plan_data["custom_large_purchase_events"]["events"]) == original_count:
            return {
                "success": False,
                "error": "指定されたイベントが見つかりません"
            }

        # プラン保存
        data_loader.save_user_plan(plan_data)

        # 計算機を再初期化
        global calculator
        calculator = LifePlanCalculator(data_loader)

        return {
            "success": True,
            "message": "イベントを削除しました"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@eel.expose
def toggle_custom_event(event_id, enabled):
    """
    カスタムイベントの有効/無効を切り替え

    Args:
        event_id: イベントID
        enabled: 有効フラグ（True/False）

    Returns:
        dict: 切り替え結果
    """
    try:
        plan_data = data_loader.get_all_data()

        if "custom_large_purchase_events" not in plan_data:
            return {
                "success": False,
                "error": "カスタムイベント設定が見つかりません"
            }

        events = plan_data["custom_large_purchase_events"]["events"]
        event_found = False

        for event in events:
            if event["id"] == event_id:
                event["enabled"] = enabled
                event_found = True
                break

        if not event_found:
            return {
                "success": False,
                "error": "指定されたイベントが見つかりません"
            }

        # プラン保存
        data_loader.save_user_plan(plan_data)

        # 計算機を再初期化
        global calculator
        calculator = LifePlanCalculator(data_loader)

        return {
            "success": True,
            "message": f"イベントを{'有効' if enabled else '無効'}にしました"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@eel.expose
def simulate_with_custom_events(event_states):
    """
    特定のカスタムイベントパターンでシミュレーション実行

    Args:
        event_states: イベントID -> 有効フラグ のマッピング（dict）

    Returns:
        dict: シミュレーション結果
    """
    try:
        # 一時的なDataLoaderとCalculatorを作成
        temp_loader = DataLoader()
        plan_data = temp_loader.get_all_data()

        if "custom_large_purchase_events" in plan_data:
            # イベントの有効/無効を設定
            for event in plan_data["custom_large_purchase_events"]["events"]:
                if event["id"] in event_states:
                    event["enabled"] = event_states[event["id"]]

        # 一時的な計算機でシミュレーション実行
        temp_loader.plan_data = plan_data
        temp_calc = LifePlanCalculator(temp_loader)
        monthly, yearly = temp_calc.simulate_30_years()

        return {
            "success": True,
            "data": {
                "yearly_data": yearly,
                "final_assets": yearly[-1]["assets_end"] if yearly else 0,
                "custom_event_funds": yearly[-1].get("custom_event_funds", {}) if yearly else {}
            }
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
