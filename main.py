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

        # 計算機を再初期化して即シミュレーション実行
        global calculator
        calculator = LifePlanCalculator(data_loader)
        calculator.simulate_30_years()

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
        from datetime import date as _date
        start_age = calculator.basic_info.get("start_age", 25)
        # 実績レコードがあればそこから開始年を逆算、なければ現在年を起点に推定
        if records:
            r0 = records[0]
            start_year = r0["year"] - (r0["age"] - start_age)
        else:
            start_year = _date.today().year

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


# ==================== データ編集 / 給与テーブル ====================

@eel.expose
def get_full_salary_table():
    """
    全年齢 (start_age〜end_age) の給与データを返す（データ編集UI用）
    アンカーポイント間は直近アンカーの値を継承して展開する。

    Returns:
        dict: 各年齢の給与データリスト
    """
    try:
        start_age = calculator.basic_info.get("start_age", 25)
        end_age   = calculator.basic_info.get("end_age",   65)
        progression = data_loader.get_income_progression()
        anchor_ages = sorted([int(a) for a in progression.keys()])

        result = []
        for age in range(start_age, end_age + 1):
            applicable = anchor_ages[0]
            for a in anchor_ages:
                if age >= a:
                    applicable = a
                else:
                    break
            sd = progression[str(applicable)]
            annual = sd["base_salary"] * (12 + sd["bonus_months"])
            result.append({
                "age": age,
                "base_salary": sd["base_salary"],
                "bonus_months": sd["bonus_months"],
                "annual_income": round(annual),
                "is_anchor": str(age) in progression
            })
        return {"success": True, "data": result}
    except Exception as e:
        return _api_error(e)


@eel.expose
def update_salary_range(start_age, end_age, base_salary, bonus_months, change_type="absolute"):
    """
    指定年齢範囲の給与を一括更新して再シミュレーション

    Args:
        start_age (int):    対象開始年齢
        end_age (int):      対象終了年齢
        base_salary (int):  月給（円）または変化率（change_type="percent"のとき %）
        bonus_months (float): ボーナス月数（-1 で変更なし）
        change_type (str): "absolute" or "percent"

    Returns:
        dict: 保存・再計算結果
    """
    try:
        plan_data = data_loader.get_all_data()
        prog = plan_data["income_progression"]

        # 既存アンカーを全年齢に展開してから範囲を上書き
        anchor_ages = sorted([int(a) for a in prog.keys()])
        s_age = int(data_loader.get_basic_info().get("start_age", 25))
        e_age = int(data_loader.get_basic_info().get("end_age",   65))

        # まず全年齢を展開
        full = {}
        for age in range(s_age, e_age + 1):
            app = anchor_ages[0]
            for a in anchor_ages:
                if age >= a:
                    app = a
                else:
                    break
            full[str(age)] = dict(prog[str(app)])

        # 範囲内を上書き
        for age in range(int(start_age), int(end_age) + 1):
            cur = full[str(age)]
            if change_type == "percent":
                cur["base_salary"] = round(cur["base_salary"] * (1 + float(base_salary) / 100))
            else:
                cur["base_salary"] = int(base_salary)
            if float(bonus_months) >= 0:
                cur["bonus_months"] = float(bonus_months)
            full[str(age)] = cur

        plan_data["income_progression"] = full
        data_loader.save_user_plan(plan_data)
        global calculator
        calculator = LifePlanCalculator(data_loader)
        calculator.simulate_30_years()
        return {"success": True, "message": f"{start_age}〜{end_age}歳の給与を更新しました"}
    except Exception as e:
        return _api_error(e)


@eel.expose
def update_single_age_salary(age, base_salary, bonus_months):
    """
    1歳分の給与を更新して再シミュレーション

    Args:
        age (int): 対象年齢
        base_salary (int): 月給（円）
        bonus_months (float): ボーナス月数

    Returns:
        dict: 保存・再計算結果
    """
    try:
        plan_data = data_loader.get_all_data()
        prog = plan_data["income_progression"]

        # まず全年齢展開
        anchor_ages = sorted([int(a) for a in prog.keys()])
        s_age = int(data_loader.get_basic_info().get("start_age", 25))
        e_age = int(data_loader.get_basic_info().get("end_age",   65))
        full = {}
        for a in range(s_age, e_age + 1):
            app = anchor_ages[0]
            for x in anchor_ages:
                if a >= x:
                    app = x
                else:
                    break
            full[str(a)] = dict(prog[str(app)])

        full[str(int(age))] = {
            "base_salary": int(base_salary),
            "bonus_months": float(bonus_months)
        }
        plan_data["income_progression"] = full
        data_loader.save_user_plan(plan_data)
        global calculator
        calculator = LifePlanCalculator(data_loader)
        calculator.simulate_30_years()
        return {"success": True, "message": f"{age}歳の給与を更新しました"}
    except Exception as e:
        return _api_error(e)


