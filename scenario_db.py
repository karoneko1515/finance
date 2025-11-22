"""
シナリオデータベース管理
SQLiteを使用してシナリオ比較データを永続化
"""
import sqlite3
import json
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

        conn.commit()
        conn.close()

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


# テスト用
if __name__ == "__main__":
    db = ScenarioDatabase()
    print("シナリオデータベース初期化完了")
    print(f"データベースパス: {db.db_path}")
