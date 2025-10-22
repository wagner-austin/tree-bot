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
        mapping_path: Path | None,
        out_dir: Path,
    ) -> int:
        """
        Simple pipeline: normalize headers ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ transform oldÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢new ÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢ write standardized.xlsx
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
            # 2b. Load species map (optional)
            species_map: dict[tuple[str, str], str] | None = None
            if mapping_path is not None:
                try:
                    species_map, _amb = val.load_species_map(mapping_path)
                except Exception as e:
                    self.logger.warning(
                        f"Failed to load species map: {e}", extra={"path": str(mapping_path)}
                    )

            # 3. Process sheets: normalize headers + transform oldÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â€šÂ¬Ã‚Â ÃƒÂ¢Ã¢â€šÂ¬Ã¢â€žÂ¢new
            all_processed: dict[str, pd.DataFrame] = {}

            for sheet in sheets:
                self.logger.info(f"Processing sheet: {sheet.name} (schema={sheet.schema})")

                # Normalize headers
                df = process_sheet(val, sheet, self.logger, species_map)

                # Transform oldÃƒÆ’Ã†â€™Ãƒâ€šÃ‚Â¢ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬Ãƒâ€šÃ‚Â ÃƒÆ’Ã‚Â¢ÃƒÂ¢Ã¢â‚¬Å¡Ã‚Â¬ÃƒÂ¢Ã¢â‚¬Å¾Ã‚Â¢new if needed
                if sheet.schema == "old":
                    self.logger.info(f"Transforming old->new for sheet: {sheet.name}")
                    result = tr.old_to_new(df, class_map)
                    df = result.df

                    # Normalization summary: Match1 -> Compound changes
                    try:
                        if "Match1" in df.columns and "Compound" in df.columns:
                            mask = df["Match1"].notna() & df["Compound"].notna()
                            diffs = df.loc[
                                mask
                                & (
                                    df["Match1"].astype(str).str.strip()
                                    != df["Compound"].astype(str)
                                ),
                                ["Match1", "Compound"],
                            ]
                            n_norm = len(diffs)
                            if n_norm:
                                self.logger.info(
                                    f"Sheet '{sheet.name}': normalized {n_norm} compound names (showing first 5)"
                                )
                                top = diffs.value_counts().head(5)
                                for (raw, comp), cnt in top.items():
                                    self.logger.info(f"  '{raw}' -> '{comp}' ({int(cnt)})")
                    except Exception:
                        pass

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
                        top_missing = um.head(20)
                        self.logger.warning(f"Top {len(top_missing)} missing-class compounds:")
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
