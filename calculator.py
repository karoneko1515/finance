"""
ライフプラン計算エンジン
30年間の詳細な資産形成シミュレーションを実行
"""
import numpy as np
import pandas as pd
from datetime import datetime
from data_loader import DataLoader


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

    def calculate_takehome(self, gross_annual, housing_allowance=0):
        """
        手取り額を計算

        Args:
            gross_annual: 年間総支給額
            housing_allowance: 家賃補助（課税対象）

        Returns:
            float: 手取り額
        """
        taxable_income = gross_annual + housing_allowance

        # 社会保険料
        social_insurance = taxable_income * self.tax_rates["social_insurance_rate"]

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

    def get_pension_for_age(self, age):
        """
        年齢に対応する年金収入を取得

        Args:
            age: 年齢

        Returns:
            float: 月額年金
        """
        pension = self.loader.get_pension()
        start_age = pension.get("start_age", 65)
        monthly_amount = pension.get("monthly_amount", 0)

        if age >= start_age:
            return monthly_amount
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

                # 現金残高更新
                assets["cash_balance"] += month_data["cashflow"]["monthly"]

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

            # 総資産
            assets["total"] = (assets["nisa_tsumitate_balance"] +
                             assets["nisa_growth_balance"] +
                             assets["company_stock_balance"] +
                             assets["education_fund_balance"] +
                             assets["marriage_fund_balance"] +
                             assets["taxable_account_balance"] +
                             assets["cash_balance"])

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
