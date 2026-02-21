"""
シナリオデータベース管理
SQLiteを使用してシナリオ比較データを永続化
"""
import sqlite3
import json
import os
import stat
from datetime import datetime
from pathlib import Path


class ScenarioDatabase:
    """シナリオデータベースクラス"""

    def __init__(self, db_path="data/scenarios.db"):
        """
        初期化

        Args:
            db_path: データベースファイルのパス
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        # DBファイルのパーミッションをオーナーのみ読み書き可に制限
        if self.db_path.exists():
            os.chmod(self.db_path, stat.S_IRUSR | stat.S_IWUSR)

    def _init_database(self):
        """データベースとテーブルを初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scenarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                settings TEXT NOT NULL,
                result_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 実績データテーブル: 月次の実際の収支を記録し計画との乖離を分析
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS actual_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_year  INTEGER NOT NULL,
                record_month INTEGER NOT NULL CHECK(record_month BETWEEN 1 AND 12),
                age          INTEGER NOT NULL,
                income_actual      INTEGER DEFAULT 0,
                expenses_actual    INTEGER DEFAULT 0,
                investment_actual  INTEGER DEFAULT 0,
                cash_balance_actual INTEGER DEFAULT 0,
                notes TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(record_year, record_month)
            )
        """)

        conn.commit()
        conn.close()

    @staticmethod
    def _validate_name(name):
        """シナリオ名のバリデーション（1〜100文字・制御文字禁止）"""
        if not name or not isinstance(name, str):
            return False
        if len(name) < 1 or len(name) > 100:
            return False
        return True

    def save_scenario(self, name, settings, result_data):
        """
        シナリオを保存（既存の場合は更新）

        Args:
            name: シナリオ名
            settings: 設定データ（dict）
            result_data: 計算結果データ（list）

        Returns:
            dict: 保存結果
        """
        if not self._validate_name(name):
            return {"success": False, "error": "シナリオ名は1〜100文字で指定してください"}

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # JSON文字列に変換
            settings_json = json.dumps(settings, ensure_ascii=False)
            result_json = json.dumps(result_data, ensure_ascii=False)

            # 既存チェック
            cursor.execute("SELECT id FROM scenarios WHERE name = ?", (name,))
            existing = cursor.fetchone()

            if existing:
                # 更新
                cursor.execute("""
                    UPDATE scenarios
                    SET settings = ?, result_data = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE name = ?
                """, (settings_json, result_json, name))
            else:
                # 新規挿入
                cursor.execute("""
                    INSERT INTO scenarios (name, settings, result_data)
                    VALUES (?, ?, ?)
                """, (name, settings_json, result_json))

            conn.commit()
            return {"success": True, "message": "シナリオを保存しました"}

        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}

        finally:
            conn.close()

    def load_scenario(self, name):
        """
        シナリオを読み込み

        Args:
            name: シナリオ名

        Returns:
            dict: シナリオデータ（見つからない場合はNone）
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name, settings, result_data, created_at, updated_at
            FROM scenarios
            WHERE name = ?
        """, (name,))

        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "name": row[0],
                "settings": json.loads(row[1]),
                "data": json.loads(row[2]),
                "created_at": row[3],
                "updated_at": row[4]
            }
        return None

    def list_scenarios(self):
        """
        すべてのシナリオをリスト表示

        Returns:
            list: シナリオリスト
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name, created_at, updated_at
            FROM scenarios
            ORDER BY updated_at DESC
        """)

        scenarios = []
        for row in cursor.fetchall():
            scenarios.append({
                "name": row[0],
                "created_at": row[1],
                "updated_at": row[2]
            })

        conn.close()
        return scenarios

    def delete_scenario(self, name):
        """
        シナリオを削除

        Args:
            name: シナリオ名

        Returns:
            dict: 削除結果
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM scenarios WHERE name = ?", (name,))
            conn.commit()

            if cursor.rowcount > 0:
                return {"success": True, "message": "シナリオを削除しました"}
            else:
                return {"success": False, "error": "シナリオが見つかりません"}

        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}

        finally:
            conn.close()

    def get_scenario_summary(self, name):
        """
        シナリオのサマリー情報を取得（データ本体は含まない）

        Args:
            name: シナリオ名

        Returns:
            dict: サマリー情報
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT name, settings, created_at, updated_at
            FROM scenarios
            WHERE name = ?
        """, (name,))

        row = cursor.fetchone()
        conn.close()

        if row:
            settings = json.loads(row[1])
            return {
                "name": row[0],
                "settings": settings,
                "created_at": row[2],
                "updated_at": row[3]
            }
        return None


    # ==================== 実績レコード CRUD ====================

    def save_actual_record(self, record_year, record_month, age,
                           income_actual, expenses_actual, investment_actual,
                           cash_balance_actual, notes=""):
        """
        月次実績を保存（既存の場合は上書き）

        Args:
            record_year:  記録年（例: 2025）
            record_month: 記録月 (1-12)
            age:          その月の年齢
            income_actual:       実際の収入（円）
            expenses_actual:     実際の支出（円）
            investment_actual:   実際の投資（円）
            cash_balance_actual: 月末現金残高（円）
            notes:               メモ

        Returns:
            dict: 保存結果
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO actual_records
                    (record_year, record_month, age,
                     income_actual, expenses_actual, investment_actual,
                     cash_balance_actual, notes, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(record_year, record_month) DO UPDATE SET
                    age=excluded.age,
                    income_actual=excluded.income_actual,
                    expenses_actual=excluded.expenses_actual,
                    investment_actual=excluded.investment_actual,
                    cash_balance_actual=excluded.cash_balance_actual,
                    notes=excluded.notes,
                    updated_at=CURRENT_TIMESTAMP
            """, (record_year, record_month, age,
                  int(income_actual), int(expenses_actual),
                  int(investment_actual), int(cash_balance_actual), notes))
            conn.commit()
            return {"success": True, "message": "実績データを保存しました"}
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()

    def get_all_actual_records(self):
        """
        全実績レコードを取得（年月順）

        Returns:
            list: 実績レコードのリスト
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT record_year, record_month, age,
                   income_actual, expenses_actual, investment_actual,
                   cash_balance_actual, notes, updated_at
            FROM actual_records
            ORDER BY record_year, record_month
        """)
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "year": r[0], "month": r[1], "age": r[2],
                "income_actual": r[3], "expenses_actual": r[4],
                "investment_actual": r[5], "cash_balance_actual": r[6],
                "notes": r[7], "updated_at": r[8]
            }
            for r in rows
        ]

    def delete_actual_record(self, record_year, record_month):
        """
        指定年月の実績を削除

        Args:
            record_year:  記録年
            record_month: 記録月

        Returns:
            dict: 削除結果
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "DELETE FROM actual_records WHERE record_year=? AND record_month=?",
                (int(record_year), int(record_month))
            )
            conn.commit()
            if cursor.rowcount > 0:
                return {"success": True, "message": "実績データを削除しました"}
            return {"success": False, "error": "該当データが見つかりません"}
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()


# テスト用
if __name__ == "__main__":
    db = ScenarioDatabase()
    print("シナリオデータベース初期化完了")
    print(f"データベースパス: {db.db_path}")