@eel.expose
def get_custom_events():
    """カスタムライフイベント一覧を取得"""
    try:
        plan_data = data_loader.get_all_data()
        events = plan_data.get("life_events", {}).get("custom_events", [])
        return {"success": True, "data": events}
    except Exception as e:
        return _api_error(e)


@eel.expose
def save_custom_event(event_data):
    """
    カスタムライフイベントを保存（id があれば更新、なければ追加）

    Args:
        event_data (dict): {id?, name, age, cost, description?}

    Returns:
        dict: 保存結果
    """
    try:
        plan_data = data_loader.get_all_data()
        if "custom_events" not in plan_data["life_events"]:
            plan_data["life_events"]["custom_events"] = []
        events = plan_data["life_events"]["custom_events"]

        name = str(event_data.get("name", "")).strip()
        if not name:
            return {"success": False, "error": "イベント名を入力してください"}
        age  = int(event_data.get("age", 0))
        cost = int(event_data.get("cost", 0))
        desc = str(event_data.get("description", ""))
        ev_id = event_data.get("id")

        if ev_id:
            # 更新
            for ev in events:
                if ev.get("id") == ev_id:
                    ev.update({"name": name, "age": age, "cost": cost, "description": desc})
                    break
        else:
            # 新規追加（id はタイムスタンプで生成）
            import time
            events.append({"id": f"ev_{int(time.time()*1000)}", "name": name, "age": age, "cost": cost, "description": desc})

        plan_data["life_events"]["custom_events"] = events
        data_loader.save_user_plan(plan_data)
        global calculator
        calculator = LifePlanCalculator(data_loader)
        calculator.simulate_30_years()
        return {"success": True, "message": "カスタムイベントを保存しました"}
    except Exception as e:
        return _api_error(e)


@eel.expose
def delete_custom_event(ev_id):
    """
    カスタムライフイベントを削除

    Args:
        ev_id (str): イベントID

    Returns:
        dict: 削除結果
    """
    try:
        plan_data = data_loader.get_all_data()
        events = plan_data.get("life_events", {}).get("custom_events", [])
        plan_data["life_events"]["custom_events"] = [e for e in events if e.get("id") != ev_id]
        data_loader.save_user_plan(plan_data)
        global calculator
        calculator = LifePlanCalculator(data_loader)
        calculator.simulate_30_years()
        return {"success": True, "message": "カスタムイベントを削除しました"}
    except Exception as e:
        return _api_error(e)


@eel.expose
def update_phase_expenses(phase_name, monthly_expenses):
    """
    フェーズ別の月次生活費を一括更新

    Args:
        phase_name (str): フェーズ名 (phase1〜phase7)
        monthly_expenses (dict): {category: amount} の辞書

    Returns:
        dict: 保存・再計算結果
    """
    try:
        plan_data = data_loader.get_all_data()
        if phase_name not in plan_data.get("phase_definitions", {}):
            return {"success": False, "error": f"フェーズ '{phase_name}' が見つかりません"}
        plan_data["phase_definitions"][phase_name]["monthly_expenses"] = {
            k: int(v) for k, v in monthly_expenses.items() if int(v) >= 0
        }
        data_loader.save_user_plan(plan_data)
        global calculator
        calculator = LifePlanCalculator(data_loader)
        calculator.simulate_30_years()
        return {"success": True, "message": f"{phase_name}の生活費を更新しました"}
    except Exception as e:
        return _api_error(e)


# ==================== Feature 1: 実績ベース将来予測 ====================

@eel.expose
def run_simulation_from_actual():
    """
    最新の実績現金残高を起点に将来予測を調整して返す。
    計画シミュレーション結果に「実績との乖離額」を加算した予測を返す。

    Returns:
        dict: 調整済み年次データ + 乖離情報
    """
    try:
        if not calculator.yearly_data:
            return {"success": False, "error": "先にシミュレーションを実行してください"}

        records = scenario_db.get_all_actual_records()
        if not records:
            return {"success": False, "error": "実績データがありません。先に実績を入力してください"}

        latest = records[-1]
        actual_age = latest["age"]
        actual_cash = latest["cash_balance_actual"]

        # 計画上の同年齢の現金残高を取得
        plan_entry = next((d for d in calculator.yearly_data if d["age"] == actual_age), None)
        if not plan_entry:
            return {"success": False, "error": f"{actual_age}歳のシミュレーションデータがありません"}

        plan_cash = plan_entry.get("cash", 0)
        cash_diff = actual_cash - plan_cash

        # 全将来年度に差分を加算（簡易オフセット方式）
        adjusted = []
        start_age = calculator.basic_info.get("start_age", 25)
        for d in calculator.yearly_data:
            entry = dict(d)
            if d["age"] >= actual_age:
                entry["assets_end_adjusted"] = d["assets_end"] + cash_diff
                entry["cash_adjusted"] = d.get("cash", 0) + cash_diff
            else:
                entry["assets_end_adjusted"] = d["assets_end"]
                entry["cash_adjusted"] = d.get("cash", 0)
            adjusted.append(entry)

        return {
            "success": True,
            "data": adjusted,
            "from_age": actual_age,
            "cash_diff": cash_diff,
            "actual_cash": actual_cash,
            "plan_cash": plan_cash
        }
    except Exception as e:
        return _api_error(e)


