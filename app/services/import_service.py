"""Data import service for historical test data."""
import json
import pandas as pd
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from app.models import sql_models


class DataImportService:
    def __init__(self, db: Session):
        self.db = db

    def import_from_excel(self, file_path: str, data_type: str) -> Dict[str, Any]:
        """Import data from Excel file."""
        try:
            df = pd.read_excel(file_path)
            if data_type == "requirements":
                return self._import_requirements(df)
            elif data_type == "testcases":
                return self._import_testcases(df)
            elif data_type == "defects":
                return self._import_defects(df)
            else:
                raise ValueError(f"Unsupported: {data_type}")
        except Exception as e:
            return {"status": "failed", "error": str(e), "imported": 0}

    def _import_requirements(self, df: pd.DataFrame) -> Dict[str, Any]:
        count = 0
        for _, row in df.iterrows():
            try:
                req = sql_models.RequirementRaw(
                    title=str(row.get('title', '')),
                    full_content=str(row.get('description', '')),
                    source_type='excel'
                )
                self.db.add(req)
                count += 1
            except Exception as e:
                print(f"Failed: {e}")
        self.db.commit()
        return {"status": "success", "imported": count}

    def _import_testcases(self, df: pd.DataFrame) -> Dict[str, Any]:
        count = 0
        for _, row in df.iterrows():
            try:
                steps = json.dumps([str(row.get('steps', ''))], ensure_ascii=False)
                tc = sql_models.TestCase(
                    title=str(row.get('title', '')),
                    steps=steps,
                    expected=str(row.get('expected', '')),
                    status=sql_models.TestCaseStatusEnum.DRAFT
                )
                self.db.add(tc)
                count += 1
            except Exception as e:
                print(f"Failed: {e}")
        self.db.commit()
        return {"status": "success", "imported": count}

    def _import_defects(self, df: pd.DataFrame) -> Dict[str, Any]:
        count = 0
        for _, row in df.iterrows():
            try:
                defect = sql_models.Defect(
                    defect_id=str(row.get('defect_id', f"DEF-{count}")),
                    title=str(row.get('title', ''))
                )
                self.db.add(defect)
                count += 1
            except Exception as e:
                print(f"Failed: {e}")
        self.db.commit()
        return {"status": "success", "imported": count}
