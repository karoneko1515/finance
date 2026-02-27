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
        self.investment_plan = self.loader.get_investment_plan()
        self.spouse_nisa = self.loader.get_spouse_nisa()
        self.child_nisa = self.loader.get_child_nisa()
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

    def calculate_monthly_data(self, age, month, assets_previous_month,
                               nisa_cumulative=0, spouse_nisa_cumulative=0):
        """
        月次データを計算

        Args:
            age: 年齢
            month: 月（1-12）
            assets_previous_month: 前月末の資産状況
            nisa_cumulative: NISA累計拠出額（枠判定用）
            spouse_nisa_cumulative: 配偶者NISA累計拠出額（枠判定用）

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

        # ── 投資計算（investment_planから決定） ──────────────────────
        inv_plan = self.investment_plan
        nisa_limit = inv_plan.get("nisa_lifetime_limit", 18000000)
        plan_key = "pre_nisa_full" if nisa_cumulative < nisa_limit else "post_nisa_full"
        active_plan = inv_plan.get(plan_key, {})

        monthly_investment = dict(active_plan.get("monthly", {}))
        bonus_allocation = {}
        if is_bonus_month:
            for k, v in active_plan.get("bonus_per_payment", {}).items():
                bonus_allocation[k] = v

        # NISA枠が上限に近い場合はNISA投資を残枠に収める
        if plan_key == "pre_nisa_full":
            remaining_nisa = max(0, nisa_limit - nisa_cumulative)
            nisa_orcan_planned = monthly_investment.get("nisa_orcan", 0) + bonus_allocation.get("nisa_orcan", 0)
            nisa_fang_planned  = monthly_investment.get("nisa_fang",  0) + bonus_allocation.get("nisa_fang",  0)
            total_nisa_planned = nisa_orcan_planned + nisa_fang_planned
            if total_nisa_planned > remaining_nisa and total_nisa_planned > 0:
                cap_ratio = remaining_nisa / total_nisa_planned
                for d in [monthly_investment, bonus_allocation]:
                    for k in ["nisa_orcan", "nisa_fang"]:
                        if k in d:
                            d[k] = round(d[k] * cap_ratio)

        # 加算合成（月次+ボーナス）
        combined_investment = dict(monthly_investment)
        for k, v in bonus_allocation.items():
            combined_investment[k] = combined_investment.get(k, 0) + v

        # ── 配偶者NISA（結婚後に有効） ─────────────────────────────────
        marriage_age = self.basic_info.get("marriage_age", 28)
        spouse_nisa_cfg = self.spouse_nisa
        if spouse_nisa_cfg.get("enabled", False) and age >= marriage_age:
            s_nisa_limit = spouse_nisa_cfg.get("nisa_lifetime_limit", 18000000)
            s_plan_key = "pre_nisa_full" if spouse_nisa_cumulative < s_nisa_limit else "post_nisa_full"
            s_active = spouse_nisa_cfg.get(s_plan_key, {})
            s_monthly = dict(s_active.get("monthly", {}))
            s_bonus = {}
            if is_bonus_month:
                s_bonus = dict(s_active.get("bonus_per_payment", {}))
            # 配偶者NISA枠上限調整
            if s_plan_key == "pre_nisa_full":
                s_remaining = max(0, s_nisa_limit - spouse_nisa_cumulative)
                s_nisa_planned = sum(s_monthly.get(k, 0) + s_bonus.get(k, 0)
                                     for k in ["nisa_orcan", "nisa_fang", "nisa_sp500"])
                if s_nisa_planned > s_remaining and s_nisa_planned > 0:
                    s_cap_ratio = s_remaining / s_nisa_planned
                    for d in [s_monthly, s_bonus]:
                        for k in list(d.keys()):
                            d[k] = round(d[k] * s_cap_ratio)
            for k, v in s_monthly.items():
                combined_investment[f"spouse_{k}"] = combined_investment.get(f"spouse_{k}", 0) + v
            for k, v in s_bonus.items():
                combined_investment[f"spouse_{k}"] = combined_investment.get(f"spouse_{k}", 0) + v

        # ── 子供NISA（子供ごとに積立） ─────────────────────────────────
        child_nisa_cfg = self.child_nisa
        if child_nisa_cfg.get("enabled", False):
            c_monthly = child_nisa_cfg.get("monthly_per_child", 0)
            first_child_birth = self.basic_info.get("first_child_birth_age", 99)
            second_child_birth = self.basic_info.get("second_child_birth_age", 99)
            # 子供NISAは出生から高校卒業（18歳）まで積立
            if 0 <= (age - first_child_birth) <= 17:
                combined_investment["child1_nisa"] = combined_investment.get("child1_nisa", 0) + c_monthly
            if 0 <= (age - second_child_birth) <= 17:
                combined_investment["child2_nisa"] = combined_investment.get("child2_nisa", 0) + c_monthly

        # ── キャッシュフロアフロア ────────────────────────────────────
        # 投資は「収入 - 生活費」の範囲内に収める。超える場合は比例縮小
        available = total_income - total_monthly_expenses
        total_investment_requested = sum(combined_investment.values())

        if total_investment_requested <= 0 or available <= 0:
            if available <= 0:
                combined_investment = {k: 0 for k in combined_investment}
            total_actual_investment = 0
            monthly_cashflow = available
        elif total_investment_requested > available:
            ratio = available / total_investment_requested
            combined_investment = {k: round(v * ratio) for k, v in combined_investment.items()}
            total_actual_investment = sum(combined_investment.values())
            monthly_cashflow = available - total_actual_investment  # ≒0
        else:
            total_actual_investment = total_investment_requested
            monthly_cashflow = available - total_actual_investment

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
                "total": total_actual_investment
            },
            "cashflow": {
                "monthly": monthly_cashflow,
            },
            "assets": {
                "nisa_balance": assets_previous_month.get("nisa_orcan_balance", 0)
                                + assets_previous_month.get("nisa_fang_balance", 0),
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
            "nisa_orcan_balance": 0,        # 本人NISA(オルカン)残高
            "nisa_fang_balance": 0,          # 本人NISA(FANG+)残高
            "nisa_sp500_balance": 0,         # 本人NISA(SP500)残高
            "spouse_nisa_orcan_balance": 0,  # 配偶者NISA(オルカン)残高
            "spouse_nisa_sp500_balance": 0,  # 配偶者NISA(SP500)残高
            "child1_nisa_balance": 0,        # 第一子NISA残高
            "child2_nisa_balance": 0,        # 第二子NISA残高
            "company_stock_balance": 0,
            "company_stock_shares": 0,
            "education_fund_balance": 0,
            "marriage_fund_balance": 0,
            "taxable_account_balance": 0,
            "cash_balance": 0,
            "total": 0
        }

        nisa_cumulative = 0         # 本人NISA累計拠出額
        spouse_nisa_cumulative = 0  # 配偶者NISA累計拠出額
        child1_nisa_cumulative = 0  # 第一子NISA累計拠出額
        child2_nisa_cumulative = 0  # 第二子NISA累計拠出額
        nisa_limit = self.investment_plan.get("nisa_lifetime_limit", 18000000)
        child_nisa_limit = self.child_nisa.get("nisa_lifetime_limit_per_child", 18000000)
        spouse_nisa_limit = self.spouse_nisa.get("nisa_lifetime_limit", 18000000)

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
                month_data = self.calculate_monthly_data(
                    age, month, assets, nisa_cumulative, spouse_nisa_cumulative
                )
                monthly_data.append(month_data)

                yearly_income += month_data["income"]["total"]
                yearly_expenses += month_data["expenses"]["total"]
                yearly_investment += month_data["investment"]["total"]
                yearly_cashflow += month_data["cashflow"]["monthly"]

                nisa_monthly_return = self.investment_settings["nisa"]["expected_return"] / 12

                # NISA(オルカン)積立
                orcan_contribution = month_data["investment"].get("nisa_orcan", 0)
                if orcan_contribution > 0:
                    actual = min(orcan_contribution, max(0, nisa_limit - nisa_cumulative))
                    if actual > 0:
                        nisa_cumulative += actual
                        assets["nisa_orcan_balance"] = (assets["nisa_orcan_balance"] + actual) * (1 + nisa_monthly_return)

                # NISA(FANG+)積立
                fang_contribution = month_data["investment"].get("nisa_fang", 0)
                if fang_contribution > 0:
                    actual = min(fang_contribution, max(0, nisa_limit - nisa_cumulative))
                    if actual > 0:
                        nisa_cumulative += actual
                        assets["nisa_fang_balance"] = (assets["nisa_fang_balance"] + actual) * (1 + nisa_monthly_return)

                # NISA(SP500)積立
                sp500_contribution = month_data["investment"].get("nisa_sp500", 0)
                if sp500_contribution > 0:
                    actual = min(sp500_contribution, max(0, nisa_limit - nisa_cumulative))
                    if actual > 0:
                        nisa_cumulative += actual
                        assets["nisa_sp500_balance"] = (assets["nisa_sp500_balance"] + actual) * (1 + nisa_monthly_return)

                # 配偶者NISA積立
                s_nisa_return = self.spouse_nisa.get("expected_return", 0.05) / 12
                for fund_key, bal_key in [("spouse_nisa_orcan", "spouse_nisa_orcan_balance"),
                                           ("spouse_nisa_sp500", "spouse_nisa_sp500_balance")]:
                    s_contrib = month_data["investment"].get(fund_key, 0)
                    if s_contrib > 0:
                        actual = min(s_contrib, max(0, spouse_nisa_limit - spouse_nisa_cumulative))
                        if actual > 0:
                            spouse_nisa_cumulative += actual
                            assets[bal_key] = (assets[bal_key] + actual) * (1 + s_nisa_return)

                # 子供NISA積立
                c_nisa_return = self.child_nisa.get("expected_return", 0.07) / 12
                c1_contrib = month_data["investment"].get("child1_nisa", 0)
                if c1_contrib > 0:
                    actual = min(c1_contrib, max(0, child_nisa_limit - child1_nisa_cumulative))
                    if actual > 0:
                        child1_nisa_cumulative += actual
                        assets["child1_nisa_balance"] = (assets["child1_nisa_balance"] + actual) * (1 + c_nisa_return)

                c2_contrib = month_data["investment"].get("child2_nisa", 0)
                if c2_contrib > 0:
                    actual = min(c2_contrib, max(0, child_nisa_limit - child2_nisa_cumulative))
                    if actual > 0:
                        child2_nisa_cumulative += actual
                        assets["child2_nisa_balance"] = (assets["child2_nisa_balance"] + actual) * (1 + c_nisa_return)

                # 自社株購入（奨励金込み）
                company_stock_contribution = month_data["investment"].get("company_stock", 0)
                if company_stock_contribution > 0:
                    actual_purchase = company_stock_contribution * (1 + incentive_rate)
                    shares_purchased = actual_purchase / stock_price
                    assets["company_stock_shares"] += shares_purchased

                # 既存キー（互換性維持）
                for edu_key in ["education_fund"]:
                    edu_contrib = month_data["investment"].get(edu_key, 0)
                    if edu_contrib > 0:
                        monthly_return = self.investment_settings["education_fund"]["expected_return"] / 12
                        assets["education_fund_balance"] = (assets["education_fund_balance"] + edu_contrib) * (1 + monthly_return)

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

            # 大学費用を子供NISA → 教育資金 → 現金の順で支払い
            if university_cost > 0:
                payment_sources = []
                remaining_uni = university_cost

                # 子供ごとに対応するNISAから支払い
                first_child_age_at_now = age - self.basic_info["first_child_birth_age"]
                second_child_age_at_now = age - self.basic_info["second_child_birth_age"]
                if 19 <= first_child_age_at_now <= 22 and assets["child1_nisa_balance"] > 0:
                    c1_used = min(assets["child1_nisa_balance"], remaining_uni)
                    assets["child1_nisa_balance"] -= c1_used
                    remaining_uni -= c1_used
                    if c1_used > 0:
                        payment_sources.append({"source": "子供NISA(第一子)", "amount": c1_used})
                if 19 <= second_child_age_at_now <= 22 and assets["child2_nisa_balance"] > 0:
                    c2_used = min(assets["child2_nisa_balance"], remaining_uni)
                    assets["child2_nisa_balance"] -= c2_used
                    remaining_uni -= c2_used
                    if c2_used > 0:
                        payment_sources.append({"source": "子供NISA(第二子)", "amount": c2_used})

                if remaining_uni > 0:
                    if assets["education_fund_balance"] >= remaining_uni:
                        assets["education_fund_balance"] -= remaining_uni
                        payment_sources.append({"source": "教育資金", "amount": remaining_uni})
                        remaining_uni = 0
                    else:
                        edu_used = assets["education_fund_balance"]
                        remaining_uni -= edu_used
                        assets["education_fund_balance"] = 0
                        if edu_used > 0:
                            payment_sources.append({"source": "教育資金", "amount": edu_used})
                if remaining_uni > 0:
                    assets["cash_balance"] -= remaining_uni
                    payment_sources.append({"source": "現金", "amount": remaining_uni})

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

                # 3) NISA(オルカン)から補填
                if remaining > 0:
                    nisa_used = min(assets["nisa_orcan_balance"], remaining)
                    if nisa_used > 0:
                        assets["nisa_orcan_balance"] -= nisa_used
                        remaining -= nisa_used
                        payment_sources.append({"source": "NISA(オルカン)", "amount": nisa_used})

                # 4) NISA(FANG+)から補填
                if remaining > 0:
                    nisa_used = min(assets["nisa_fang_balance"], remaining)
                    if nisa_used > 0:
                        assets["nisa_fang_balance"] -= nisa_used
                        remaining -= nisa_used
                        payment_sources.append({"source": "NISA(FANG+)", "amount": nisa_used})

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
            assets["total"] = (assets["nisa_orcan_balance"] +
                             assets["nisa_fang_balance"] +
                             assets["nisa_sp500_balance"] +
                             assets["spouse_nisa_orcan_balance"] +
                             assets["spouse_nisa_sp500_balance"] +
                             assets["child1_nisa_balance"] +
                             assets["child2_nisa_balance"] +
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
                "nisa_orcan": assets["nisa_orcan_balance"],
                "nisa_fang": assets["nisa_fang_balance"],
                "nisa_sp500": assets["nisa_sp500_balance"],
                "nisa_cumulative": nisa_cumulative,
                "spouse_nisa_orcan": assets["spouse_nisa_orcan_balance"],
                "spouse_nisa_sp500": assets["spouse_nisa_sp500_balance"],
                "spouse_nisa_cumulative": spouse_nisa_cumulative,
                "child1_nisa": assets["child1_nisa_balance"],
                "child2_nisa": assets["child2_nisa_balance"],
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
        def _prev(key):
            return prev_year_data[key] if prev_year_data else 0

        assets_start = {
            "nisa_orcan": _prev("nisa_orcan"),
            "nisa_fang": _prev("nisa_fang"),
            "nisa_sp500": _prev("nisa_sp500"),
            "spouse_nisa_orcan": _prev("spouse_nisa_orcan"),
            "spouse_nisa_sp500": _prev("spouse_nisa_sp500"),
            "child1_nisa": _prev("child1_nisa"),
            "child2_nisa": _prev("child2_nisa"),
            "company_stock": _prev("company_stock"),
            "education_fund": _prev("education_fund"),
            "marriage_fund": _prev("marriage_fund"),
            "taxable_account": _prev("taxable_account"),
            "cash": _prev("cash"),
            "total": _prev("assets_end")
        }

        # 年末の資産
        assets_end = {
            "nisa_orcan": year_data["nisa_orcan"],
            "nisa_fang": year_data["nisa_fang"],
            "nisa_sp500": year_data["nisa_sp500"],
            "spouse_nisa_orcan": year_data["spouse_nisa_orcan"],
            "spouse_nisa_sp500": year_data["spouse_nisa_sp500"],
            "child1_nisa": year_data["child1_nisa"],
            "child2_nisa": year_data["child2_nisa"],
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