# ==================== Feature 4: 目標達成率ゲージ ====================

@eel.expose
def get_goal_achievement():
    """
    各種目標の達成率を計算して返す

    Returns:
        dict: 目標達成状況サマリー
    """
    try:
        if not calculator.yearly_data:
            return {"success": False, "error": "シミュレーションを先に実行してください"}

        from datetime import date as _date
        records = scenario_db.get_all_actual_records()
        has_actual = bool(records)
        latest = records[-1] if records else None

        start_age = calculator.basic_info.get("start_age", 25)
        end_age   = calculator.basic_info.get("end_age",   65)

        # 現在の推定年齢: 実績があれば最新レコードの年齢、なければ日付から推定
        if latest:
            actual_age = latest["age"]
        else:
            if records:
                r0 = records[0]
                sim_start_year = r0["year"] - (r0["age"] - start_age)
            else:
                sim_start_year = _date.today().year
            actual_age = min(end_age, start_age + (_date.today().year - sim_start_year))

        # 65歳時の計画最終資産
        final_entry  = calculator.yearly_data[-1]
        target_final = final_entry.get("assets_end", 0)

        # 現在年齢の計画エントリを取得（なければ最初の年）
        current_year_data = next(
            (d for d in calculator.yearly_data if d["age"] == actual_age),
            calculator.yearly_data[0]
        )
        current_plan = current_year_data.get("assets_end", 0)

        # 緊急予備費目標（月支出×6ヶ月分）
        monthly_expenses_est = current_year_data.get("expenses_total", 0) / 12
        emergency_target = monthly_expenses_est * 6

        # 緊急予備費の現在値: 実績があれば実績現金、なければ計画現金残高
        if has_actual:
            emergency_current = latest["cash_balance_actual"]
        else:
            emergency_current = current_year_data.get("cash", 0)

        # NISA積立進捗（計画累計）
        nisa_limit = (
            calculator.investment_settings["nisa"].get("tsumitate_limit", 12000000)
            + calculator.investment_settings["nisa"].get("growth_limit", 6000000)
        )
        nisa_balance_current = (
            current_year_data.get("nisa_tsumitate", 0)
            + current_year_data.get("nisa_growth", 0)
        )

        # 退職準備進捗（現計画資産 / 最終目標）
        retirement_rate = min(100, round(current_plan / target_final * 100, 1)) if target_final else 0
        emergency_rate  = min(100, round(emergency_current / emergency_target * 100, 1)) if emergency_target else 0
        nisa_rate       = min(100, round(nisa_balance_current / nisa_limit * 100, 1)) if nisa_limit else 0

        # 老後2000万問題: 65歳時の資産が2000万以上かどうか
        target_2000 = 20_000_000
        goal_2000_rate = min(100, round(target_final / target_2000 * 100, 1))

        return {
            "success": True,
            "has_actual": has_actual,
            "current_age": actual_age,
            "data": {
                "retirement": {
                    "label": "退職資産目標",
                    "current": current_plan,
                    "target": target_final,
                    "rate": retirement_rate,
                    "unit": "円",
                    "source": "plan"
                },
                "emergency": {
                    "label": "緊急予備費 (支出6ヶ月分)",
                    "current": emergency_current,
                    "target": round(emergency_target),
                    "rate": emergency_rate,
                    "unit": "円",
                    "source": "actual" if has_actual else "plan"
                },
                "nisa": {
                    "label": "NISA累積残高",
                    "current": nisa_balance_current,
                    "target": nisa_limit,
                    "rate": nisa_rate,
                    "unit": "円",
                    "source": "plan"
                },
                "goal_2000": {
                    "label": "老後2,000万円目標",
                    "current": target_final,
                    "target": target_2000,
                    "rate": goal_2000_rate,
                    "unit": "円",
                    "source": "plan"
                }
            }
        }
    except Exception as e:
        return _api_error(e)


@eel.expose
def get_age_for_year(target_year):
    """
    指定年に対応する推定年齢を返す（実績入力フォームの年齢自動補完用）

    実績レコードがあれば正確に逆算、なければ今日の日付から推定。

    Args:
        target_year (int): 対象年

    Returns:
        dict: {success, age, is_exact}
    """
    try:
        from datetime import date as _date
        start_age = calculator.basic_info.get("start_age", 25)
        end_age   = calculator.basic_info.get("end_age", 65)
        records = scenario_db.get_all_actual_records()

        if records:
            r0 = records[0]
            sim_start_year = r0["year"] - (r0["age"] - start_age)
            is_exact = True
        else:
            sim_start_year = _date.today().year
            is_exact = False

        age = start_age + (int(target_year) - sim_start_year)
        age = max(start_age, min(end_age, age))
        return {"success": True, "age": age, "is_exact": is_exact}
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
