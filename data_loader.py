"""
データローダー
JSONファイルから設定を読み込み、Pythonデータ構造として提供
"""
import json
import os
from pathlib import Path


class DataLoader:
    """ライフプラン設定データのローダー"""

    def __init__(self, config_dir=None):
        """
        初期化

        Args:
            config_dir: 設定ファイルのディレクトリ（Noneの場合は自動検出）
        """
        if config_dir is None:
            # スクリプトの場所から相対パスで config ディレクトリを探す
            script_dir = Path(__file__).parent
            config_dir = script_dir / "config"

        self.config_dir = Path(config_dir)
        self.default_plan_path = self.config_dir / "default_plan.json"
        self.user_plan_path = self.config_dir / "user_plan.json"

        self.plan_data = None
        self.load_plan()

    def load_plan(self, use_user_plan=True):
        """
        プラン設定を読み込み

        Args:
            use_user_plan: ユーザー設定を優先するか（存在する場合）
        """
        # ユーザー設定が存在し、優先する場合はそちらを読み込み
        if use_user_plan and self.user_plan_path.exists():
            with open(self.user_plan_path, 'r', encoding='utf-8') as f:
                self.plan_data = json.load(f)
        else:
            # デフォルト設定を読み込み
            with open(self.default_plan_path, 'r', encoding='utf-8') as f:
                self.plan_data = json.load(f)

    def save_user_plan(self, plan_data):
        """
        ユーザー設定を保存

        Args:
            plan_data: 保存するプランデータ
        """
        with open(self.user_plan_path, 'w', encoding='utf-8') as f:
            json.dump(plan_data, f, ensure_ascii=False, indent=2)

        self.plan_data = plan_data

    def reset_to_default(self):
        """デフォルト設定に戻す"""
        if self.user_plan_path.exists():
            os.remove(self.user_plan_path)
        self.load_plan(use_user_plan=False)

    def get_basic_info(self):
        """基本情報を取得"""
        return self.plan_data.get("basic_info", {})

    def get_life_events(self):
        """ライフイベント情報を取得"""
        return self.plan_data.get("life_events", {})

    def get_income_progression(self):
        """年齢別収入情報を取得"""
        return self.plan_data.get("income_progression", {})

    def get_spouse_income(self):
        """配偶者収入情報を取得"""
        return self.plan_data.get("spouse_income", {})

    def get_pension(self):
        """年金情報を取得"""
        return self.plan_data.get("pension", {})

    def get_housing_allowance(self):
        """家賃補助情報を取得"""
        return self.plan_data.get("housing_allowance", {})

    def get_housing_costs(self):
        """住居費情報を取得"""
        return self.plan_data.get("housing_costs", {})

    def get_phase_definitions(self):
        """フェーズ定義を取得"""
        return self.plan_data.get("phase_definitions", {})

    def get_child_allowance(self):
        """児童手当情報を取得"""
        return self.plan_data.get("child_allowance", {})

    def get_high_school_subsidy(self):
        """高校無償化補助を取得"""
        return self.plan_data.get("high_school_subsidy", 0)

    def get_education_costs(self):
        """教育費情報を取得"""
        return self.plan_data.get("education_costs_per_child", {})

    def get_pet_costs(self):
        """ペット費用を取得"""
        return self.plan_data.get("pet_costs", {})

    def get_investment_plan(self):
        """投資プラン（NISA枠管理・オルカン/FANG+/自社株配分）を取得"""
        return self.plan_data.get("investment_plan", {})

    def get_investment_settings(self):
        """投資設定を取得"""
        return self.plan_data.get("investment_settings", {})

    def get_tax_rates(self):
        """税率情報を取得"""
        return self.plan_data.get("tax_rates", {})

    def get_mortgage_deduction(self):
        """住宅ローン控除情報を取得"""
        return self.plan_data.get("mortgage_deduction", {})

    def get_inflation_settings(self):
        """インフレ設定を取得"""
        return self.plan_data.get("inflation_settings", {})

    def get_emergency_reserve(self):
        """緊急予備資金額を取得"""
        return self.plan_data.get("emergency_reserve", 3000000)

    def get_scenario_settings(self):
        """シナリオ設定を取得"""
        return self.plan_data.get("scenario_settings", {})

    def get_all_data(self):
        """全データを取得"""
        return self.plan_data


# テスト用
if __name__ == "__main__":
    loader = DataLoader()
    print("基本情報:", loader.get_basic_info())
    print("\nライフイベント:", loader.get_life_events())
    print("\n投資設定:", loader.get_investment_settings())
