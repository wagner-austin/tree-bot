from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from ..config import Config
from ..services.transform_service import TransformService
from ..services.validate_service import ValidateService
from .container import Container
from .run_manager import start_run
from .steps.sheet_processing import process_sheet
from ..services.output.manifest_writer import write_manifest


@dataclass(frozen=True)
class Orchestrator:
    container: Container
    cfg: Config
    logger: logging.Logger

    def run(
        self,
        input_path: Path,
        classes_path: Path,
        out_dir: Path,
    ) -> int:
        """
        Simple pipeline: normalize headers â†’ transform oldâ†’new â†’ write standardized.xlsx
        """
        run_ctx = start_run(out_dir)
        val: ValidateService = self.container.validate
        tr: TransformService = self.container.transform

        try:
            # 1. Load workbook
            self.logger.info("Loading workbook")
            sheets, skipped = self.container.io.read_results_multi_detailed(input_path)
            self.logger.info(f"Loaded {len(sheets)} sheets")

            if skipped:
                self.logger.warning(f"Skipped {len(skipped)} sheets: {[s.name for s in skipped]}")
                for sk in skipped:
                    self.logger.warning(f"  - {sk.name}: {sk.reason}")

            # 2. Load class map
            class_map = val.load_class_map(classes_path)

            # 3. Load name canonicalization map (optional)
            name_canon_map = None
            canon_path = Path("configs/name_canonicalization.yaml")
            if canon_path.exists():
                from ..services.validation.name_canon import load_name_canon

                name_canon_map = load_name_canon(canon_path)
                self.logger.info(f"Loaded {len(name_canon_map)} name canonicalization rules")

            # 4. Process sheets: normalize headers + transform old→new
            all_processed: dict[str, pd.DataFrame] = {}

            for sheet in sheets:
                self.logger.info(f"Processing sheet: {sheet.name} (schema={sheet.schema})")

                # Normalize headers
                df = process_sheet(val, sheet, self.logger)

                # Transform oldâ†’new if needed
                if sheet.schema == "old":
                    self.logger.info(f"Transforming old→new for sheet: {sheet.name}")
                    result = tr.old_to_new(df, class_map, name_canon_map)
                    df = result.df

                    if not result.unmapped_compounds.empty:
                        self.logger.warning(
                            f"Sheet '{sheet.name}': {len(result.unmapped_compounds)} compounds missing class"
                        )
                        # Show top 5 missing-class compounds for this sheet (skip blanks)
                        um = result.unmapped_compounds
                        if "Compound" in um.columns:
                            um = um[
                                um["Compound"].notna()
                                & (um["Compound"].astype(str).str.strip() != "")
                            ]
                        top_missing = um.head(5)
                        self.logger.warning("Top 5 missing-class compounds:")
                        for _, r in top_missing.iterrows():
                            try:
                                cnt = int(r["count"])
                            except Exception:
                                cnt = 0
                            self.logger.warning(f"  {r['Compound']} ({cnt})")
                    # Old schema does not include Species; we add an empty column so users can fill later
                    if "Species" in df.columns and df["Species"].isna().all():
                        self.logger.info(
                            f"Sheet '{sheet.name}': added empty 'Species' column (old schema)"
                        )

                # Ensure all new schema columns exist (add empty if missing)
                df = self._ensure_new_schema_columns(df)

                # Helper: compute Excel display row from pandas index using sheet offsets
                def _display_row(idx: int) -> int:
                    try:
                        data_start_excel = sheet.header_row_excel + 1
                        return int(idx) - sheet.first_data_index + data_start_excel
                    except Exception:
                        return int(idx) + 2  # fallback

                # Report first five rows with empty Species (per sheet)
                if "Species" in df.columns:
                    s = df["Species"]
                    empty_mask = s.isna() | (s.astype(str).str.strip() == "")
                    if empty_mask.any():
                        idxs = df.index[empty_mask].tolist()
                        self.logger.warning(
                            f"Sheet '{sheet.name}': {len(idxs)} rows with empty Species (showing first 5)"
                        )
                        for i in idxs[:5]:
                            display_row = _display_row(int(i))
                            self.logger.warning(f"  Row {display_row}: Species is empty")
                # Report first five rows with empty CartridgeNum (per sheet)
                if "CartridgeNum" in df.columns:
                    s2 = df["CartridgeNum"]
                    empty2 = s2.isna() | (s2.astype(str).str.strip() == "")
                    if empty2.any():
                        idxs2 = df.index[empty2].tolist()
                        self.logger.warning(
                            f"Sheet '{sheet.name}': {len(idxs2)} rows with empty CartridgeNum (showing first 5)"
                        )
                        for i in idxs2[:5]:
                            display_row = _display_row(int(i))
                            self.logger.warning(f"  Row {display_row}: CartridgeNum is empty")
                # Report first five rows with empty DataFolderName (per sheet)
                if "DataFolderName" in df.columns:
                    s3 = df["DataFolderName"]
                    empty3 = s3.isna() | (s3.astype(str).str.strip() == "")
                    if empty3.any():
                        idxs3 = df.index[empty3].tolist()
                        self.logger.warning(
                            f"Sheet '{sheet.name}': {len(idxs3)} rows with empty DataFolderName (showing first 5)"
                        )
                        for i in idxs3[:5]:
                            display_row = _display_row(int(i))
                            self.logger.warning(f"  Row {display_row}: DataFolderName is empty")
                # Report first five rows with empty Quality columns (per sheet)
                for qcol in ["Match1.Quality", "Match2.Quality", "Match3.Quality"]:
                    if qcol in df.columns:
                        qs = df[qcol]
                        qempty = qs.isna() | (qs.astype(str).str.strip() == "")
                        if qempty.any():
                            idxsq = df.index[qempty].tolist()
                            self.logger.warning(
                                f"Sheet '{sheet.name}': {len(idxsq)} rows with empty {qcol} (showing first 5)"
                            )
                            for i in idxsq[:5]:
                                display_row = _display_row(int(i))
                                self.logger.warning(f"  Row {display_row}: {qcol} is empty")

                all_processed[sheet.name] = df

            # 5. Write standardized workbook (timestamped name)
            if not all_processed:
                self.logger.error("No sheets processed")
                return 1

            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            std_path = run_ctx.run_dir / f"standardized_{ts}.xlsx"
            self.container.io.write_output(all_processed, std_path)
            total_rows = sum(len(df) for df in all_processed.values())
            self.logger.info(
                f"Wrote {std_path.name} ({len(all_processed)} sheets, {total_rows} rows)"
            )
            # Single output only (no duplicate stable name)

            # 7. Write manifest
            started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            finished = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            write_manifest(
                run_dir=run_ctx.run_dir,
                input_path=input_path,
                classes_path=classes_path,
                started_at=started,
                finished_at=finished,
                cfg=self.cfg,
                logger=self.logger,
            )

            self.logger.info("Pipeline completed successfully")
            return 0

        except Exception as e:
            self.logger.error(f"Pipeline failed: {e}", exc_info=True)
            return 3

    def _ensure_new_schema_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Ensure all new schema columns exist (add empty if missing)."""
        required_cols = [
            "DataFolderName",
            "DateRun",
            "CartridgeNum",
            "Species",
            "RetentionTime",
            "Match1",
            "Match1.Quality",
            "Match2",
            "Match2.Quality",
            "Match3",
            "Match3.Quality",
            "Comments",
            "Compound",
            "Class",
            "MatchScore",
        ]

        for col in required_cols:
            if col not in df.columns:
                df[col] = pd.NA

        return df
