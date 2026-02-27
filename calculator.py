"""
ライフプラン計算エンジン
30年間の詳細な資産形成シミュレーションを実行
"""
import numpy as np
import pandas as pd
from datetime import date as _date
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

        # シミュレーション開始年（設定ファイル優先、なければ実行年）
        self._start_year = int(self.basic_info.get("start_year", _date.today().year))

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
        年齢に対応する配偶者収入を取得（設定ファイルのキーを動的に解析）

        Args:
            age: 年齢

        Returns:
            float: 月収
        """
        marriage_age = self.basic_info["marriage_age"]
        if age < marriage_age:
            return 0

        spouse_income = self.loader.get_spouse_income()

        for key, amount in spouse_income.items():
            try:
                start, end = map(int, key.split('-'))
                if start <= age <= end:
                    return amount
            except (ValueError, AttributeError):
                continue
        return 0

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
        年齢に対応する家賃補助を取得（設定ファイルのキーを動的に解析）

        Args:
            age: 年齢

        Returns:
            float: 月額家賃補助
        """
        housing_allowance = self.loader.get_housing_allowance()

        for key, amount in housing_allowance.items():
            try:
                start, end = map(int, key.split('-'))
                if start <= age <= end:
                    return amount
            except (ValueError, AttributeError):
                continue
        return 0

    def get_housing_costs_for_age(self, age):
        """
        年齢に対応する住居費を取得（設定ファイルのキーを動的に解析）

        Args:
            age: 年齢

        Returns:
            dict: 住居費内訳
        """
        housing_costs = self.loader.get_housing_costs()

        for key, costs in housing_costs.items():
            try:
                start, end = map(int, key.split('-'))
                if start <= age <= end:
                    return costs
            except (ValueError, AttributeError):
                continue
        return {}

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

        # 第二子（3歳未満は第一子と同額、3〜14歳は多子加算で増額）
        if age >= second_child_birth:
            child2_age = age - second_child_birth
            if child2_age <= 2:
                total_allowance += child_allowance["age_0_2"]
            elif child2_age <= 14:
                total_allowance += child_allowance["age_3_14_second_child"]

        return total_allowance

    def _calc_annual_child_edu_cost(self, child_age, education_costs, years_from_start):
        """
        子供1人分の年間教育費を計算（インフレ調整済み）

        Args:
            child_age: 子供の年齢（0〜22）
            education_costs: 教育費設定dict
            years_from_start: シミュレーション開始からの経過年数

        Returns:
            float: 年間教育費（インフレ調整済み）
        """
        if child_age < 0 or child_age > 22:
            return 0

        inflation_rate = self.inflation_settings.get("education_rate", 0)
        cost = 0

        if 0 <= child_age <= 5:
            cost = education_costs.get("age_0_5", {}).get("childcare", 0)
        elif 6 <= child_age <= 11:
            cost = (education_costs.get("age_6_11", {}).get("school_fees", 0)
                    + education_costs.get("age_6_11", {}).get("lessons", 0))
        elif 12 <= child_age <= 14:
            cost = (education_costs.get("age_12_14", {}).get("school_fees", 0)
                    + education_costs.get("age_12_14", {}).get("cram_school", 0))
        elif 15 <= child_age <= 17:
            cost = (education_costs.get("age_15_17", {}).get("school_fees", 0)
                    + education_costs.get("age_15_17", {}).get("cram_school", 0)
                    - self.loader.get_high_school_subsidy())
        elif child_age == 18:
            cost = education_costs.get("age_18", {}).get("exam_fees", 0)
        elif child_age == 19:
            uni = education_costs.get("age_19_22", {})
            cost = (uni.get("university_entrance_fee", 0)
                    + uni.get("university_annual_tuition", 0)
                    + uni.get("living_expenses_annual", 0))
        elif 20 <= child_age <= 22:
            uni = education_costs.get("age_19_22", {})
            cost = (uni.get("university_annual_tuition", 0)
                    + uni.get("living_expenses_annual", 0))

        return self.apply_inflation(cost, years_from_start, inflation_rate)

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
        start_age = self.basic_info["start_age"]
        years_from_start = age - start_age
        is_bonus_month = month in [6, 12]

        # ── 収入計算 ──────────────────────────────────────────────────
        base_salary, bonus_months = self.get_salary_for_age(age)
        housing_allowance_monthly = self.get_housing_allowance_for_age(age)
        housing_allowance_annual = housing_allowance_monthly * 12

        # 【修正】月次給与はベース給与のみで計算（ボーナスを二重計上しない）
        annual_base_only = base_salary * 12
        net_annual_base = self.calculate_takehome(annual_base_only, housing_allowance_annual)
        monthly_net_salary = net_annual_base / 12

        # ボーナス手取り：年間トータル手取りとベース手取りの差分を2等分
        if is_bonus_month and bonus_months > 0:
            annual_total = base_salary * (12 + bonus_months)
            net_annual_total = self.calculate_takehome(annual_total, housing_allowance_annual)
            bonus_net = (net_annual_total - net_annual_base) / 2
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

        # ── 支出計算 ──────────────────────────────────────────────────
        phase = self.get_phase_for_age(age)
        housing_costs = self.get_housing_costs_for_age(age)

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

        # ── 投資計算 ──────────────────────────────────────────────────
        monthly_investment = {}
        if phase:
            for inv_key, inv_value in phase.get("monthly_investment", {}).items():
                monthly_investment[inv_key] = inv_value

        total_monthly_investment = sum(monthly_investment.values())

        # ボーナス配分（ボーナス月のみ、年2回なので半分ずつ）
        bonus_allocation = {}
        if is_bonus_month and phase:
            for bonus_key, bonus_value in phase.get("bonus_allocation", {}).items():
                bonus_allocation[bonus_key] = bonus_value / 2

        total_bonus_allocation = sum(bonus_allocation.values())

        # 【修正】月次投資とボーナス配分を加算合成（キー衝突時は合算）
        combined_investment = dict(monthly_investment)
        for k, v in bonus_allocation.items():
            combined_investment[k] = combined_investment.get(k, 0) + v

        # 月間収支（投資・貯蓄を差し引いた残余キャッシュ）
        monthly_cashflow = total_income - total_monthly_expenses - total_monthly_investment - total_bonus_allocation

        return {
            "age": age,
            "month": month,
            "year": self._start_year + years_from_start,
            "income": {
                "salary_net": monthly_net_salary,
                "bonus_net": bonus_net,
                "spouse_income": spouse_income,
                "pension": pension_income,
                "child_allowance": child_allowance,
                "housing_allowance": housing_allowance_monthly,
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
                **combined_investment,
                "total": total_monthly_investment + total_bonus_allocation
            },
            "cashflow": {
                "monthly": monthly_cashflow,
            },
            "assets": {
                "nisa_balance": assets_previous_month.get("nisa_tsumitate_balance", 0)
                                + assets_previous_month.get("nisa_growth_balance", 0),
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

        education_costs = self.loader.get_education_costs()

        for age in range(start_age, end_age + 1):
            year_start_assets = assets.copy()
            yearly_income = 0
            yearly_expenses = 0
            yearly_investment = 0
            yearly_cashflow = 0
            years_from_start = age - start_age

            # ── 月次ループ ────────────────────────────────────────────
            for month in range(1, 13):
                month_data = self.calculate_monthly_data(age, month, assets)
                monthly_data.append(month_data)

                yearly_income += month_data["income"]["total"]
                yearly_expenses += month_data["expenses"]["total"]
                yearly_investment += month_data["investment"]["total"]
                yearly_cashflow += month_data["cashflow"]["monthly"]

                # NISA積立
                nisa_contribution = month_data["investment"].get("nisa_tsumitate", 0)
                if nisa_contribution > 0:
                    if nisa_tsumitate_total_contribution < self.investment_settings["nisa"]["tsumitate_limit"]:
                        contribution = min(nisa_contribution,
                                         self.investment_settings["nisa"]["tsumitate_limit"] - nisa_tsumitate_total_contribution)
                        nisa_tsumitate_total_contribution += contribution
                        monthly_return = self.investment_settings["nisa"]["expected_return"] / 12
                        assets["nisa_tsumitate_balance"] = (assets["nisa_tsumitate_balance"] + contribution) * (1 + monthly_return)
                    else:
                        # つみたてNISA満額後は特定口座へ
                        monthly_return = self.investment_settings["taxable_account"]["expected_return"] / 12
                        assets["taxable_account_balance"] = (assets["taxable_account_balance"] + nisa_contribution) * (1 + monthly_return)

                # NISA成長投資枠（ボーナス月含む）
                nisa_growth_contribution = month_data["investment"].get("nisa_growth", 0)
                if nisa_growth_contribution > 0:
                    if nisa_growth_total_contribution < self.investment_settings["nisa"]["growth_limit"]:
                        contribution = min(nisa_growth_contribution,
                                         self.investment_settings["nisa"]["growth_limit"] - nisa_growth_total_contribution)
                        nisa_growth_total_contribution += contribution
                        monthly_return = self.investment_settings["nisa"]["expected_return"] / 12
                        assets["nisa_growth_balance"] = (assets["nisa_growth_balance"] + contribution) * (1 + monthly_return)
                    else:
                        monthly_return = self.investment_settings["taxable_account"]["expected_return"] / 12
                        assets["taxable_account_balance"] = (assets["taxable_account_balance"] + nisa_growth_contribution) * (1 + monthly_return)

                # 自社株購入（奨励金込み）
                company_stock_contribution = month_data["investment"].get("company_stock", 0)
                if company_stock_contribution > 0:
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

                # 子供準備資金（現金として積立）
                child_prep_contribution = month_data["investment"].get("child_preparation_fund", 0)
                if child_prep_contribution > 0:
                    assets["cash_balance"] += child_prep_contribution

                # 緊急予備費（現金として積立）
                emergency_contribution = month_data["investment"].get("emergency_fund", 0)
                if emergency_contribution > 0:
                    assets["cash_balance"] += emergency_contribution

                # 高配当株投資（特定口座）
                high_dividend_contribution = month_data["investment"].get("high_dividend_stocks", 0)
                if high_dividend_contribution > 0:
                    monthly_return = self.investment_settings["taxable_account"]["expected_return"] / 12
                    assets["taxable_account_balance"] = (assets["taxable_account_balance"] + high_dividend_contribution) * (1 + monthly_return)

                # 現金残高にキャッシュフローを反映
                assets["cash_balance"] += month_data["cashflow"]["monthly"]

            # ── 年末処理 ──────────────────────────────────────────────
            irregular_expenses = []

            # 【修正】統一ヘルパーで教育費を計算（K-12と大学を一括処理）
            first_child_age = age - self.basic_info["first_child_birth_age"]
            second_child_age = age - self.basic_info["second_child_birth_age"]

            k12_cost = 0       # K-12費用 → 現金から支払い
            university_cost = 0  # 大学費用 → 教育資金から支払い

            for child_age in [first_child_age, second_child_age]:
                cost = self._calc_annual_child_edu_cost(child_age, education_costs, years_from_start)
                if cost <= 0:
                    continue
                if child_age <= 18:
                    k12_cost += cost
                else:
                    university_cost += cost

            # K-12費用を現金から支払い
            if k12_cost > 0:
                assets["cash_balance"] -= k12_cost

            # 大学費用を教育資金 → 現金の順で支払い
            if university_cost > 0:
                payment_sources = []
                if assets["education_fund_balance"] >= university_cost:
                    assets["education_fund_balance"] -= university_cost
                    payment_sources.append({"source": "教育資金", "amount": university_cost})
                else:
                    edu_used = assets["education_fund_balance"]
                    shortfall = university_cost - edu_used
                    assets["education_fund_balance"] = 0
                    assets["cash_balance"] -= shortfall
                    if edu_used > 0:
                        payment_sources.append({"source": "教育資金", "amount": edu_used})
                    payment_sources.append({"source": "現金", "amount": shortfall})

                irregular_expenses.append({
                    "type": f"大学費用 ({first_child_age}歳・{second_child_age}歳)" if 19 <= first_child_age <= 22 and 19 <= second_child_age <= 22
                           else f"大学費用（第{'一' if 19 <= first_child_age <= 22 else '二'}子）",
                    "amount": university_cost,
                    "payment_sources": payment_sources
                })

            annual_education_cost = k12_cost + university_cost

            # 自社株の株価更新・配当計算
            stock_price = stock_price * (1 + stock_growth_rate)
            assets["company_stock_balance"] = assets["company_stock_shares"] * stock_price

            annual_dividend_total = 0
            annual_dividend_received = 0
            if assets["company_stock_balance"] > 0:
                annual_dividend = assets["company_stock_balance"] * dividend_yield
                annual_dividend_total = annual_dividend

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

                if reinvest_amount > 0:
                    shares_purchased = reinvest_amount / stock_price
                    assets["company_stock_shares"] += shares_purchased
                    assets["company_stock_balance"] = assets["company_stock_shares"] * stock_price

                assets["cash_balance"] += cash_dividend

            # ライフイベント：結婚
            if age == self.life_events["marriage"]["age"]:
                marriage_cost = self.life_events["marriage"]["cost"]
                payment_sources = []

                if assets["marriage_fund_balance"] >= marriage_cost:
                    assets["marriage_fund_balance"] -= marriage_cost
                    payment_sources.append({"source": "結婚資金", "amount": marriage_cost})
                else:
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

            # ライフイベント：住宅購入
            if age == self.life_events["home_purchase"]["age"]:
                down_payment = self.life_events["home_purchase"]["down_payment"]
                closing_costs = self.life_events["home_purchase"]["closing_costs"]
                total_upfront = down_payment + closing_costs
                payment_sources = []

                remaining = total_upfront

                # 1) 現金から支払い
                cash_used = min(assets["cash_balance"], remaining)
                if cash_used > 0:
                    assets["cash_balance"] -= cash_used
                    remaining -= cash_used
                    payment_sources.append({"source": "現金", "amount": cash_used})

                # 2) 教育資金から補填
                if remaining > 0:
                    edu_used = min(assets["education_fund_balance"], remaining)
                    if edu_used > 0:
                        assets["education_fund_balance"] -= edu_used
                        remaining -= edu_used
                        payment_sources.append({"source": "教育資金", "amount": edu_used})

                # 3) NISA成長投資枠から補填
                if remaining > 0:
                    nisa_used = min(assets["nisa_growth_balance"], remaining)
                    if nisa_used > 0:
                        assets["nisa_growth_balance"] -= nisa_used
                        remaining -= nisa_used
                        payment_sources.append({"source": "NISA成長", "amount": nisa_used})

                irregular_expenses.append({
                    "type": "住宅購入（頭金）",
                    "amount": down_payment,
                    "payment_sources": [{"source": "住宅購入費合計", "amount": total_upfront}]
                })
                irregular_expenses.append({
                    "type": "住宅購入（諸費用）",
                    "amount": closing_costs,
                    "payment_sources": payment_sources
                })

            # カスタムライフイベント
            for ev in self.life_events.get("custom_events", []):
                if ev.get("age") == age:
                    ev_cost = int(ev.get("cost", 0))
                    if ev_cost > 0:
                        assets["cash_balance"] -= ev_cost
                        irregular_expenses.append({
                            "type": ev.get("name", "カスタムイベント"),
                            "amount": ev_cost,
                            "payment_sources": [{"source": "現金", "amount": ev_cost}]
                        })

            # 総資産
            assets["total"] = (assets["nisa_tsumitate_balance"] +
                             assets["nisa_growth_balance"] +
                             assets["company_stock_balance"] +
                             assets["education_fund_balance"] +
                             assets["marriage_fund_balance"] +
                             assets["taxable_account_balance"] +
                             assets["cash_balance"])

            yearly_summary.append({
                "age": age,
                "year": self._start_year + years_from_start,
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
                "marriage_fund": assets["marriage_fund_balance"],
                "taxable_account": assets["taxable_account_balance"],
                "cash": assets["cash_balance"],
                "education_cost_annual": annual_education_cost,
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

        # 年始の資産（前年末）
        assets_start = {
            "nisa_tsumitate": prev_year_data["nisa_tsumitate"] if prev_year_data else 0,
            "nisa_growth": prev_year_data["nisa_growth"] if prev_year_data else 0,
            "company_stock": prev_year_data["company_stock"] if prev_year_data else 0,
            "education_fund": prev_year_data["education_fund"] if prev_year_data else 0,
            "marriage_fund": prev_year_data["marriage_fund"] if prev_year_data else 0,
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
            "marriage_fund": year_data["marriage_fund"],
            "taxable_account": year_data["taxable_account"],
            "cash": year_data["cash"],
            "total": year_data["assets_end"]
        }

        # 配当金情報
        dividend_info = {
            "company_stock_dividend": year_data["company_stock"] * self.investment_settings["company_stock"]["dividend_yield"],
            "taxable_dividend": year_data["taxable_account"] * self.investment_settings["taxable_account"]["dividend_yield"],
            "total_dividend_pretax": year_data.get("dividend_total", 0),
            "total_dividend_received": year_data.get("dividend_received", 0)
        }

        dividend_assets = year_data["company_stock"] + year_data["taxable_account"]
        dividend_info["dividend_yield"] = (dividend_info["total_dividend_pretax"] / dividend_assets * 100) if dividend_assets > 0 else 0

        return {
            "age": age,
            "year": year_data["year"],
            "assets_start": assets_start,
            "assets_end": assets_end,
            "income_total": year_data["income_total"],
            "expenses_total": year_data["expenses_total"],
            "investment_total": year_data["investment_total"],
            "cashflow_annual": year_data["cashflow_annual"],
            "education_cost": year_data.get("education_cost_annual", 0),
            "dividend_info": dividend_info,
            "irregular_expenses": year_data.get("irregular_expenses", [])
        }

    def get_education_summary(self):
        """
        教育費の詳細サマリーを取得
        【修正】_calc_annual_child_edu_cost を使って一元計算し、二重計上を排除

        Returns:
            dict: 教育費サマリー
        """
        if not self.yearly_data:
            return {}

        first_child_birth = self.basic_info["first_child_birth_age"]
        second_child_birth = self.basic_info["second_child_birth_age"]
        education_costs = self.loader.get_education_costs()

        child1_total = 0
        child2_total = 0
        child_allowance_total = 0

        child1_by_age = []
        child2_by_age = []

        for year_data in self.yearly_data:
            age = year_data["age"]
            years_from_start = age - self.basic_info["start_age"]

            first_child_age = age - first_child_birth
            second_child_age = age - second_child_birth

            # 第一子の教育費を直接計算（education_cost_annualの分割流用をやめる）
            if 0 <= first_child_age <= 22:
                child1_cost = self._calc_annual_child_edu_cost(
                    first_child_age, education_costs, years_from_start
                )
                child1_total += child1_cost
                child1_by_age.append({
                    "child_age": first_child_age,
                    "parent_age": age,
                    "annual_cost": child1_cost,
                    "cumulative_cost": child1_total
                })

            # 第二子の教育費を直接計算
            if 0 <= second_child_age <= 22:
                child2_cost = self._calc_annual_child_edu_cost(
                    second_child_age, education_costs, years_from_start
                )
                child2_total += child2_cost
                child2_by_age.append({
                    "child_age": second_child_age,
                    "parent_age": age,
                    "annual_cost": child2_cost,
                    "cumulative_cost": child2_total
                })

        # 児童手当の総額
        for year_data in self.yearly_data:
            monthly_allowance = self.calculate_child_allowance(year_data["age"])
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

        company_stock_balance = last_year["company_stock"]
        taxable_balance = last_year["taxable_account"]
        dividend_assets = company_stock_balance + taxable_balance

        company_dividend = company_stock_balance * self.investment_settings["company_stock"]["dividend_yield"]
        taxable_dividend = taxable_balance * self.investment_settings["taxable_account"]["dividend_yield"]
        total_dividend = company_dividend + taxable_dividend

        # 税引後（20.315%）
        dividend_after_tax = total_dividend * (1 - 0.20315)

        dividend_yield = (dividend_after_tax / dividend_assets * 100) if dividend_assets > 0 else 0

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

    def run_monte_carlo(self, n_simulations=300, return_std=0.08,
                        actual_cash_offset=0, actual_age=None):
        """
        モンテカルロシミュレーション（シミュレーションごとに異なるリターン率を使用）

        Args:
            n_simulations (int): シミュレーション回数
            return_std (float): 年間リターンの標準偏差
            actual_cash_offset (float): 実績ベース時の現金差分オフセット
            actual_age (int|None): オフセットを適用する開始年齢

        Returns:
            dict: パーセンタイル統計データ
        """
        start_age = self.basic_info["start_age"]
        end_age = self.basic_info["end_age"]
        n_years = end_age - start_age + 1

        base_nisa    = self.investment_settings["nisa"]["expected_return"]
        base_taxable = self.investment_settings["taxable_account"]["expected_return"]
        base_edu     = self.investment_settings["education_fund"]["expected_return"]

        results = np.zeros((n_simulations, n_years))

        # 元の設定を退避（try/finallyで確実に復元）
        orig_nisa    = base_nisa
        orig_taxable = base_taxable
        orig_edu     = base_edu

        try:
            for i in range(n_simulations):
                # シミュレーションごとにランダムリターン生成
                nisa_r    = float(np.clip(np.random.normal(base_nisa,    return_std),       -0.5, 1.5))
                taxable_r = float(np.clip(np.random.normal(base_taxable, return_std),       -0.5, 1.5))
                edu_r     = float(np.clip(np.random.normal(base_edu,     return_std * 0.5), -0.3, 0.5))

                self.investment_settings["nisa"]["expected_return"]            = nisa_r
                self.investment_settings["taxable_account"]["expected_return"] = taxable_r
                self.investment_settings["education_fund"]["expected_return"]  = edu_r

                _, yearly = self.simulate_30_years()

                for j, yd in enumerate(yearly):
                    offset = actual_cash_offset if (actual_age and yd["age"] >= actual_age) else 0
                    results[i, j] = yd["assets_end"] + offset

        finally:
            # 必ず元のリターン率に戻す
            self.investment_settings["nisa"]["expected_return"]            = orig_nisa
            self.investment_settings["taxable_account"]["expected_return"] = orig_taxable
            self.investment_settings["education_fund"]["expected_return"]  = orig_edu
            # ベースシミュレーションを復元
            self.simulate_30_years()

        ages = list(range(start_age, end_age + 1))
        final = results[:, -1]

        return {
            "ages": ages,
            "p5":   np.percentile(results, 5,  axis=0).tolist(),
            "p25":  np.percentile(results, 25, axis=0).tolist(),
            "p50":  np.percentile(results, 50, axis=0).tolist(),
            "p75":  np.percentile(results, 75, axis=0).tolist(),
            "p95":  np.percentile(results, 95, axis=0).tolist(),
            "mean": np.mean(results, axis=0).tolist(),
            "final_p5":   float(np.percentile(final, 5)),
            "final_p25":  float(np.percentile(final, 25)),
            "final_p50":  float(np.percentile(final, 50)),
            "final_p75":  float(np.percentile(final, 75)),
            "final_p95":  float(np.percentile(final, 95)),
            "final_mean": float(np.mean(final)),
            "n_simulations": n_simulations,
            "return_std": return_std,
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
