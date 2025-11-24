"""
ライフプラン計算エンジン
30年間の詳細な資産形成シミュレーションを実行
"""
import numpy as np
import pandas as pd
from datetime import datetime
from data_loader import DataLoader
import random


class LifePlanCalculator:
    """ライフプラン計算クラス"""

    def __init__(self, data_loader=None):
        """
        初期化

        Args:
            data_loader: DataLoaderインスタンス（Noneの場合は新規作成）
        """
        self.loader = data_loader if data_loader else DataLoader()
        self.basic_info = self.loader.get_basic_info()
        self.life_events = self.loader.get_life_events()
        self.income_progression = self.loader.get_income_progression()
        self.investment_settings = self.loader.get_investment_settings()
        self.tax_rates = self.loader.get_tax_rates()
        self.inflation_settings = self.loader.get_inflation_settings()

        # 計算結果キャッシュ
        self.monthly_data = []
        self.yearly_data = []

    def calculate_social_insurance_detailed(self, monthly_salary):
        """
        社会保険料の詳細計算（健康保険・厚生年金・雇用保険）

        Args:
            monthly_salary: 月額給与

        Returns:
            dict: 各保険料の詳細
        """
        if "social_insurance_detailed" in self.tax_rates and self.tax_rates["social_insurance_detailed"].get("enabled", False):
            si_detail = self.tax_rates["social_insurance_detailed"]

            # 健康保険料（標準報酬月額に上限あり）
            health_max = si_detail["health_insurance"]["max_monthly_salary"]
            health_salary = min(monthly_salary, health_max)
            health_insurance = health_salary * si_detail["health_insurance"]["rate"] * 0.5  # 労使折半

            # 厚生年金保険料（標準報酬月額に上限あり）
            pension_max = si_detail["employee_pension"]["max_monthly_salary"]
            pension_salary = min(monthly_salary, pension_max)
            employee_pension = pension_salary * si_detail["employee_pension"]["rate"] * si_detail["employee_pension"]["employee_share"]

            # 雇用保険料
            employment_insurance = monthly_salary * si_detail["employment_insurance"]["rate"]

            return {
                "health_insurance": health_insurance,
                "employee_pension": employee_pension,
                "employment_insurance": employment_insurance,
                "total": health_insurance + employee_pension + employment_insurance
            }
        else:
            # 簡易計算にフォールバック
            total = monthly_salary * self.tax_rates["social_insurance_rate"]
            return {
                "health_insurance": total * 0.4,
                "employee_pension": total * 0.55,
                "employment_insurance": total * 0.05,
                "total": total
            }

    def calculate_takehome(self, gross_annual, housing_allowance=0):
        """
        手取り額を計算（社会保険料の詳細計算対応）

        Args:
            gross_annual: 年間総支給額
            housing_allowance: 家賃補助（課税対象）

        Returns:
            float: 手取り額
        """
        taxable_income = gross_annual + housing_allowance
        monthly_average = taxable_income / 12

        # 社会保険料（詳細計算）
        si_detail = self.calculate_social_insurance_detailed(monthly_average)
        social_insurance = si_detail["total"] * 12

        # 所得税+住民税
        tax_base = taxable_income - social_insurance
        income_tax_rates = self.tax_rates["income_tax_rates"]

        if taxable_income <= 5500000:
            tax_rate = income_tax_rates["0-5500000"]
        elif taxable_income <= 8000000:
            tax_rate = income_tax_rates["5500001-8000000"]
        elif taxable_income <= 10000000:
            tax_rate = income_tax_rates["8000001-10000000"]
        else:
            tax_rate = income_tax_rates["10000001-99999999"]

        income_tax = tax_base * tax_rate

        return taxable_income - social_insurance - income_tax

    def get_salary_for_age(self, age):
        """
        年齢に対応する月給とボーナス月数を取得

        Args:
            age: 年齢

        Returns:
            tuple: (月給, ボーナス月数)
        """
        # 年齢に最も近い設定を探す
        ages = sorted([int(a) for a in self.income_progression.keys()])
        applicable_age = ages[0]

        for a in ages:
            if age >= a:
                applicable_age = a
            else:
                break

        salary_data = self.income_progression[str(applicable_age)]
        return salary_data["base_salary"], salary_data["bonus_months"]

    def get_spouse_income_for_age(self, age):
        """
        年齢に対応する配偶者収入を取得

        Args:
            age: 年齢

        Returns:
            float: 月収
        """
        marriage_age = self.basic_info["marriage_age"]
        if age < marriage_age:
            return 0

        spouse_income = self.loader.get_spouse_income()

        if age < 48:
            return spouse_income.get("28-47", 0)
        elif age < 65:
            return spouse_income.get("48-64", 0)
        else:
            return spouse_income.get("65-99", 0)

    def calculate_pension_amount_detailed(self, start_age=65):
        """
        年金額の精密計算（繰上げ/繰下げ対応）

        Args:
            start_age: 年金受給開始年齢

        Returns:
            tuple: (本人月額, 配偶者月額)
        """
        pension = self.loader.get_pension()
        base_amount = pension.get("monthly_amount", 180000)
        base_start_age = 65
        spouse_amount = pension.get("spouse_monthly_amount", 100000)

        # 繰上げ/繰下げ計算
        if "deferral_options" in pension and pension["deferral_options"].get("enabled", False):
            monthly_rate = pension["deferral_options"]["monthly_rate"]
            months_diff = (start_age - base_start_age) * 12

            if start_age < base_start_age:
                # 繰上げ（減額率: 0.4%/月）
                reduction_rate = 0.004
                adjustment = 1 - (abs(months_diff) * reduction_rate)
            elif start_age > base_start_age:
                # 繰下げ（増額率: 0.7%/月）
                adjustment = 1 + (months_diff * monthly_rate)
            else:
                adjustment = 1.0

            adjusted_amount = base_amount * adjustment
            adjusted_spouse = spouse_amount * adjustment
        else:
            adjusted_amount = base_amount
            adjusted_spouse = spouse_amount

        return adjusted_amount, adjusted_spouse

    def get_pension_for_age(self, age, start_age=None):
        """
        年齢に対応する年金収入を取得（繰上げ/繰下げ対応）

        Args:
            age: 現在の年齢
            start_age: 年金受給開始年齢（Noneの場合はデフォルト）

        Returns:
            float: 月額年金
        """
        pension = self.loader.get_pension()

        if start_age is None:
            start_age = pension.get("start_age", 65)

        if age >= start_age:
            amount, _ = self.calculate_pension_amount_detailed(start_age)
            return amount
        return 0

    def get_spouse_pension_for_age(self, age, start_age=None):
        """
        配偶者の年金を取得

        Args:
            age: 現在の年齢
            start_age: 年金受給開始年齢

        Returns:
            float: 配偶者の月額年金
        """
        pension = self.loader.get_pension()

        if start_age is None:
            start_age = pension.get("start_age", 65)

        # 配偶者は通常65歳から
        if age >= start_age:
            _, spouse_amount = self.calculate_pension_amount_detailed(start_age)
            return spouse_amount
        return 0

    def get_housing_allowance_for_age(self, age):
        """
        年齢に対応する家賃補助を取得

        Args:
            age: 年齢

        Returns:
            float: 月額家賃補助
        """
        housing_allowance = self.loader.get_housing_allowance()

        if 45 <= age <= 49:
            return housing_allowance.get("45-49", 0)
        return 0

    def get_housing_costs_for_age(self, age):
        """
        年齢に対応する住居費を取得

        Args:
            age: 年齢

        Returns:
            dict: 住居費内訳
        """
        housing_costs = self.loader.get_housing_costs()

        if age <= 27:
            return housing_costs.get("25-27", {})
        elif age <= 49:
            return housing_costs.get("28-49", {})
        else:
            return housing_costs.get("50-55", {})

    def get_phase_for_age(self, age):
        """
        年齢に対応するフェーズを取得

        Args:
            age: 年齢

        Returns:
            dict: フェーズ定義
        """
        phase_definitions = self.loader.get_phase_definitions()

        for phase_name, phase_data in phase_definitions.items():
            age_range = phase_data["ages"]
            start, end = map(int, age_range.split("-"))

            if start <= age <= end:
                return phase_data

        return None

    def calculate_child_allowance(self, age):
        """
        児童手当を計算

        Args:
            age: 現在の年齢

        Returns:
            float: 月額児童手当
        """
        first_child_birth = self.basic_info["first_child_birth_age"]
        second_child_birth = self.basic_info["second_child_birth_age"]
        child_allowance = self.loader.get_child_allowance()

        total_allowance = 0

        # 第一子
        if age >= first_child_birth:
            child1_age = age - first_child_birth
            if child1_age <= 2:
                total_allowance += child_allowance["age_0_2"]
            elif child1_age <= 14:
                total_allowance += child_allowance["age_3_14"]

        # 第二子
        if age >= second_child_birth:
            child2_age = age - second_child_birth
            if child2_age <= 2:
                total_allowance += child_allowance["age_3_14_second_child"]
            elif child2_age <= 14:
                total_allowance += child_allowance["age_3_14"]

        return total_allowance

    def calculate_investment_growth(self, principal, monthly_contribution, months, annual_return):
        """
        投資の成長を計算（月次複利）

        Args:
            principal: 初期投資額
            monthly_contribution: 月次積立額
            months: 運用月数
            annual_return: 年利

        Returns:
            float: 将来価値
        """
        monthly_rate = annual_return / 12

        if monthly_rate == 0:
            return principal + monthly_contribution * months

        # 元本の成長
        future_principal = principal * ((1 + monthly_rate) ** months)

        # 積立分の成長
        if monthly_contribution > 0:
            future_contribution = monthly_contribution * (((1 + monthly_rate) ** months - 1) / monthly_rate)
        else:
            future_contribution = 0

        return future_principal + future_contribution

    def apply_inflation(self, base_amount, years, rate):
        """
        インフレ調整を適用

        Args:
            base_amount: 基準額
            years: 経過年数
            rate: インフレ率

        Returns:
            int: インフレ調整後の金額（円単位で四捨五入）
        """
        if not self.inflation_settings.get("enabled", False):
            return base_amount

        adjusted = base_amount * ((1 + rate) ** years)
        return round(adjusted)

    def calculate_retirement_benefit_tax(self, lump_sum, years_of_service):
        """
        退職所得控除と税額を計算

        Args:
            lump_sum: 退職金一時金
            years_of_service: 勤続年数

        Returns:
            dict: 控除額、課税対象額、税額
        """
        # 退職所得控除の計算
        if years_of_service <= 20:
            deduction = 400000 * years_of_service
        else:
            deduction = 8000000 + 700000 * (years_of_service - 20)

        # 課税退職所得金額（控除後の1/2）
        taxable_amount = max(0, (lump_sum - deduction) / 2)

        # 税額計算（所得税+住民税、簡易計算）
        if taxable_amount <= 1950000:
            tax = taxable_amount * 0.05
        elif taxable_amount <= 3300000:
            tax = taxable_amount * 0.1 - 97500
        elif taxable_amount <= 6950000:
            tax = taxable_amount * 0.2 - 427500
        elif taxable_amount <= 9000000:
            tax = taxable_amount * 0.23 - 636000
        elif taxable_amount <= 18000000:
            tax = taxable_amount * 0.33 - 1536000
        else:
            tax = taxable_amount * 0.4 - 2796000

        # 住民税10%を加算
        total_tax = tax + taxable_amount * 0.1

        return {
            "deduction": deduction,
            "taxable_amount": taxable_amount,
            "tax": total_tax,
            "net_amount": lump_sum - total_tax
        }

    def get_retirement_benefit(self, age):
        """
        退職金を取得

        Args:
            age: 年齢

        Returns:
            dict: 退職金情報（一時金、企業年金）
        """
        retirement_benefit = self.loader.plan_data.get("retirement_benefit", {})

        if not retirement_benefit.get("enabled", False):
            return {"lump_sum_net": 0, "corporate_pension": 0}

        # 65歳でのみ一時金を支給
        if age == 65:
            lump_sum = retirement_benefit.get("lump_sum", 0)
            years_of_service = retirement_benefit.get("tax_deduction", {}).get("years_of_service", 38)

            # 税金計算
            tax_info = self.calculate_retirement_benefit_tax(lump_sum, years_of_service)

            return {
                "lump_sum_gross": lump_sum,
                "lump_sum_net": tax_info["net_amount"],
                "lump_sum_tax": tax_info["tax"],
                "corporate_pension": 0
            }

        # 企業年金（月額）
        corporate_pension = retirement_benefit.get("corporate_pension", {})
        if corporate_pension.get("enabled", False):
            start_age = corporate_pension.get("start_age", 65)
            end_age = start_age + corporate_pension.get("years", 10)
            monthly_amount = corporate_pension.get("monthly_amount", 0)

            if start_age <= age < end_age:
                return {
                    "lump_sum_net": 0,
                    "corporate_pension": monthly_amount
                }

        return {"lump_sum_net": 0, "corporate_pension": 0}

    def get_custom_events(self):
        """
        カスタム大きな買い物イベント一覧を取得

        Returns:
            list: イベントのリスト
        """
        custom_events = self.loader.plan_data.get("custom_large_purchase_events", {})

        if not custom_events.get("enabled", False):
            return []

        return custom_events.get("events", [])

    def get_active_custom_events(self):
        """
        有効なカスタムイベントのみ取得

        Returns:
            list: 有効なイベントのリスト
        """
        all_events = self.get_custom_events()
        return [event for event in all_events if event.get("enabled", False)]

    def get_custom_events_for_age(self, age):
        """
        特定年齢で発生するイベントを取得

        Args:
            age: 年齢

        Returns:
            list: その年齢で発生するイベントのリスト
        """
        active_events = self.get_active_custom_events()
        return [event for event in active_events if event.get("age") == age]

    def get_custom_event_saving_for_age(self, age):
        """
        特定年齢での各イベント用積立額を取得

        Args:
            age: 年齢

        Returns:
            dict: {event_id: monthly_amount} の辞書
        """
        active_events = self.get_active_custom_events()
        savings = {}

        for event in active_events:
            auto_saving = event.get("auto_saving", {})
            if not auto_saving.get("enabled", False):
                continue

            start_age = auto_saving.get("start_age", event["age"] - 5)
            end_age = event.get("age")

            # 積立期間中なら
            if start_age <= age < end_age:
                monthly_amount = auto_saving.get("monthly_amount", 0)
                savings[event["id"]] = monthly_amount

        return savings

    def calculate_monthly_data(self, age, month, assets_previous_month):
        """
        月次データを計算

        Args:
            age: 年齢
            month: 月（1-12）
            assets_previous_month: 前月末の資産状況

        Returns:
            dict: 月次データ
        """
        years_from_start = age - self.basic_info["start_age"]
        is_bonus_month = month in [6, 12]

        # 収入計算
        base_salary, bonus_months = self.get_salary_for_age(age)
        annual_salary = base_salary * (12 + bonus_months)
        housing_allowance_monthly = self.get_housing_allowance_for_age(age)
        housing_allowance_annual = housing_allowance_monthly * 12

        # 手取り計算
        net_annual = self.calculate_takehome(annual_salary, housing_allowance_annual)
        monthly_net_salary = net_annual / 12

        # ボーナス（年2回に分けて支給）
        if is_bonus_month:
            bonus_gross = (base_salary * bonus_months) / 2
            bonus_net = self.calculate_takehome(bonus_gross, 0)
        else:
            bonus_net = 0

        # 配偶者収入
        spouse_income = self.get_spouse_income_for_age(age)

        # 年金収入
        pension_income = self.get_pension_for_age(age)

        # 児童手当
        child_allowance = self.calculate_child_allowance(age)

        # 総収入
        total_income = monthly_net_salary + bonus_net + spouse_income + pension_income + child_allowance

        # 支出計算
        phase = self.get_phase_for_age(age)
        housing_costs = self.get_housing_costs_for_age(age)

        # 住居費
        rent = housing_costs.get("rent", 0)
        mortgage = housing_costs.get("mortgage", 0)
        utilities = housing_costs.get("utilities", 0)

        # 生活費（インフレ調整）
        monthly_expenses = {}
        if phase:
            for expense_key, expense_value in phase["monthly_expenses"].items():
                inflation_rate = self.inflation_settings.get("living_expenses_rate", 0)
                adjusted_expense = self.apply_inflation(expense_value, years_from_start, inflation_rate)
                monthly_expenses[expense_key] = adjusted_expense

        total_monthly_expenses = sum(monthly_expenses.values()) + rent + mortgage + utilities

        # 投資
        monthly_investment = {}
        if phase:
            for inv_key, inv_value in phase.get("monthly_investment", {}).items():
                monthly_investment[inv_key] = inv_value

        total_monthly_investment = sum(monthly_investment.values())

        # ボーナス配分
        bonus_allocation = {}
        if is_bonus_month and phase:
            for bonus_key, bonus_value in phase.get("bonus_allocation", {}).items():
                # ボーナスは年2回なので半分ずつ
                bonus_allocation[bonus_key] = bonus_value / 2

        total_bonus_allocation = sum(bonus_allocation.values())

        # 月間収支
        monthly_cashflow = total_income - total_monthly_expenses - total_monthly_investment - total_bonus_allocation

        # 資産計算（簡略版 - 詳細は年次計算で実施）
        nisa_contribution = monthly_investment.get("nisa_tsumitate", 0)
        company_stock_contribution = monthly_investment.get("company_stock", 0)

        return {
            "age": age,
            "month": month,
            "year": 2025 + years_from_start,
            "income": {
                "salary_net": monthly_net_salary,
                "bonus_net": bonus_net,
                "spouse_income": spouse_income,
                "pension": pension_income,
                "child_allowance": child_allowance,
                "housing_allowance": housing_allowance_monthly if housing_allowance_monthly > 0 else 0,
                "total": total_income
            },
            "expenses": {
                "housing_rent": rent,
                "housing_mortgage": mortgage,
                "housing_utilities": utilities,
                **monthly_expenses,
                "total": total_monthly_expenses
            },
            "investment": {
                **monthly_investment,
                **bonus_allocation,
                "total": total_monthly_investment + total_bonus_allocation
            },
            "cashflow": {
                "monthly": monthly_cashflow,
            },
            "assets": {
                "nisa_balance": assets_previous_month.get("nisa_balance", 0),
                "company_stock_balance": assets_previous_month.get("company_stock_balance", 0),
                "cash_balance": assets_previous_month.get("cash_balance", 0),
                "total": assets_previous_month.get("total", 0)
            }
        }

    def simulate_30_years(self):
        """
        30年間のシミュレーションを実行

        Returns:
            tuple: (月次データリスト, 年次データリスト)
        """
        start_age = self.basic_info["start_age"]
        end_age = self.basic_info["end_age"]
        birth_month = self.basic_info["birth_month"]

        monthly_data = []
        yearly_summary = []

        # 初期資産
        assets = {
            "nisa_tsumitate_balance": 0,
            "nisa_growth_balance": 0,
            "company_stock_balance": 0,
            "company_stock_shares": 0,
            "education_fund_balance": 0,
            "marriage_fund_balance": 0,
            "taxable_account_balance": 0,
            "cash_balance": 0,
            "total": 0
        }

        # カスタムイベント用の資産枠を動的に追加
        active_events = self.get_active_custom_events()
        for event in active_events:
            fund_key = f"custom_event_{event['id']}_fund"
            assets[fund_key] = 0

        nisa_tsumitate_total_contribution = 0
        nisa_growth_total_contribution = 0

        # 自社株情報
        company_stock_settings = self.investment_settings["company_stock"]
        stock_price = company_stock_settings["initial_price"]
        stock_growth_rate = company_stock_settings["price_growth_rate"]
        dividend_yield = company_stock_settings["dividend_yield"]
        incentive_rate = company_stock_settings["incentive_rate"]

        # 年齢ごとにループ
        for age in range(start_age, end_age + 1):
            year_start_assets = assets.copy()
            yearly_income = 0
            yearly_expenses = 0
            yearly_investment = 0
            yearly_cashflow = 0

            # 各月をシミュレート
            for month in range(1, 13):
                month_data = self.calculate_monthly_data(age, month, assets)
                monthly_data.append(month_data)

                # 年間集計
                yearly_income += month_data["income"]["total"]
                yearly_expenses += month_data["expenses"]["total"]
                yearly_investment += month_data["investment"]["total"]
                yearly_cashflow += month_data["cashflow"]["monthly"]

                # 資産更新
                # NISA積立
                nisa_contribution = month_data["investment"].get("nisa_tsumitate", 0)
                if nisa_contribution > 0:
                    if nisa_tsumitate_total_contribution < self.investment_settings["nisa"]["tsumitate_limit"]:
                        contribution = min(nisa_contribution,
                                         self.investment_settings["nisa"]["tsumitate_limit"] - nisa_tsumitate_total_contribution)
                        nisa_tsumitate_total_contribution += contribution
                        # 月次で運用益を加算（簡易計算）
                        monthly_return = self.investment_settings["nisa"]["expected_return"] / 12
                        assets["nisa_tsumitate_balance"] = (assets["nisa_tsumitate_balance"] + contribution) * (1 + monthly_return)
                    else:
                        # つみたてNISA満額後は特定口座に投資
                        monthly_return = self.investment_settings["taxable_account"]["expected_return"] / 12
                        assets["taxable_account_balance"] = (assets["taxable_account_balance"] + nisa_contribution) * (1 + monthly_return)

                # NISA成長投資枠（ボーナス月のみ）
                nisa_growth_contribution = month_data["investment"].get("nisa_growth", 0)
                if nisa_growth_contribution > 0:
                    if nisa_growth_total_contribution < self.investment_settings["nisa"]["growth_limit"]:
                        contribution = min(nisa_growth_contribution,
                                         self.investment_settings["nisa"]["growth_limit"] - nisa_growth_total_contribution)
                        nisa_growth_total_contribution += contribution
                        monthly_return = self.investment_settings["nisa"]["expected_return"] / 12
                        assets["nisa_growth_balance"] = (assets["nisa_growth_balance"] + contribution) * (1 + monthly_return)
                    else:
                        # NISA満額後は特定口座に投資
                        monthly_return = self.investment_settings["taxable_account"]["expected_return"] / 12
                        assets["taxable_account_balance"] = (assets["taxable_account_balance"] + nisa_growth_contribution) * (1 + monthly_return)

                # 自社株購入
                company_stock_contribution = month_data["investment"].get("company_stock", 0)
                if company_stock_contribution > 0:
                    # 奨励金込み
                    actual_purchase = company_stock_contribution * (1 + incentive_rate)
                    shares_purchased = actual_purchase / stock_price
                    assets["company_stock_shares"] += shares_purchased

                # 教育資金積立
                education_contribution = month_data["investment"].get("education_fund", 0)
                if education_contribution > 0:
                    monthly_return = self.investment_settings["education_fund"]["expected_return"] / 12
                    assets["education_fund_balance"] = (assets["education_fund_balance"] + education_contribution) * (1 + monthly_return)

                # 結婚資金積立
                marriage_contribution = month_data["investment"].get("marriage_fund", 0)
                if marriage_contribution > 0:
                    monthly_return = self.investment_settings["education_fund"]["expected_return"] / 12
                    assets["marriage_fund_balance"] = (assets["marriage_fund_balance"] + marriage_contribution) * (1 + monthly_return)

                # 子供準備資金積立（28-29歳）- 現金として積立
                child_prep_contribution = month_data["investment"].get("child_preparation_fund", 0)
                if child_prep_contribution > 0:
                    # 子供準備資金は現金として積み立て
                    assets["cash_balance"] += child_prep_contribution

                # 緊急予備費積立 - 現金として積立
                emergency_contribution = month_data["investment"].get("emergency_fund", 0)
                if emergency_contribution > 0:
                    assets["cash_balance"] += emergency_contribution

                # 高配当株投資（特定口座）
                high_dividend_contribution = month_data["investment"].get("high_dividend_stocks", 0)
                if high_dividend_contribution > 0:
                    monthly_return = self.investment_settings["taxable_account"]["expected_return"] / 12
                    assets["taxable_account_balance"] = (assets["taxable_account_balance"] + high_dividend_contribution) * (1 + monthly_return)

                # カスタムイベント用の積立
                event_savings = self.get_custom_event_saving_for_age(age)
                for event_id, monthly_amount in event_savings.items():
                    fund_key = f"custom_event_{event_id}_fund"
                    if fund_key in assets:
                        # 現金から積立（利息なし）
                        assets[fund_key] += monthly_amount
                        # 積立額は支出として扱う（キャッシュフローから差し引かれる）

                # 現金残高更新
                assets["cash_balance"] += month_data["cashflow"]["monthly"]
                # カスタムイベント積立分を現金から差し引く
                total_event_saving = sum(event_savings.values())
                assets["cash_balance"] -= total_event_saving

            # 年末処理
            # イレギュラー支出を記録するリスト
            irregular_expenses = []

            # 教育費の計算（0-18歳）
            education_costs = self.loader.get_education_costs()
            annual_education_cost = 0

            # 第一子の教育費
            first_child_age = age - self.basic_info["first_child_birth_age"]
            if 0 <= first_child_age <= 22:
                if 0 <= first_child_age <= 5:
                    # 保育園費用（年額）
                    annual_education_cost += education_costs.get("age_0_5", {}).get("childcare", 0)
                elif 6 <= first_child_age <= 11:
                    # 小学校費用（年額）
                    annual_education_cost += education_costs.get("age_6_11", {}).get("school_fees", 0)
                    annual_education_cost += education_costs.get("age_6_11", {}).get("lessons", 0)
                elif 12 <= first_child_age <= 14:
                    # 中学校費用（年額）
                    annual_education_cost += education_costs.get("age_12_14", {}).get("school_fees", 0)
                    annual_education_cost += education_costs.get("age_12_14", {}).get("cram_school", 0)
                elif 15 <= first_child_age <= 17:
                    # 高校費用（年額）
                    annual_education_cost += education_costs.get("age_15_17", {}).get("school_fees", 0)
                    annual_education_cost += education_costs.get("age_15_17", {}).get("cram_school", 0)
                    # 高校無償化補助を差し引き
                    annual_education_cost -= self.loader.get_high_school_subsidy()
                elif first_child_age == 18:
                    # 受験費用（年額）
                    annual_education_cost += education_costs.get("age_18", {}).get("exam_fees", 0)

            # 第二子の教育費
            second_child_age = age - self.basic_info["second_child_birth_age"]
            if 0 <= second_child_age <= 22:
                if 0 <= second_child_age <= 5:
                    annual_education_cost += education_costs.get("age_0_5", {}).get("childcare", 0)
                elif 6 <= second_child_age <= 11:
                    annual_education_cost += education_costs.get("age_6_11", {}).get("school_fees", 0)
                    annual_education_cost += education_costs.get("age_6_11", {}).get("lessons", 0)
                elif 12 <= second_child_age <= 14:
                    annual_education_cost += education_costs.get("age_12_14", {}).get("school_fees", 0)
                    annual_education_cost += education_costs.get("age_12_14", {}).get("cram_school", 0)
                elif 15 <= second_child_age <= 17:
                    annual_education_cost += education_costs.get("age_15_17", {}).get("school_fees", 0)
                    annual_education_cost += education_costs.get("age_15_17", {}).get("cram_school", 0)
                    annual_education_cost -= self.loader.get_high_school_subsidy()
                elif second_child_age == 18:
                    annual_education_cost += education_costs.get("age_18", {}).get("exam_fees", 0)

            # 教育費を現金から支払い（インフレ調整）
            adjusted_cost = 0
            if annual_education_cost > 0:
                inflation_rate = self.inflation_settings.get("education_rate", 0)
                adjusted_cost = self.apply_inflation(annual_education_cost, age - start_age, inflation_rate)
                assets["cash_balance"] -= adjusted_cost

            # カスタムイベントの購入処理
            events_this_year = self.get_custom_events_for_age(age)
            for event in events_this_year:
                event_id = event["id"]
                event_amount = event["amount"]
                fund_key = f"custom_event_{event_id}_fund"

                payment_sources = []

                # 専用貯金の残高を確認
                fund_balance = assets.get(fund_key, 0)

                if fund_balance >= event_amount:
                    # 専用資金で全額支払い
                    assets[fund_key] -= event_amount
                    payment_sources.append({
                        "source": f"{event['name']}用貯金",
                        "amount": event_amount
                    })
                else:
                    # 不足分は現金から補填
                    shortfall = event_amount - fund_balance

                    if fund_balance > 0:
                        # 貯金を使い切る
                        assets[fund_key] = 0
                        payment_sources.append({
                            "source": f"{event['name']}用貯金",
                            "amount": fund_balance
                        })

                    # 不足分を現金から支払い
                    assets["cash_balance"] -= shortfall
                    payment_sources.append({
                        "source": "現金",
                        "amount": shortfall
                    })

                # イレギュラー支出として記録
                irregular_expenses.append({
                    "type": event["name"],
                    "amount": event_amount,
                    "payment_sources": payment_sources,
                    "category": event.get("category", "other"),
                    "description": event.get("description", "")
                })

            # 自社株の株価更新
            stock_price = stock_price * (1 + stock_growth_rate)
            assets["company_stock_balance"] = assets["company_stock_shares"] * stock_price

            # 配当金（年2回を年末に一括計算）
            annual_dividend_total = 0
            annual_dividend_received = 0
            if assets["company_stock_balance"] > 0:
                annual_dividend = assets["company_stock_balance"] * dividend_yield
                annual_dividend_total = annual_dividend

                # 配当金の再投資判定
                if age <= 45:
                    reinvest_rate = self.investment_settings["dividend_reinvestment"]["age_0_45"]
                elif age <= 55:
                    reinvest_rate = self.investment_settings["dividend_reinvestment"]["age_46_55"]
                elif age <= 64:
                    reinvest_rate = self.investment_settings["dividend_reinvestment"]["age_56_64"]
                else:
                    reinvest_rate = self.investment_settings["dividend_reinvestment"]["age_65_99"]

                reinvest_amount = annual_dividend * reinvest_rate
                cash_dividend = annual_dividend - reinvest_amount
                annual_dividend_received = cash_dividend

                # 再投資（自社株追加購入）
                if reinvest_amount > 0:
                    shares_purchased = reinvest_amount / stock_price
                    assets["company_stock_shares"] += shares_purchased
                    assets["company_stock_balance"] = assets["company_stock_shares"] * stock_price

                # 現金配当
                assets["cash_balance"] += cash_dividend

            # ライフイベント支出
            if age == self.life_events["marriage"]["age"]:
                # 結婚式費用を結婚資金から支払い
                marriage_cost = self.life_events["marriage"]["cost"]
                payment_sources = []

                if assets["marriage_fund_balance"] >= marriage_cost:
                    assets["marriage_fund_balance"] -= marriage_cost
                    payment_sources.append({"source": "結婚資金", "amount": marriage_cost})
                else:
                    # 結婚資金が不足している場合は現金から
                    marriage_fund_used = assets["marriage_fund_balance"]
                    shortfall = marriage_cost - assets["marriage_fund_balance"]
                    assets["marriage_fund_balance"] = 0
                    assets["cash_balance"] -= shortfall

                    if marriage_fund_used > 0:
                        payment_sources.append({"source": "結婚資金", "amount": marriage_fund_used})
                    payment_sources.append({"source": "現金", "amount": shortfall})

                irregular_expenses.append({
                    "type": "結婚式・新婚旅行",
                    "amount": marriage_cost,
                    "payment_sources": payment_sources
                })

            if age == self.life_events["home_purchase"]["age"]:
                # 頭金 + 諸費用
                down_payment = self.life_events["home_purchase"]["down_payment"]
                closing_costs = self.life_events["home_purchase"]["closing_costs"]
                total_upfront = down_payment + closing_costs
                payment_sources = []

                # 現金から支払い、不足分は教育資金から
                if assets["cash_balance"] >= total_upfront:
                    assets["cash_balance"] -= total_upfront
                    payment_sources.append({"source": "現金", "amount": total_upfront})
                else:
                    cash_used = assets["cash_balance"]
                    shortfall = total_upfront - assets["cash_balance"]
                    assets["cash_balance"] = 0

                    if cash_used > 0:
                        payment_sources.append({"source": "現金", "amount": cash_used})

                    # 教育資金から不足分を補填
                    if assets["education_fund_balance"] >= shortfall:
                        assets["education_fund_balance"] -= shortfall
                        payment_sources.append({"source": "教育資金", "amount": shortfall})
                    else:
                        # 教育資金も不足の場合、残りをNISA成長投資枠から
                        education_fund_used = assets["education_fund_balance"]
                        remaining_shortfall = shortfall - assets["education_fund_balance"]
                        assets["education_fund_balance"] = 0

                        if education_fund_used > 0:
                            payment_sources.append({"source": "教育資金", "amount": education_fund_used})

                        if assets["nisa_growth_balance"] >= remaining_shortfall:
                            assets["nisa_growth_balance"] -= remaining_shortfall
                            payment_sources.append({"source": "NISA成長", "amount": remaining_shortfall})
                        else:
                            nisa_used = assets["nisa_growth_balance"]
                            assets["nisa_growth_balance"] = max(0, assets["nisa_growth_balance"] - remaining_shortfall)
                            if nisa_used > 0:
                                payment_sources.append({"source": "NISA成長", "amount": nisa_used})

                irregular_expenses.append({
                    "type": "住宅購入（頭金）",
                    "amount": down_payment,
                    "payment_sources": payment_sources[:len(payment_sources)//2] if len(payment_sources) > 1 else payment_sources
                })
                irregular_expenses.append({
                    "type": "住宅購入（諸費用）",
                    "amount": closing_costs,
                    "payment_sources": payment_sources[len(payment_sources)//2:] if len(payment_sources) > 1 else []
                })

            # 大学費用の支払い
            first_child_age = age - self.basic_info["first_child_birth_age"]
            second_child_age = age - self.basic_info["second_child_birth_age"]

            university_cost_this_year = 0
            university_details = []

            # 第一子の大学費用（19-22歳）
            if 19 <= first_child_age <= 22:
                # 年間学費 + 生活費
                annual_tuition = 5500000 / 4  # 4年間で550万円
                annual_living = 4560000 / 4   # 4年間で456万円
                child1_cost = annual_tuition + annual_living
                university_cost_this_year += child1_cost
                university_details.append({
                    "child": "第一子",
                    "age": first_child_age,
                    "amount": child1_cost
                })

            # 第二子の大学費用（19-22歳）
            if 19 <= second_child_age <= 22:
                annual_tuition = 5500000 / 4
                annual_living = 4560000 / 4
                child2_cost = annual_tuition + annual_living
                university_cost_this_year += child2_cost
                university_details.append({
                    "child": "第二子",
                    "age": second_child_age,
                    "amount": child2_cost
                })

            # 大学費用も教育費として記録（adjusted_costに加算）
            adjusted_cost += university_cost_this_year

            # 大学費用を教育資金から支払い
            if university_cost_this_year > 0:
                payment_sources = []

                if assets["education_fund_balance"] >= university_cost_this_year:
                    assets["education_fund_balance"] -= university_cost_this_year
                    payment_sources.append({"source": "教育資金", "amount": university_cost_this_year})
                else:
                    # 教育資金が不足している場合は現金から
                    education_fund_used = assets["education_fund_balance"]
                    shortfall = university_cost_this_year - assets["education_fund_balance"]
                    assets["education_fund_balance"] = 0
                    assets["cash_balance"] -= shortfall

                    if education_fund_used > 0:
                        payment_sources.append({"source": "教育資金", "amount": education_fund_used})
                    payment_sources.append({"source": "現金", "amount": shortfall})

                # イレギュラー支出として記録
                for detail in university_details:
                    irregular_expenses.append({
                        "type": f"大学費用（{detail['child']} {detail['age']}歳）",
                        "amount": detail["amount"],
                        "payment_sources": [
                            {
                                "source": ps["source"],
                                "amount": ps["amount"] * (detail["amount"] / university_cost_this_year)
                            }
                            for ps in payment_sources
                        ]
                    })

            # 退職金の処理
            retirement_benefit = self.get_retirement_benefit(age)
            retirement_lump_sum = 0
            retirement_pension = 0

            if retirement_benefit["lump_sum_net"] > 0:
                # 65歳で退職金一時金を受領
                retirement_lump_sum = retirement_benefit["lump_sum_net"]
                assets["cash_balance"] += retirement_lump_sum
                irregular_expenses.append({
                    "type": "退職金（一時金・税引後）",
                    "amount": -retirement_lump_sum,  # マイナスは収入
                    "payment_sources": [{"source": "退職金", "amount": retirement_lump_sum}]
                })

            if retirement_benefit["corporate_pension"] > 0:
                # 企業年金を年額で計算
                retirement_pension = retirement_benefit["corporate_pension"] * 12
                assets["cash_balance"] += retirement_pension

            # 総資産
            total_custom_event_funds = sum(
                assets.get(f"custom_event_{event['id']}_fund", 0)
                for event in self.get_active_custom_events()
            )
            assets["total"] = (assets["nisa_tsumitate_balance"] +
                             assets["nisa_growth_balance"] +
                             assets["company_stock_balance"] +
                             assets["education_fund_balance"] +
                             assets["marriage_fund_balance"] +
                             assets["taxable_account_balance"] +
                             assets["cash_balance"] +
                             total_custom_event_funds)

            # カスタムイベント資金の記録
            custom_event_funds = {}
            for event in self.get_active_custom_events():
                fund_key = f"custom_event_{event['id']}_fund"
                custom_event_funds[event['id']] = {
                    "name": event['name'],
                    "balance": assets.get(fund_key, 0),
                    "target_amount": event['amount'],
                    "target_age": event['age']
                }

            # 年次サマリー
            yearly_summary.append({
                "age": age,
                "year": 2025 + (age - start_age),
                "income_total": yearly_income,
                "expenses_total": yearly_expenses,
                "investment_total": yearly_investment,
                "cashflow_annual": yearly_cashflow,
                "assets_start": year_start_assets["total"],
                "assets_end": assets["total"],
                "nisa_tsumitate": assets["nisa_tsumitate_balance"],
                "nisa_growth": assets["nisa_growth_balance"],
                "company_stock": assets["company_stock_balance"],
                "education_fund": assets["education_fund_balance"],
                "taxable_account": assets["taxable_account_balance"],
                "cash": assets["cash_balance"],
                "custom_event_funds": custom_event_funds,
                "education_cost_annual": adjusted_cost,
                "dividend_total": annual_dividend_total,
                "dividend_received": annual_dividend_received,
                "irregular_expenses": irregular_expenses
            })

        self.monthly_data = monthly_data
        self.yearly_data = yearly_summary

        return monthly_data, yearly_summary

    def get_age_detail(self, age):
        """
        特定年齢の12ヶ月分詳細データを取得

        Args:
            age: 年齢

        Returns:
            list: 12ヶ月分のデータ
        """
        return [m for m in self.monthly_data if m["age"] == age]

    def get_age_assets_detail(self, age):
        """
        特定年齢の資産詳細情報を取得

        Args:
            age: 年齢

        Returns:
            dict: 資産詳細情報
        """
        if not self.yearly_data:
            return {}

        # 指定年齢の年次データを取得
        year_data = None
        prev_year_data = None
        for i, y in enumerate(self.yearly_data):
            if y["age"] == age:
                year_data = y
                if i > 0:
                    prev_year_data = self.yearly_data[i - 1]
                break

        if not year_data:
            return {}

        # 年始の資産（前年末 = 今年の年始）
        assets_start = {
            "nisa_tsumitate": prev_year_data["nisa_tsumitate"] if prev_year_data else 0,
            "nisa_growth": prev_year_data["nisa_growth"] if prev_year_data else 0,
            "company_stock": prev_year_data["company_stock"] if prev_year_data else 0,
            "education_fund": prev_year_data["education_fund"] if prev_year_data else 0,
            "taxable_account": prev_year_data["taxable_account"] if prev_year_data else 0,
            "cash": prev_year_data["cash"] if prev_year_data else 0,
            "total": prev_year_data["assets_end"] if prev_year_data else 0
        }

        # 年末の資産
        assets_end = {
            "nisa_tsumitate": year_data["nisa_tsumitate"],
            "nisa_growth": year_data["nisa_growth"],
            "company_stock": year_data["company_stock"],
            "education_fund": year_data["education_fund"],
            "taxable_account": year_data["taxable_account"],
            "cash": year_data["cash"],
            "total": year_data["assets_end"]
        }

        # 配当金予想
        dividend_info = {
            "company_stock_dividend": year_data["company_stock"] * self.investment_settings["company_stock"]["dividend_yield"],
            "taxable_dividend": year_data["taxable_account"] * self.investment_settings["taxable_account"]["dividend_yield"],
            "total_dividend_pretax": year_data.get("dividend_total", 0),
            "total_dividend_received": year_data.get("dividend_received", 0)
        }

        # 配当利回り
        dividend_assets = year_data["company_stock"] + year_data["taxable_account"]
        dividend_info["dividend_yield"] = (dividend_info["total_dividend_pretax"] / dividend_assets * 100) if dividend_assets > 0 else 0

        # 教育費
        education_cost = year_data.get("education_cost_annual", 0)

        # イレギュラー支出
        irregular_expenses = year_data.get("irregular_expenses", [])

        return {
            "age": age,
            "year": year_data["year"],
            "assets_start": assets_start,
            "assets_end": assets_end,
            "income_total": year_data["income_total"],
            "expenses_total": year_data["expenses_total"],
            "investment_total": year_data["investment_total"],
            "cashflow_annual": year_data["cashflow_annual"],
            "education_cost": education_cost,
            "dividend_info": dividend_info,
            "irregular_expenses": irregular_expenses
        }

    def get_education_summary(self):
        """
        教育費の詳細サマリーを取得

        Returns:
            dict: 教育費サマリー
        """
        if not self.yearly_data:
            return {}

        first_child_birth = self.basic_info["first_child_birth_age"]
        second_child_birth = self.basic_info["second_child_birth_age"]

        # 子供別の累積教育費を計算
        child1_total = 0
        child2_total = 0
        child_allowance_total = 0

        child1_by_age = []
        child2_by_age = []

        education_costs = self.loader.get_education_costs()

        for year_data in self.yearly_data:
            age = year_data["age"]
            first_child_age = age - first_child_birth
            second_child_age = age - second_child_birth

            # 第一子の教育費（0-18歳）
            if 0 <= first_child_age <= 22:
                annual_cost = year_data.get("education_cost_annual", 0)

                # 大学費用を追加（19-22歳）
                entrance_fee_1 = 0
                annual_tuition_1 = 0
                annual_living_1 = 0
                if 19 <= first_child_age <= 22:
                    # 入学金（初年度のみ）
                    entrance_fee_1 = education_costs.get("age_19_22", {}).get("university_entrance_fee", 0) if first_child_age == 19 else 0
                    # 年間授業料
                    annual_tuition_1 = education_costs.get("age_19_22", {}).get("university_annual_tuition", 0)
                    # 年間生活費
                    annual_living_1 = education_costs.get("age_19_22", {}).get("living_expenses_annual", 0)
                    annual_cost += entrance_fee_1 + annual_tuition_1 + annual_living_1

                # 両方の子供がいる場合は0-18歳の費用を半分ずつ（大学費用は個別）
                if 0 <= second_child_age <= 22 and first_child_age <= 18:
                    child1_cost = year_data.get("education_cost_annual", 0) / 2
                    # 第一子の大学費用を追加
                    if 19 <= first_child_age <= 22:
                        child1_cost += entrance_fee_1 + annual_tuition_1 + annual_living_1
                else:
                    child1_cost = annual_cost

                child1_total += child1_cost

                child1_by_age.append({
                    "child_age": first_child_age,
                    "parent_age": age,
                    "annual_cost": child1_cost,
                    "cumulative_cost": child1_total
                })

            # 第二子の教育費
            if 0 <= second_child_age <= 22:
                annual_cost_2 = year_data.get("education_cost_annual", 0)

                # 大学費用を追加（19-22歳）
                entrance_fee_2 = 0
                annual_tuition_2 = 0
                annual_living_2 = 0
                if 19 <= second_child_age <= 22:
                    # 入学金（初年度のみ）
                    entrance_fee_2 = education_costs.get("age_19_22", {}).get("university_entrance_fee", 0) if second_child_age == 19 else 0
                    # 年間授業料
                    annual_tuition_2 = education_costs.get("age_19_22", {}).get("university_annual_tuition", 0)
                    # 年間生活費
                    annual_living_2 = education_costs.get("age_19_22", {}).get("living_expenses_annual", 0)
                    annual_cost_2 += entrance_fee_2 + annual_tuition_2 + annual_living_2

                # 0-18歳の費用を半分に（大学費用は個別）
                if 0 <= first_child_age <= 22 and second_child_age <= 18:
                    child2_cost = year_data.get("education_cost_annual", 0) / 2
                    # 第二子の大学費用を追加
                    if 19 <= second_child_age <= 22:
                        child2_cost += entrance_fee_2 + annual_tuition_2 + annual_living_2
                else:
                    child2_cost = annual_cost_2

                child2_total += child2_cost

                child2_by_age.append({
                    "child_age": second_child_age,
                    "parent_age": age,
                    "annual_cost": child2_cost,
                    "cumulative_cost": child2_total
                })

        # 児童手当の総額を計算
        child_allowance = self.loader.get_child_allowance()
        for year_data in self.yearly_data:
            age = year_data["age"]
            monthly_allowance = self.calculate_child_allowance(age)
            child_allowance_total += monthly_allowance * 12

        return {
            "child1_total": child1_total,
            "child2_total": child2_total,
            "child_allowance_total": child_allowance_total,
            "net_education_cost": child1_total + child2_total - child_allowance_total,
            "child1_by_age": child1_by_age,
            "child2_by_age": child2_by_age
        }

    def get_dividend_summary(self):
        """
        配当金の詳細サマリーを取得

        Returns:
            dict: 配当金サマリー
        """
        if not self.yearly_data:
            return {}

        last_year = self.yearly_data[-1]

        # 65歳時点の配当資産
        company_stock_balance = last_year["company_stock"]
        taxable_balance = last_year["taxable_account"]
        dividend_assets = company_stock_balance + taxable_balance

        # 年間配当金（税引後）
        company_dividend = company_stock_balance * self.investment_settings["company_stock"]["dividend_yield"]
        taxable_dividend = taxable_balance * self.investment_settings["taxable_account"]["dividend_yield"]
        total_dividend = company_dividend + taxable_dividend

        # 税引後（20.315%の税金）
        dividend_after_tax = total_dividend * (1 - 0.20315)

        # 配当利回り
        dividend_yield = (dividend_after_tax / dividend_assets * 100) if dividend_assets > 0 else 0

        # 年次配当金推移
        dividend_history = []
        for year_data in self.yearly_data:
            dividend_history.append({
                "age": year_data["age"],
                "year": year_data["year"],
                "dividend_total": year_data.get("dividend_total", 0),
                "dividend_received": year_data.get("dividend_received", 0)
            })

        return {
            "dividend_assets": dividend_assets,
            "annual_dividend": dividend_after_tax,
            "monthly_dividend": dividend_after_tax / 12,
            "dividend_yield": dividend_yield,
            "dividend_history": dividend_history
        }

    def simulate_retirement(self, start_assets=None):
        """
        退職後シミュレーション（65-90歳）

        Args:
            start_assets: 開始時の資産（Noneの場合は現役時代の最終資産を使用）

        Returns:
            tuple: (年次データリスト, サマリー)
        """
        if start_assets is None:
            if not self.yearly_data:
                # 現役時代のシミュレーションを先に実行
                self.simulate_30_years()

            # 65歳時点の資産を取得
            last_year = self.yearly_data[-1]
            start_assets = {
                "nisa_tsumitate_balance": last_year["nisa_tsumitate"],
                "nisa_growth_balance": last_year["nisa_growth"],
                "company_stock_balance": last_year["company_stock"],
                "taxable_account_balance": last_year.get("taxable_account", 0),
                "cash_balance": last_year["cash"],
                "total": last_year["assets_end"]
            }

        retirement_data = []
        assets = start_assets.copy()

        # 投資設定
        investment_return = self.investment_settings["nisa"]["expected_return"]
        dividend_yield = self.investment_settings["company_stock"]["dividend_yield"]
        taxable_dividend_yield = self.investment_settings["taxable_account"]["dividend_yield"]

        # 年金収入（月額）
        pension = self.loader.get_pension()
        monthly_pension = pension.get("monthly_amount", 180000)
        spouse_pension = 100000  # 配偶者の年金（想定）

        # 退職後の生活費（月額）
        monthly_living_cost = 250000  # 基本生活費
        monthly_medical = 20000  # 医療費（年齢とともに増加）
        monthly_leisure = 50000  # 余暇・娯楽

        for age in range(65, 91):  # 65-90歳
            years_from_retirement = age - 65

            # インフレ調整（年2%）
            inflation_rate = self.inflation_settings.get("living_expenses_rate", 0.02)
            adjusted_living = monthly_living_cost * ((1 + inflation_rate) ** years_from_retirement)
            adjusted_medical = monthly_medical * ((1 + inflation_rate) ** years_from_retirement)
            adjusted_leisure = monthly_leisure * ((1 + inflation_rate) ** years_from_retirement)

            # 医療費は年齢とともに増加（75歳以降は1.5倍）
            if age >= 75:
                adjusted_medical *= 1.5

            # 年間収入
            annual_pension = (monthly_pension + spouse_pension) * 12

            # 配当収入（税引後：79.685%）
            annual_dividend = (
                assets["company_stock_balance"] * dividend_yield +
                assets["taxable_account_balance"] * taxable_dividend_yield
            ) * 0.79685  # 20.315%の税金を引く

            total_income = annual_pension + annual_dividend

            # 年間支出
            annual_living = (adjusted_living + adjusted_medical + adjusted_leisure) * 12

            # 固定資産税・修繕費（持ち家の場合）
            property_tax = 150000  # 年15万円
            maintenance = 200000 * ((1 + inflation_rate) ** years_from_retirement)  # 年20万円から増加

            annual_expenses = annual_living + property_tax + maintenance

            # 年間収支
            annual_cashflow = total_income - annual_expenses

            # 不足分は資産を取り崩し
            if annual_cashflow < 0:
                # 現金から取り崩し
                withdrawal = abs(annual_cashflow)
                if assets["cash_balance"] >= withdrawal:
                    assets["cash_balance"] -= withdrawal
                else:
                    # 現金不足の場合は投資資産を売却
                    cash_used = assets["cash_balance"]
                    assets["cash_balance"] = 0
                    remaining_withdrawal = withdrawal - cash_used

                    # 優先順位: 特定口座 → NISA成長 → NISAつみたて → 自社株
                    if assets["taxable_account_balance"] >= remaining_withdrawal:
                        assets["taxable_account_balance"] -= remaining_withdrawal
                    elif assets["taxable_account_balance"] > 0:
                        taxable_used = assets["taxable_account_balance"]
                        assets["taxable_account_balance"] = 0
                        remaining_withdrawal -= taxable_used

                        if assets["nisa_growth_balance"] >= remaining_withdrawal:
                            assets["nisa_growth_balance"] -= remaining_withdrawal
                        elif assets["nisa_growth_balance"] > 0:
                            nisa_growth_used = assets["nisa_growth_balance"]
                            assets["nisa_growth_balance"] = 0
                            remaining_withdrawal -= nisa_growth_used

                            if assets["nisa_tsumitate_balance"] >= remaining_withdrawal:
                                assets["nisa_tsumitate_balance"] -= remaining_withdrawal
                            elif assets["nisa_tsumitate_balance"] > 0:
                                nisa_tsumitate_used = assets["nisa_tsumitate_balance"]
                                assets["nisa_tsumitate_balance"] = 0
                                remaining_withdrawal -= nisa_tsumitate_used

                                if assets["company_stock_balance"] >= remaining_withdrawal:
                                    assets["company_stock_balance"] -= remaining_withdrawal
                                else:
                                    assets["company_stock_balance"] = max(0, assets["company_stock_balance"] - remaining_withdrawal)
            else:
                # 余剰分は現金に積み上げ
                assets["cash_balance"] += annual_cashflow

            # 投資資産の運用益（年次）
            monthly_return = investment_return / 12
            assets["nisa_tsumitate_balance"] *= (1 + monthly_return) ** 12
            assets["nisa_growth_balance"] *= (1 + monthly_return) ** 12
            assets["company_stock_balance"] *= (1 + monthly_return) ** 12
            assets["taxable_account_balance"] *= (1 + monthly_return) ** 12

            # 総資産
            total_assets = (
                assets["nisa_tsumitate_balance"] +
                assets["nisa_growth_balance"] +
                assets["company_stock_balance"] +
                assets["taxable_account_balance"] +
                assets["cash_balance"]
            )

            retirement_data.append({
                "age": age,
                "year": 2065 + (age - 65),
                "income": {
                    "pension": annual_pension,
                    "dividend": annual_dividend,
                    "total": total_income
                },
                "expenses": {
                    "living": annual_living,
                    "property_tax": property_tax,
                    "maintenance": maintenance,
                    "total": annual_expenses
                },
                "cashflow": annual_cashflow,
                "assets": {
                    "nisa_tsumitate": assets["nisa_tsumitate_balance"],
                    "nisa_growth": assets["nisa_growth_balance"],
                    "company_stock": assets["company_stock_balance"],
                    "taxable_account": assets["taxable_account_balance"],
                    "cash": assets["cash_balance"],
                    "total": total_assets
                },
                "withdrawal": abs(annual_cashflow) if annual_cashflow < 0 else 0
            })

        # サマリー計算
        final_assets = retirement_data[-1]["assets"]["total"] if retirement_data else 0
        total_pension = sum(y["income"]["pension"] for y in retirement_data)
        total_dividend = sum(y["income"]["dividend"] for y in retirement_data)
        total_withdrawal = sum(y["withdrawal"] for y in retirement_data)

        # 資産枯渇年齢を計算
        depletion_age = None
        for data in retirement_data:
            if data["assets"]["total"] < 1000000:  # 100万円未満になった年齢
                depletion_age = data["age"]
                break

        summary = {
            "start_assets": start_assets["total"],
            "final_assets": final_assets,
            "total_pension": total_pension,
            "total_dividend": total_dividend,
            "total_withdrawal": total_withdrawal,
            "depletion_age": depletion_age,
            "assets_survived": depletion_age is None
        }

        return retirement_data, summary

    def run_monte_carlo(self, num_simulations=1000, progress_callback=None):
        """
        モンテカルロシミュレーション（確率的シミュレーション）

        Args:
            num_simulations: シミュレーション回数（デフォルト1000回）
            progress_callback: 進捗コールバック関数

        Returns:
            dict: モンテカルロシミュレーション結果
        """
        # 基本設定
        base_return = self.investment_settings["nisa"]["expected_return"]
        return_std = 0.15  # 標準偏差15%（株式市場の一般的な変動）

        all_results = []

        for i in range(num_simulations):
            # 投資リターンをランダムに変動（正規分布）
            annual_returns = []
            for year in range(65 - self.basic_info["start_age"] + 1):
                # 正規分布からランダムサンプリング
                return_rate = random.gauss(base_return, return_std)
                # 極端な値を制限（-30% 〜 +50%）
                return_rate = max(-0.30, min(0.50, return_rate))
                annual_returns.append(return_rate)

            # 一時的なデータローダーを作成
            temp_loader = DataLoader()
            plan_data = temp_loader.get_all_data()

            # 年齢ごとに異なるリターンを適用（簡易版）
            # 実際には月次でリターンを変動させるべきだが、計算コストを考慮して年次で変動
            temp_calc = LifePlanCalculator(temp_loader)

            # シンプルなシミュレーション: 平均リターンを使用
            avg_return = sum(annual_returns) / len(annual_returns)
            plan_data["investment_settings"]["nisa"]["expected_return"] = avg_return
            plan_data["investment_settings"]["taxable_account"]["expected_return"] = avg_return
            temp_loader.plan_data = plan_data
            temp_calc = LifePlanCalculator(temp_loader)

            # シミュレーション実行
            monthly, yearly = temp_calc.simulate_30_years()

            # 最終資産を記録
            final_assets = yearly[-1]["assets_end"] if yearly else 0
            all_results.append({
                "simulation_id": i + 1,
                "final_assets": final_assets,
                "avg_return": avg_return,
                "yearly_data": yearly
            })

            # 進捗コールバック
            if progress_callback and (i + 1) % 50 == 0:
                progress_callback(i + 1, num_simulations)

        # 統計分析
        final_assets_list = [r["final_assets"] for r in all_results]
        final_assets_list.sort()

        # パーセンタイル計算
        percentile_10 = final_assets_list[int(num_simulations * 0.10)]
        percentile_25 = final_assets_list[int(num_simulations * 0.25)]
        percentile_50 = final_assets_list[int(num_simulations * 0.50)]  # 中央値
        percentile_75 = final_assets_list[int(num_simulations * 0.75)]
        percentile_90 = final_assets_list[int(num_simulations * 0.90)]

        # 目標達成確率（例: 5,000万円以上）
        target_50m = sum(1 for assets in final_assets_list if assets >= 50000000) / num_simulations * 100
        target_70m = sum(1 for assets in final_assets_list if assets >= 70000000) / num_simulations * 100
        target_100m = sum(1 for assets in final_assets_list if assets >= 100000000) / num_simulations * 100

        summary = {
            "num_simulations": num_simulations,
            "mean": sum(final_assets_list) / num_simulations,
            "median": percentile_50,
            "min": min(final_assets_list),
            "max": max(final_assets_list),
            "std": np.std(final_assets_list),
            "percentiles": {
                "10th": percentile_10,
                "25th": percentile_25,
                "50th": percentile_50,
                "75th": percentile_75,
                "90th": percentile_90
            },
            "target_probabilities": {
                "50m": target_50m,
                "70m": target_70m,
                "100m": target_100m
            }
        }

        return {
            "summary": summary,
            "all_results": all_results,
            "distribution": final_assets_list
        }

    def run_monte_carlo_advanced(self, num_simulations=1000, progress_callback=None):
        """
        本格的なモンテカルロシミュレーション
        年ごとに異なるリターンを適用してsequence-of-returnsリスクを考慮

        Args:
            num_simulations: シミュレーション回数（デフォルト1000回）
            progress_callback: 進捗コールバック関数

        Returns:
            dict: 詳細なモンテカルロシミュレーション結果
        """
        # 基本設定
        base_return = self.investment_settings["nisa"]["expected_return"]
        return_std = 0.15  # 標準偏差15%

        all_results = []

        for sim_idx in range(num_simulations):
            # 年ごとのランダムリターンを生成（40年分）
            annual_returns = []
            num_years = 65 - self.basic_info["start_age"] + 1

            for year in range(num_years):
                # 正規分布からランダムサンプリング
                return_rate = random.gauss(base_return, return_std)
                # 極端な値を制限（-40% 〜 +60%）
                return_rate = max(-0.40, min(0.60, return_rate))
                annual_returns.append(return_rate)

            # このシミュレーションの詳細データを実行
            yearly_data = self._simulate_with_variable_returns(annual_returns)

            # 最終資産を記録
            final_assets = yearly_data[-1]["assets_end"] if yearly_data else 0

            all_results.append({
                "simulation_id": sim_idx + 1,
                "final_assets": final_assets,
                "returns": annual_returns,
                "yearly_data": yearly_data
            })

            # 進捗コールバック
            if progress_callback and (sim_idx + 1) % 50 == 0:
                progress_callback(sim_idx + 1, num_simulations)

        # 統計分析
        final_assets_list = [r["final_assets"] for r in all_results]
        final_assets_list.sort()

        # パーセンタイル計算
        percentile_10 = final_assets_list[int(num_simulations * 0.10)]
        percentile_25 = final_assets_list[int(num_simulations * 0.25)]
        percentile_50 = final_assets_list[int(num_simulations * 0.50)]
        percentile_75 = final_assets_list[int(num_simulations * 0.75)]
        percentile_90 = final_assets_list[int(num_simulations * 0.90)]

        # 目標達成確率
        target_50m = sum(1 for assets in final_assets_list if assets >= 50000000) / num_simulations * 100
        target_70m = sum(1 for assets in final_assets_list if assets >= 70000000) / num_simulations * 100
        target_100m = sum(1 for assets in final_assets_list if assets >= 100000000) / num_simulations * 100

        # パーセンタイルごとの年次推移を計算
        percentile_yearly_progression = self._calculate_percentile_progression(
            all_results, [10, 25, 50, 75, 90]
        )

        summary = {
            "num_simulations": num_simulations,
            "mean": sum(final_assets_list) / num_simulations,
            "median": percentile_50,
            "min": min(final_assets_list),
            "max": max(final_assets_list),
            "std": np.std(final_assets_list),
            "percentiles": {
                "10th": percentile_10,
                "25th": percentile_25,
                "50th": percentile_50,
                "75th": percentile_75,
                "90th": percentile_90
            },
            "target_probabilities": {
                "50m": target_50m,
                "70m": target_70m,
                "100m": target_100m
            },
            "yearly_progression": percentile_yearly_progression
        }

        return {
            "summary": summary,
            "all_results": all_results,
            "distribution": final_assets_list
        }

    def _simulate_with_variable_returns(self, annual_returns):
        """
        年ごとに異なるリターンを適用してシミュレーションを実行

        Args:
            annual_returns: 年ごとのリターンのリスト

        Returns:
            list: 年次データのリスト
        """
        start_age = self.basic_info["start_age"]
        end_age = self.basic_info["end_age"]

        yearly_summary = []

        # 初期資産
        assets = {
            "nisa_tsumitate_balance": 0,
            "nisa_growth_balance": 0,
            "company_stock_balance": 0,
            "company_stock_shares": 0,
            "education_fund_balance": 0,
            "marriage_fund_balance": 0,
            "taxable_account_balance": 0,
            "cash_balance": 0,
            "total": 0
        }

        nisa_tsumitate_total_contribution = 0
        nisa_growth_total_contribution = 0

        # 自社株情報
        company_stock_settings = self.investment_settings["company_stock"]
        stock_price = company_stock_settings["initial_price"]
        stock_growth_rate = company_stock_settings["price_growth_rate"]
        dividend_yield = company_stock_settings["dividend_yield"]
        incentive_rate = company_stock_settings["incentive_rate"]

        # 年齢ごとにループ
        for age in range(start_age, end_age + 1):
            year_index = age - start_age
            year_return = annual_returns[year_index] if year_index < len(annual_returns) else annual_returns[-1]
            monthly_return = year_return / 12

            year_start_assets = assets.copy()
            yearly_income = 0
            yearly_expenses = 0
            yearly_investment = 0
            yearly_cashflow = 0

            # 各月をシミュレート
            for month in range(1, 13):
                month_data = self.calculate_monthly_data(age, month, assets)

                # 年間集計
                yearly_income += month_data["income"]["total"]
                yearly_expenses += month_data["expenses"]["total"]
                yearly_investment += month_data["investment"]["total"]
                yearly_cashflow += month_data["cashflow"]["monthly"]

                # 資産更新（変動リターンを適用）
                # NISA積立
                nisa_contribution = month_data["investment"].get("nisa_tsumitate", 0)
                if nisa_contribution > 0:
                    if nisa_tsumitate_total_contribution < self.investment_settings["nisa"]["tsumitate_limit"]:
                        contribution = min(nisa_contribution,
                                         self.investment_settings["nisa"]["tsumitate_limit"] - nisa_tsumitate_total_contribution)
                        nisa_tsumitate_total_contribution += contribution
                        assets["nisa_tsumitate_balance"] = (assets["nisa_tsumitate_balance"] + contribution) * (1 + monthly_return)
                    else:
                        # つみたてNISA満額後は特定口座に投資
                        assets["taxable_account_balance"] = (assets["taxable_account_balance"] + nisa_contribution) * (1 + monthly_return)

                # NISA成長投資枠（ボーナス月のみ）
                nisa_growth_contribution = month_data["investment"].get("nisa_growth", 0)
                if nisa_growth_contribution > 0:
                    if nisa_growth_total_contribution < self.investment_settings["nisa"]["growth_limit"]:
                        contribution = min(nisa_growth_contribution,
                                         self.investment_settings["nisa"]["growth_limit"] - nisa_growth_total_contribution)
                        nisa_growth_total_contribution += contribution
                        assets["nisa_growth_balance"] = (assets["nisa_growth_balance"] + contribution) * (1 + monthly_return)
                    else:
                        # NISA満額後は特定口座に投資
                        assets["taxable_account_balance"] = (assets["taxable_account_balance"] + nisa_growth_contribution) * (1 + monthly_return)

                # 自社株購入
                company_stock_contribution = month_data["investment"].get("company_stock", 0)
                if company_stock_contribution > 0:
                    actual_purchase = company_stock_contribution * (1 + incentive_rate)
                    shares_purchased = actual_purchase / stock_price
                    assets["company_stock_shares"] += shares_purchased

                # 教育資金積立
                education_contribution = month_data["investment"].get("education_fund", 0)
                if education_contribution > 0:
                    assets["education_fund_balance"] = (assets["education_fund_balance"] + education_contribution) * (1 + monthly_return)

                # 結婚資金積立
                marriage_contribution = month_data["investment"].get("marriage_fund", 0)
                if marriage_contribution > 0:
                    assets["marriage_fund_balance"] = (assets["marriage_fund_balance"] + marriage_contribution) * (1 + monthly_return)

                # 子供準備資金積立 - 現金として積立
                child_prep_contribution = month_data["investment"].get("child_preparation_fund", 0)
                if child_prep_contribution > 0:
                    assets["cash_balance"] += child_prep_contribution

                # 緊急予備費積立 - 現金として積立
                emergency_contribution = month_data["investment"].get("emergency_fund", 0)
                if emergency_contribution > 0:
                    assets["cash_balance"] += emergency_contribution

                # 高配当株投資（特定口座）
                high_dividend_contribution = month_data["investment"].get("high_dividend_stocks", 0)
                if high_dividend_contribution > 0:
                    assets["taxable_account_balance"] = (assets["taxable_account_balance"] + high_dividend_contribution) * (1 + monthly_return)

                # 現金残高更新
                assets["cash_balance"] += month_data["cashflow"]["monthly"]

            # 年末処理（教育費、ライフイベントなど）
            # 教育費の計算
            education_costs = self.loader.get_education_costs()
            annual_education_cost = 0

            # 第一子の教育費
            first_child_age = age - self.basic_info["first_child_birth_age"]
            if 0 <= first_child_age <= 22:
                if 0 <= first_child_age <= 5:
                    annual_education_cost += education_costs.get("age_0_5", {}).get("childcare", 0)
                elif 6 <= first_child_age <= 11:
                    annual_education_cost += education_costs.get("age_6_11", {}).get("school_fees", 0)
                    annual_education_cost += education_costs.get("age_6_11", {}).get("lessons", 0)
                elif 12 <= first_child_age <= 14:
                    annual_education_cost += education_costs.get("age_12_14", {}).get("school_fees", 0)
                    annual_education_cost += education_costs.get("age_12_14", {}).get("cram_school", 0)
                elif 15 <= first_child_age <= 17:
                    annual_education_cost += education_costs.get("age_15_17", {}).get("school_fees", 0)
                    annual_education_cost += education_costs.get("age_15_17", {}).get("cram_school", 0)
                    annual_education_cost -= self.loader.get_high_school_subsidy()
                elif first_child_age == 18:
                    annual_education_cost += education_costs.get("age_18", {}).get("exam_fees", 0)

            # 第二子の教育費
            second_child_age = age - self.basic_info["second_child_birth_age"]
            if 0 <= second_child_age <= 22:
                if 0 <= second_child_age <= 5:
                    annual_education_cost += education_costs.get("age_0_5", {}).get("childcare", 0)
                elif 6 <= second_child_age <= 11:
                    annual_education_cost += education_costs.get("age_6_11", {}).get("school_fees", 0)
                    annual_education_cost += education_costs.get("age_6_11", {}).get("lessons", 0)
                elif 12 <= second_child_age <= 14:
                    annual_education_cost += education_costs.get("age_12_14", {}).get("school_fees", 0)
                    annual_education_cost += education_costs.get("age_12_14", {}).get("cram_school", 0)
                elif 15 <= second_child_age <= 17:
                    annual_education_cost += education_costs.get("age_15_17", {}).get("school_fees", 0)
                    annual_education_cost += education_costs.get("age_15_17", {}).get("cram_school", 0)
                    annual_education_cost -= self.loader.get_high_school_subsidy()
                elif second_child_age == 18:
                    annual_education_cost += education_costs.get("age_18", {}).get("exam_fees", 0)

            # 教育費を現金から支払い（インフレ調整）
            if annual_education_cost > 0:
                inflation_rate = self.inflation_settings.get("education_rate", 0)
                adjusted_cost = self.apply_inflation(annual_education_cost, age - start_age, inflation_rate)
                assets["cash_balance"] -= adjusted_cost

            # 自社株の株価更新
            stock_price = stock_price * (1 + stock_growth_rate)
            assets["company_stock_balance"] = assets["company_stock_shares"] * stock_price

            # 配当金（年末に一括計算）
            if assets["company_stock_balance"] > 0:
                annual_dividend = assets["company_stock_balance"] * dividend_yield

                # 配当金の再投資判定
                if age <= 45:
                    reinvest_rate = self.investment_settings["dividend_reinvestment"]["age_0_45"]
                elif age <= 55:
                    reinvest_rate = self.investment_settings["dividend_reinvestment"]["age_46_55"]
                elif age <= 64:
                    reinvest_rate = self.investment_settings["dividend_reinvestment"]["age_56_64"]
                else:
                    reinvest_rate = self.investment_settings["dividend_reinvestment"]["age_65_99"]

                reinvest_amount = annual_dividend * reinvest_rate
                cash_dividend = annual_dividend - reinvest_amount

                # 再投資（自社株追加購入）
                if reinvest_amount > 0:
                    shares_purchased = reinvest_amount / stock_price
                    assets["company_stock_shares"] += shares_purchased
                    assets["company_stock_balance"] = assets["company_stock_shares"] * stock_price

                # 現金配当
                assets["cash_balance"] += cash_dividend

            # ライフイベント支出（結婚、住宅購入など）
            if age == self.life_events["marriage"]["age"]:
                marriage_cost = self.life_events["marriage"]["cost"]
                if assets["marriage_fund_balance"] >= marriage_cost:
                    assets["marriage_fund_balance"] -= marriage_cost
                else:
                    shortfall = marriage_cost - assets["marriage_fund_balance"]
                    assets["marriage_fund_balance"] = 0
                    assets["cash_balance"] -= shortfall

            if age == self.life_events["home_purchase"]["age"]:
                down_payment = self.life_events["home_purchase"]["down_payment"]
                closing_costs = self.life_events["home_purchase"]["closing_costs"]
                total_upfront = down_payment + closing_costs

                if assets["cash_balance"] >= total_upfront:
                    assets["cash_balance"] -= total_upfront
                else:
                    shortfall = total_upfront - assets["cash_balance"]
                    assets["cash_balance"] = 0
                    if assets["education_fund_balance"] >= shortfall:
                        assets["education_fund_balance"] -= shortfall
                    else:
                        remaining = shortfall - assets["education_fund_balance"]
                        assets["education_fund_balance"] = 0
                        if assets["nisa_growth_balance"] >= remaining:
                            assets["nisa_growth_balance"] -= remaining
                        else:
                            assets["nisa_growth_balance"] = 0

            # 大学費用支払い
            first_child_age = age - self.basic_info["first_child_birth_age"]
            if 19 <= first_child_age <= 22:
                annual_college_cost = education_costs.get("age_19_22", {}).get("tuition", 0)
                inflation_rate = self.inflation_settings.get("education_rate", 0)
                adjusted_cost = self.apply_inflation(annual_college_cost, age - start_age, inflation_rate)

                if assets["education_fund_balance"] >= adjusted_cost:
                    assets["education_fund_balance"] -= adjusted_cost
                else:
                    shortfall = adjusted_cost - assets["education_fund_balance"]
                    assets["education_fund_balance"] = 0
                    assets["cash_balance"] -= shortfall

            second_child_age = age - self.basic_info["second_child_birth_age"]
            if 19 <= second_child_age <= 22:
                annual_college_cost = education_costs.get("age_19_22", {}).get("tuition", 0)
                inflation_rate = self.inflation_settings.get("education_rate", 0)
                adjusted_cost = self.apply_inflation(annual_college_cost, age - start_age, inflation_rate)

                if assets["education_fund_balance"] >= adjusted_cost:
                    assets["education_fund_balance"] -= adjusted_cost
                else:
                    shortfall = adjusted_cost - assets["education_fund_balance"]
                    assets["education_fund_balance"] = 0
                    assets["cash_balance"] -= shortfall

            # 総資産計算
            assets["total"] = (
                assets["nisa_tsumitate_balance"] +
                assets["nisa_growth_balance"] +
                assets["company_stock_balance"] +
                assets["education_fund_balance"] +
                assets["marriage_fund_balance"] +
                assets["taxable_account_balance"] +
                assets["cash_balance"]
            )

            # 年次サマリーを記録
            yearly_summary.append({
                "age": age,
                "year": 2025 + (age - start_age),
                "income_total": yearly_income,
                "expenses_total": yearly_expenses,
                "investment_total": yearly_investment,
                "cashflow_annual": yearly_cashflow,
                "assets_start": year_start_assets["total"],
                "assets_end": assets["total"],
                "return_rate": year_return
            })

        return yearly_summary

    def _calculate_percentile_progression(self, all_results, percentiles):
        """
        パーセンタイルごとの年次推移を計算

        Args:
            all_results: 全シミュレーション結果
            percentiles: 計算するパーセンタイルのリスト（例: [10, 25, 50, 75, 90]）

        Returns:
            dict: パーセンタイルごとの年次推移
        """
        if not all_results or not all_results[0]["yearly_data"]:
            return {}

        num_years = len(all_results[0]["yearly_data"])
        progression = {p: [] for p in percentiles}

        # 各年について全シミュレーションの資産値を収集
        for year_idx in range(num_years):
            year_assets = []
            for result in all_results:
                if year_idx < len(result["yearly_data"]):
                    year_assets.append(result["yearly_data"][year_idx]["assets_end"])

            year_assets.sort()

            # 各パーセンタイルの値を計算
            for p in percentiles:
                idx = int(len(year_assets) * p / 100)
                idx = min(idx, len(year_assets) - 1)
                progression[p].append(year_assets[idx])

        return progression

    def generate_alerts(self, yearly_data):
        """
        アラートを生成（現金不足、赤字、NISA枠余り等を検出）

        Args:
            yearly_data: 年次データのリスト

        Returns:
            list: アラートのリスト
        """
        alerts = []
        alert_settings = self.loader.plan_data.get("alert_settings", {})

        if not alert_settings.get("enabled", True):
            return alerts

        cash_warning = alert_settings.get("cash_warning_threshold", 1000000)
        cash_critical = alert_settings.get("cash_critical_threshold", 500000)
        nisa_threshold = alert_settings.get("nisa_utilization_threshold", 0.8)

        for year_data in yearly_data:
            age = year_data["age"]
            cash = year_data.get("cash", 0)
            cashflow = year_data.get("cashflow_annual", 0)

            # 現金不足アラート
            if cash < cash_critical:
                alerts.append({
                    "age": age,
                    "severity": "critical",
                    "type": "low_cash",
                    "message": f"{age}歳時点で現金が{cash/10000:.0f}万円しかありません（危険レベル）",
                    "value": cash
                })
            elif cash < cash_warning:
                alerts.append({
                    "age": age,
                    "severity": "warning",
                    "type": "low_cash",
                    "message": f"{age}歳時点で現金が{cash/10000:.0f}万円を下回っています",
                    "value": cash
                })

            # 赤字アラート
            if cashflow < 0 and alert_settings.get("deficit_warning", True):
                alerts.append({
                    "age": age,
                    "severity": "warning",
                    "type": "deficit",
                    "message": f"{age}歳は年間{abs(cashflow)/10000:.0f}万円の赤字です",
                    "value": cashflow
                })

        # NISA枠の利用率チェック
        total_nisa_contribution = sum(
            y.get("nisa_tsumitate", 0) + y.get("nisa_growth", 0)
            for y in yearly_data if y["age"] < 65
        )
        years_count = len([y for y in yearly_data if y["age"] < 65])
        nisa_limit = self.investment_settings["nisa"]["tsumitate_limit"] + \
                     self.investment_settings["nisa"]["growth_limit"]

        if years_count > 0:
            avg_annual_nisa = total_nisa_contribution / years_count
            if avg_annual_nisa < 1800000 * nisa_threshold:  # 年180万円の80%
                alerts.append({
                    "age": None,
                    "severity": "info",
                    "type": "nisa_underutilized",
                    "message": f"NISA枠を十分に活用できていません（年平均{avg_annual_nisa/10000:.0f}万円）",
                    "value": avg_annual_nisa
                })

        return alerts

    def calculate_risk_score(self, yearly_data, monte_carlo_data=None):
        """
        リスク評価スコアを計算

        Args:
            yearly_data: 年次データ
            monte_carlo_data: モンテカルロデータ（オプション）

        Returns:
            dict: リスクスコアと評価
        """
        risk_scoring = self.loader.plan_data.get("risk_scoring", {})

        if not risk_scoring.get("enabled", True):
            return {"score": 0, "grade": "N/A", "details": {}}

        weights = risk_scoring.get("weights", {
            "final_assets": 0.3,
            "cash_stability": 0.25,
            "deficit_years": 0.2,
            "investment_diversity": 0.15,
            "emergency_fund": 0.1
        })

        scores = {}

        # 1. 最終資産スコア（100点満点）
        final_assets = yearly_data[-1]["assets_end"]
        if final_assets >= 100000000:  # 1億円以上
            scores["final_assets"] = 100
        elif final_assets >= 70000000:
            scores["final_assets"] = 80 + (final_assets - 70000000) / 30000000 * 20
        elif final_assets >= 50000000:
            scores["final_assets"] = 60 + (final_assets - 50000000) / 20000000 * 20
        else:
            scores["final_assets"] = max(0, final_assets / 50000000 * 60)

        # 2. 現金安定性スコア（100点満点）
        min_cash = min(y.get("cash", 0) for y in yearly_data)
        avg_cash = sum(y.get("cash", 0) for y in yearly_data) / len(yearly_data)

        if min_cash >= 3000000:  # 常に300万円以上
            cash_score = 100
        elif min_cash >= 1000000:
            cash_score = 60 + (min_cash - 1000000) / 2000000 * 40
        else:
            cash_score = max(0, min_cash / 1000000 * 60)

        scores["cash_stability"] = cash_score

        # 3. 赤字年数スコア（100点満点）
        deficit_years = sum(1 for y in yearly_data if y.get("cashflow_annual", 0) < 0)
        deficit_score = max(0, 100 - deficit_years * 5)  # 赤字1年で-5点
        scores["deficit_years"] = deficit_score

        # 4. 投資分散スコア（100点満点）
        last_year = yearly_data[-1]
        nisa_ratio = (last_year.get("nisa_tsumitate", 0) + last_year.get("nisa_growth", 0)) / max(1, final_assets)
        stock_ratio = last_year.get("company_stock", 0) / max(1, final_assets)
        taxable_ratio = last_year.get("taxable_account", 0) / max(1, final_assets)

        # バランスが取れているほど高得点
        diversity_score = 100
        if stock_ratio > 0.5:  # 自社株が50%超は集中リスク
            diversity_score -= 30
        if nisa_ratio < 0.3:  # NISA比率が低い
            diversity_score -= 20

        scores["investment_diversity"] = max(0, diversity_score)

        # 5. 緊急予備費スコア（100点満点）
        emergency_reserve = self.loader.plan_data.get("emergency_reserve", 3000000)
        avg_cash_score = min(100, avg_cash / emergency_reserve * 100)
        scores["emergency_fund"] = avg_cash_score

        # 総合スコア計算
        total_score = sum(scores[key] * weights.get(key, 0) for key in scores.keys())

        # グレード判定
        grade_thresholds = risk_scoring.get("grade_thresholds", {
            "S": 90, "A": 80, "B": 70, "C": 60, "D": 0
        })

        grade = "D"
        for g, threshold in sorted(grade_thresholds.items(), key=lambda x: x[1], reverse=True):
            if total_score >= threshold:
                grade = g
                break

        # リスク要因と強みを抽出
        risk_factors = []
        strengths = []

        if scores["final_assets"] < 60:
            risk_factors.append(f"最終資産が目標に届いていません（{final_assets/10000:.0f}万円）")
        else:
            strengths.append(f"最終資産が十分です（{final_assets/10000:.0f}万円）")

        if scores["cash_stability"] < 60:
            risk_factors.append(f"現金不足のリスクがあります（最低{min_cash/10000:.0f}万円）")
        else:
            strengths.append(f"現金が安定しています（平均{avg_cash/10000:.0f}万円）")

        if deficit_years > 3:
            risk_factors.append(f"{deficit_years}年間赤字があります")
        else:
            strengths.append("収支が安定しています")

        if scores["investment_diversity"] < 60:
            risk_factors.append("投資先の分散が不十分です")
        else:
            strengths.append("投資先が適切に分散されています")

        return {
            "score": round(total_score, 1),
            "grade": grade,
            "scores": scores,
            "risk_factors": risk_factors,
            "strengths": strengths,
            "details": {
                "final_assets": final_assets,
                "min_cash": min_cash,
                "avg_cash": avg_cash,
                "deficit_years": deficit_years
            }
        }

    def calculate_furusato_nozei_limit(self, gross_annual_income, dependents=0):
        """
        ふるさと納税控除限度額を計算

        Args:
            gross_annual_income: 年間総収入
            dependents: 扶養家族数

        Returns:
            dict: ふるさと納税情報
        """
        furusato_settings = self.tax_rates.get("furusato_nozei", {})

        if not furusato_settings.get("enabled", True):
            return {"limit": 0, "benefit": 0}

        # 簡易計算式（住民税所得割の約20%）
        # 給与所得控除
        if gross_annual_income <= 1625000:
            employment_deduction = 550000
        elif gross_annual_income <= 1800000:
            employment_deduction = gross_annual_income * 0.4 - 100000
        elif gross_annual_income <= 3600000:
            employment_deduction = gross_annual_income * 0.3 + 80000
        elif gross_annual_income <= 6600000:
            employment_deduction = gross_annual_income * 0.2 + 440000
        elif gross_annual_income <= 8500000:
            employment_deduction = gross_annual_income * 0.1 + 1100000
        else:
            employment_deduction = 1950000

        # 所得金額
        income = gross_annual_income - employment_deduction

        # 所得控除（基礎控除48万円 + 社会保険料控除 + 扶養控除）
        basic_deduction = 480000
        social_insurance = gross_annual_income * self.tax_rates["social_insurance_rate"]
        dependent_deduction = dependents * 380000

        total_deduction = basic_deduction + social_insurance + dependent_deduction

        # 課税所得
        taxable_income = max(0, income - total_deduction)

        # 住民税所得割（課税所得の10%）
        resident_tax = taxable_income * 0.1

        # ふるさと納税限度額（住民税所得割の約20% + 2,000円）
        limit = resident_tax * 0.2 + 2000

        # 実質2,000円でもらえる返礼品の価値（限度額の30%と仮定）
        benefit = (limit - 2000) * 0.3

        return {
            "limit": round(limit, -3),  # 千円単位で四捨五入
            "benefit": round(benefit, -3),
            "resident_tax": resident_tax,
            "description": f"年収{gross_annual_income/10000:.0f}万円の場合"
        }

    def calculate_medical_deduction(self, medical_expenses, gross_annual_income):
        """
        医療費控除を計算

        Args:
            medical_expenses: 年間医療費
            gross_annual_income: 年間総収入

        Returns:
            dict: 医療費控除情報
        """
        medical_settings = self.tax_rates.get("medical_expense_deduction", {})

        if not medical_settings.get("enabled", True):
            return {"deduction": 0, "tax_savings": 0}

        threshold = medical_settings.get("threshold", 100000)

        # 医療費控除額（10万円または所得の5%のいずれか低い方を超えた分）
        income_threshold = gross_annual_income * 0.05
        actual_threshold = min(threshold, income_threshold)

        deduction = max(0, medical_expenses - actual_threshold)
        deduction = min(deduction, 2000000)  # 上限200万円

        # 税率を所得に応じて決定（簡易計算）
        if gross_annual_income <= 5500000:
            tax_rate = 0.15  # 所得税5% + 住民税10%
        elif gross_annual_income <= 8000000:
            tax_rate = 0.20  # 所得税10% + 住民税10%
        else:
            tax_rate = 0.23  # 所得税13% + 住民税10%

        tax_savings = deduction * tax_rate

        return {
            "deduction": deduction,
            "tax_savings": round(tax_savings, -3),
            "threshold": actual_threshold,
            "description": f"医療費{medical_expenses/10000:.0f}万円の場合"
        }

    def calculate_tax_optimization_suggestions(self, yearly_data):
        """
        税金最適化の提案を生成

        Args:
            yearly_data: 年次データ

        Returns:
            list: 最適化提案のリスト
        """
        suggestions = []

        for year_data in yearly_data:
            age = year_data["age"]

            # 収入情報から年収を推定（簡易計算）
            income_total = year_data.get("income_total", 0)
            gross_estimate = income_total / 0.75  # 手取りから逆算（簡易）

            # ふるさと納税の提案
            furusato = self.calculate_furusato_nozei_limit(gross_estimate, dependents=0)
            if furusato["limit"] > 10000:
                suggestions.append({
                    "age": age,
                    "type": "furusato_nozei",
                    "title": f"{age}歳：ふるさと納税で節税",
                    "savings": furusato["benefit"],
                    "details": f"限度額{furusato['limit']/10000:.0f}万円まで寄付可能。実質2,000円で約{furusato['benefit']/10000:.0f}万円相当の返礼品",
                    "action": f"年間{furusato['limit']/10000:.0f}万円のふるさと納税を実行"
                })

        return suggestions

    def run_optimization_analysis(self, num_patterns=5):
        """
        最適化提案AIを実行（現在のプランを分析して改善案を提案）

        Args:
            num_patterns: 生成する改善パターン数

        Returns:
            dict: 最適化提案結果
        """
        # 現在のプランを実行
        current_monthly, current_yearly = self.simulate_30_years()
        current_score = self.calculate_risk_score(current_yearly)["score"]

        # 問題点を検出
        alerts = self.generate_alerts(current_yearly)
        issues = self._analyze_plan_issues(current_yearly, alerts)

        # 改善パターンを生成
        patterns = self._generate_improvement_patterns(issues, num_patterns)

        # 各パターンをシミュレーション
        results = []
        for i, pattern in enumerate(patterns):
            # 一時的なDataLoaderを作成
            from data_loader import DataLoader
            temp_loader = DataLoader()
            plan_data = temp_loader.get_all_data()

            # パターンを適用
            plan_data = self._apply_pattern(plan_data, pattern)

            temp_loader.plan_data = plan_data
            temp_calc = LifePlanCalculator(temp_loader)

            # シミュレーション実行
            try:
                monthly, yearly = temp_calc.simulate_30_years()
                score = temp_calc.calculate_risk_score(yearly)["score"]

                final_assets = yearly[-1]["assets_end"]
                improvement = final_assets - current_yearly[-1]["assets_end"]

                results.append({
                    "pattern_id": i + 1,
                    "name": pattern["name"],
                    "reason": pattern["reason"],
                    "final_assets": final_assets,
                    "improvement": improvement,
                    "improvement_pct": (improvement / current_yearly[-1]["assets_end"]) * 100,
                    "score": score,
                    "score_improvement": score - current_score,
                    "yearly_data": yearly,
                    "changes": pattern["changes"]
                })
            except Exception as e:
                print(f"Pattern {i+1} failed: {e}")
                continue

        # スコアでソート
        results.sort(key=lambda x: x["score"], reverse=True)

        return {
            "current": {
                "final_assets": current_yearly[-1]["assets_end"],
                "score": current_score,
                "issues": issues,
                "alerts": alerts
            },
            "suggestions": results[:3],  # トップ3を返す
            "all_patterns": results
        }

    def _analyze_plan_issues(self, yearly_data, alerts):
        """
        プランの問題点を分析

        Args:
            yearly_data: 年次データ
            alerts: アラートリスト

        Returns:
            list: 問題点のリスト
        """
        issues = []

        # 現金不足の問題
        min_cash = min(y.get("cash", 0) for y in yearly_data)
        if min_cash < 1000000:
            issues.append({
                "type": "low_cash",
                "severity": "high" if min_cash < 500000 else "medium",
                "description": f"現金が最低{min_cash/10000:.0f}万円まで減少",
                "recommendation": "緊急予備費を増やす、または支出を削減"
            })

        # 赤字年の問題
        deficit_years = [y for y in yearly_data if y.get("cashflow_annual", 0) < 0]
        if len(deficit_years) > 0:
            issues.append({
                "type": "deficit",
                "severity": "high" if len(deficit_years) > 3 else "medium",
                "description": f"{len(deficit_years)}年間が赤字",
                "ages": [y["age"] for y in deficit_years],
                "recommendation": "投資額を減らすか、収入を増やす"
            })

        # NISA枠の未活用
        total_nisa = sum(y.get("nisa_tsumitate", 0) + y.get("nisa_growth", 0) for y in yearly_data)
        avg_nisa = total_nisa / len(yearly_data)
        if avg_nisa < 1440000:  # 年180万円の80%
            issues.append({
                "type": "nisa_underutilized",
                "severity": "low",
                "description": f"NISA枠を年平均{avg_nisa/10000:.0f}万円しか使っていない",
                "recommendation": "NISA積立額を増やす"
            })

        # 最終資産が低い
        final_assets = yearly_data[-1]["assets_end"]
        if final_assets < 50000000:
            issues.append({
                "type": "low_final_assets",
                "severity": "high",
                "description": f"最終資産が{final_assets/10000:.0f}万円で目標未達",
                "recommendation": "投資額を増やす、または支出を削減"
            })

        return issues

    def _generate_improvement_patterns(self, issues, num_patterns):
        """
        改善パターンを生成

        Args:
            issues: 問題点リスト
            num_patterns: 生成数

        Returns:
            list: 改善パターンのリスト
        """
        patterns = []

        # パターン1: NISA積立を増やす
        patterns.append({
            "name": "NISA積立額を増やす（月+1万円）",
            "reason": "NISA枠を最大限活用して節税効果を高める",
            "changes": [
                {"type": "nisa_increase", "amount": 10000}
            ]
        })

        # パターン2: 高配当株投資を増やす
        patterns.append({
            "name": "高配当株投資を増やす（月+2万円）",
            "reason": "配当収入を増やして老後の安定収入を確保",
            "changes": [
                {"type": "high_dividend_increase", "amount": 20000}
            ]
        })

        # パターン3: 全体的に投資額を10%増やす
        patterns.append({
            "name": "全投資額を10%増額",
            "reason": "資産形成を加速し、最終資産を増やす",
            "changes": [
                {"type": "all_investment_increase", "rate": 1.10}
            ]
        })

        # パターン4: 配当再投資率を上げる
        patterns.append({
            "name": "配当再投資率を20%アップ",
            "reason": "複利効果を最大化",
            "changes": [
                {"type": "dividend_reinvest_increase", "rate": 0.20}
            ]
        })

        # パターン5: 緊急予備費を削減して投資へ
        patterns.append({
            "name": "緊急予備費を削減（月-1万円）して投資へ",
            "reason": "余剰資金を運用に回して資産を増やす",
            "changes": [
                {"type": "emergency_to_investment", "amount": 10000}
            ]
        })

        return patterns[:num_patterns]

    def _apply_pattern(self, plan_data, pattern):
        """
        改善パターンをプランデータに適用

        Args:
            plan_data: プランデータ
            pattern: 改善パターン

        Returns:
            dict: 修正されたプランデータ
        """
        for change in pattern["changes"]:
            if change["type"] == "nisa_increase":
                # 全フェーズのNISA積立を増額
                for phase_key, phase_data in plan_data["phase_definitions"].items():
                    if "nisa_tsumitate" in phase_data.get("monthly_investment", {}):
                        phase_data["monthly_investment"]["nisa_tsumitate"] += change["amount"]

            elif change["type"] == "high_dividend_increase":
                # 高配当株投資を増額（phase5, phase6）
                for phase_key in ["phase5", "phase6"]:
                    if phase_key in plan_data["phase_definitions"]:
                        phase_data = plan_data["phase_definitions"][phase_key]
                        if "high_dividend_stocks" in phase_data.get("monthly_investment", {}):
                            phase_data["monthly_investment"]["high_dividend_stocks"] += change["amount"]

            elif change["type"] == "all_investment_increase":
                # 全投資額を指定倍率で増額
                for phase_key, phase_data in plan_data["phase_definitions"].items():
                    for inv_key in phase_data.get("monthly_investment", {}).keys():
                        phase_data["monthly_investment"][inv_key] *= change["rate"]
                    for bonus_key in phase_data.get("bonus_allocation", {}).keys():
                        if "investment" in bonus_key or "fund" in bonus_key:
                            phase_data["bonus_allocation"][bonus_key] *= change["rate"]

            elif change["type"] == "dividend_reinvest_increase":
                # 配当再投資率を増やす
                for age_key in plan_data["investment_settings"]["dividend_reinvestment"].keys():
                    current_rate = plan_data["investment_settings"]["dividend_reinvestment"][age_key]
                    plan_data["investment_settings"]["dividend_reinvestment"][age_key] = min(1.0, current_rate + change["rate"])

            elif change["type"] == "emergency_to_investment":
                # 緊急予備費を削減してNISAへ
                for phase_key, phase_data in plan_data["phase_definitions"].items():
                    if "emergency_fund" in phase_data.get("monthly_investment", {}):
                        phase_data["monthly_investment"]["emergency_fund"] -= change["amount"]
                        if "nisa_tsumitate" in phase_data["monthly_investment"]:
                            phase_data["monthly_investment"]["nisa_tsumitate"] += change["amount"]

        return plan_data

    def export_to_dict(self):
        """
        計算結果を辞書形式でエクスポート

        Returns:
            dict: 計算結果
        """
        return {
            "monthly_data": self.monthly_data,
            "yearly_data": self.yearly_data,
            "summary": {
                "start_age": self.basic_info["start_age"],
                "end_age": self.basic_info["end_age"],
                "final_assets": self.yearly_data[-1]["assets_end"] if self.yearly_data else 0,
                "total_investment": sum(y["investment_total"] for y in self.yearly_data),
                "total_cashflow": sum(y["cashflow_annual"] for y in self.yearly_data)
            }
        }


# テスト用
if __name__ == "__main__":
    calc = LifePlanCalculator()
    monthly, yearly = calc.simulate_30_years()

    print("=== 年次サマリー（最初の5年） ===")
    for y in yearly[:5]:
        print(f"年齢 {y['age']}: 総資産 {y['assets_end']:,.0f}円, 年間CF {y['cashflow_annual']:,.0f}円")

    print("\n=== 年次サマリー（最後の5年） ===")
    for y in yearly[-5:]:
        print(f"年齢 {y['age']}: 総資産 {y['assets_end']:,.0f}円, 年間CF {y['cashflow_annual']:,.0f}円")
