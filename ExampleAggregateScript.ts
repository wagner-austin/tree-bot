function main(workbook: ExcelScript.Workbook) {
  const NOW: string = new Date().toISOString();
  const LOG = getOrCreateAppendTable(workbook, "Log",
    ["run_id", "module", "level", "code", "message", "table_or_sheet", "row_ref", "key", "extra"]);
  const STATS = getOrCreateAppendTable(workbook, "Stats",
    ["run_id", "module", "metric", "value"]);
  const PROV = ensureSheet(workbook, "Provenance");
  const params = readParamsStrict(workbook);

  // ---------- Types ----------
  type Group = {
    speciesDisp: string;
    compoundDispCanon: string;
    classDisp: string;
    rt: number[];
    ms: number[];
    sites: Set<string>;
    comments: Set<string>;
    totalCount: number;
    siteCounts: Map<string, number>;
  };

  type SummaryRow = [
    string,  // Species
    string,  // Compound (canonical)
    string,  // Class
    number,  // N_Observations (total)
    number,  // N_Sites
    string,  // Sites
    number,  // RT_Median
    number,  // RetentionMin
    number,  // RetentionMax
    number,  // RTrange
    number,  // Certainty_Mean
    string   // Comments
  ];

  type SiteSpeciesRow = [
    number,  // RetentionMin
    number,  // RetentionMax
    number,  // RTrange
    string,  // CompoundClass
    string,  // CompoundName (canonical)
    number,  // N_Observations_Total
    number,  // N_Observations_Site
    number,  // N_Sites
    string,  // Sites
    string   // Comments
  ];

  // ---------- Clean existing Out_* ----------
  workbook.getWorksheets().forEach((ws) => { if (ws.getName().startsWith("Out_")) ws.delete(); });

  // ---------- Read optional maps ----------
  const canonMap = readCanonicalMap(workbook);                 // Map<normalizedFrom, toDisplay>
  const classMap = readClassMap(workbook);                     // Map<normalizedCanonicalName, classDisp>
  const canonRules = canonMap.size;
  const classRules = classMap.size;

  // For reports
  const canonCounts: Map<string, number> = new Map(); // "Raw -> Canonical" count
  const unmappedClasses: Set<string> = new Set();     // canonical names with no class
  const classConflicts: Array<{ compound: string; dataClass: string; mapClass: string }> = [];

  // ---------- Aggregate ----------
  const agg: Map<string, Group> = new Map();
  let tablesScanned = 0, rowsIn = 0, rowsKept = 0, canonChanged = 0;

  const tables = workbook.getTables().filter(t => t.getName().startsWith(params.tablePrefix));
  if (tables.length === 0) throw new Error(`No tables found with prefix "${params.tablePrefix}".`);

  for (const t of tables) {
    tablesScanned++;
    const siteFromSheet = t.getWorksheet().getName();
    const vals = t.getRange().getValues();
    if (vals.length < 2) continue;

    const header = vals[0].map(v => String(v).trim());
    const h = header.map(x => x.toLowerCase());
    const idx = (col: string) => h.indexOf(col.toLowerCase());

    const iSpecies = idx("species");
    const iComp = idx("compound");
    const iClass = idx("class");       // optional
    const iRT = idx("retentiontime");
    const iMS = idx("matchscore");
    const iCmt = idx("comments");    // optional
    const iSiteCol = idx("site");        // only if site_mode=column

    if (iSpecies < 0 || iComp < 0 || iRT < 0 || iMS < 0) {
      throw new Error(`Missing required columns in table "${t.getName()}".`);
    }

    for (let r = 1; r < vals.length; r++) {
      rowsIn++;
      const row = vals[r];

      const species = row[iSpecies];
      const compoundRaw = row[iComp];
      const rt = Number(row[iRT]);
      const ms = Number(row[iMS]);
      if (species === null || species === "" || compoundRaw === null || compoundRaw === "") continue;
      if (Number.isNaN(rt) || Number.isNaN(ms)) continue;
      if (ms < params.certaintyThreshold) continue;

      rowsKept++;

      const siteName = (params.siteMode === "column")
        ? String(row[iSiteCol] ?? "").trim()
        : siteFromSheet;
      if (params.siteMode === "column" && !siteName) {
        throw new Error(`Blank Site value (site_mode=column) in table "${t.getName()}", row ${r + 1}.`);
      }

      const spDisp = String(species).trim();

      // Canonicalize display + key
      const compCleanDisplay = tidyDisplay(String(compoundRaw));
      const compNormBase = normalizeCompound(String(compoundRaw));
      let compDispCanon = compCleanDisplay;
      const mapped = canonMap.get(compNormBase);
      if (mapped) {
        compDispCanon = mapped;
        if (mapped.toLowerCase() !== compCleanDisplay.toLowerCase()) {
          canonChanged++;
          const k = `${compCleanDisplay} -> ${mapped}`;
          canonCounts.set(k, (canonCounts.get(k) ?? 0) + 1);
        }
      } else if (compCleanDisplay !== String(compoundRaw).trim()) {
        const k2 = `${String(compoundRaw).trim()} -> ${compCleanDisplay}`;
        canonCounts.set(k2, (canonCounts.get(k2) ?? 0) + 1);
      }
      const compNormKey = mapped ? normalizeCompound(mapped) : compNormBase;

      // Class resolution (data column > map). Read-only; we don't write back.
      const classFromData = (iClass >= 0 && row[iClass] !== null && row[iClass] !== "")
        ? String(row[iClass]).trim()
        : "";
      const classFromMap = classMap.get(compNormKey) ?? "";
      let classDisp = classFromData || classFromMap;

      if (classFromData && classFromMap && classFromData.toLowerCase() !== classFromMap.toLowerCase()) {
        classConflicts.push({ compound: compDispCanon, dataClass: classFromData, mapClass: classFromMap });
      }
      if (!classDisp) {
        // No class at all
        if (params.requireFullClassCoverage) unmappedClasses.add(compDispCanon);
        // else leave empty for output
      }

      const cmt = (iCmt >= 0 && row[iCmt] !== null) ? String(row[iCmt]).trim() : "";
      const key = normalizeSpecies(spDisp) + "||" + compNormKey;

      if (!agg.has(key)) {
        agg.set(key, {
          speciesDisp: spDisp,
          compoundDispCanon: compDispCanon,
          classDisp: classDisp,
          rt: [],
          ms: [],
          sites: new Set<string>(),
          comments: new Set<string>(),
          totalCount: 0,
          siteCounts: new Map<string, number>()
        });
      }
      const g = agg.get(key)!;
      g.totalCount += 1;
      g.rt.push(rt);
      g.ms.push(ms);
      g.sites.add(siteName);
      if (!g.classDisp && classDisp) g.classDisp = classDisp; // fill if still blank
      if (cmt) g.comments.add(cmt);
      g.siteCounts.set(siteName, (g.siteCounts.get(siteName) ?? 0) + 1);
    }
  }

  // If strict class coverage required, report + fail before writing outputs
  if (params.requireFullClassCoverage && (unmappedClasses.size > 0 || classConflicts.length > 0)) {
    writeClassIssues(workbook, unmappedClasses, classConflicts);
    appendRow(LOG, [NOW, "30_Filter_Aggregate", "ERROR", "E-CLASS-COVERAGE",
      `Missing or conflicting class mappings. See Class_Issues.`, "", "", "", ""]);
    appendRow(STATS, [NOW, "30_Filter_Aggregate", "class_unmapped", unmappedClasses.size]);
    appendRow(STATS, [NOW, "30_Filter_Aggregate", "class_conflicts", classConflicts.length]);
    throw new Error(`Class coverage check failed: ${unmappedClasses.size} unmapped, ${classConflicts.length} conflicts. See "Class_Issues".`);
  }

  // ---------- Build global Summary (global frequency filter) ----------
  const rows: SummaryRow[] = [];
  const perSiteSpecies: Map<string, Map<string, SiteSpeciesRow[]>> = new Map();

  agg.forEach((g) => {
    if (g.totalCount < params.frequencyMin) return;

    const rtMin = min(g.rt);
    const rtMax = max(g.rt);
    const rtMedian = median(g.rt);
    const rtRange = (Number.isNaN(rtMin) || Number.isNaN(rtMax)) ? NaN : (rtMax - rtMin);
    const msMean = mean(g.ms);
    const nSites = g.sites.size;
    const sitesList = Array.from(g.sites).sort((a, b) => a.localeCompare(b)).join(", ");
    const commentsMerged = Array.from(g.comments).filter((x) => Boolean(x)).join(" | ");

    rows.push([
      g.speciesDisp, g.compoundDispCanon, g.classDisp || "",
      g.totalCount, nSites, sitesList,
      rtMedian, rtMin, rtMax, rtRange, msMean,
      commentsMerged
    ]);

    g.siteCounts.forEach((siteCount, siteName) => {
      if (siteCount <= 0) return;
      const rowForSite: SiteSpeciesRow = [
        rtMin, rtMax, rtRange,
        g.classDisp || "",
        g.compoundDispCanon,
        g.totalCount,
        siteCount,
        nSites,
        sitesList,
        commentsMerged
      ];
      if (!perSiteSpecies.has(siteName)) perSiteSpecies.set(siteName, new Map<string, SiteSpeciesRow[]>());
      const bySpecies = perSiteSpecies.get(siteName)!;
      if (!bySpecies.has(g.speciesDisp)) bySpecies.set(g.speciesDisp, []);
      bySpecies.get(g.speciesDisp)!.push(rowForSite);
    });
  });

  if (rows.length === 0) {
    throw new Error(`No compounds met filters (threshold=${params.certaintyThreshold}, frequency_min=${params.frequencyMin}).`);
  }

  // ---------- Write Summary ----------
  rows.sort((A, B) =>
    A[0] !== B[0] ? (A[0] < B[0] ? -1 : 1)
      : (A[3] !== B[3] ? B[3] - A[3]
        : (A[1] < B[1] ? -1 : (A[1] > B[1] ? 1 : 0)))
  );

  const headers = [
    "Species", "Compound", "Class", "N_Observations", "N_Sites", "Sites",
    "RT_Median", "RetentionMin", "RetentionMax", "RTrange", "Certainty_Mean", "Comments"
  ];
  let sumWs = workbook.getWorksheet("Summary");
  if (!sumWs) sumWs = workbook.addWorksheet("Summary"); else sumWs.getUsedRange()?.clear(ExcelScript.ClearApplyTo.all);
  const out = [headers, ...rows];
  const rng = sumWs.getRangeByIndexes(0, 0, out.length, headers.length);
  rng.setValues(out);
  sumWs.addTable(rng.getAddress(), true).setName("SummaryTable");

  // ---------- One Out_<Site> sheet per site with all species blocks ----------
  const siteNamesSorted = Array.from(perSiteSpecies.keys()).sort((a, b) => a.localeCompare(b));
  let outSheets = 0;

  siteNamesSorted.forEach((siteName) => {
    const speciesMap = perSiteSpecies.get(siteName)!;
    const speciesSorted = Array.from(speciesMap.keys()).sort((a, b) => a.localeCompare(b));

    const desiredName = "Out_" + safeSheetName(siteName);
    let ws = workbook.getWorksheet(desiredName);
    if (ws) { ws.getUsedRange()?.clear(ExcelScript.ClearApplyTo.all); }
    else { ws = workbook.addWorksheet(desiredName); }
    outSheets++;

    ws.getRange("A1").setValue(`Site: ${siteName}`);
    ws.getRange("A1").getFormat().getFont().setBold(true);

    let curRow = 2;
    const spHeaders = [
      "RetentionMin", "RetentionMax", "RTrange", "CompoundClass", "CompoundName",
      "N_Observations_Total", "N_Observations_Site", "N_Sites", "Sites", "Comments"
    ];

    speciesSorted.forEach((spDisp) => {
      const rowsForSpecies = speciesMap.get(spDisp)!;
      rowsForSpecies.sort((A, B) =>
        A[0] !== B[0] ? A[0] - B[0] : (A[4] < B[4] ? -1 : (A[4] > B[4] ? 1 : 0))
      );

      ws.getRangeByIndexes(curRow, 0, 1, 1).setValue(`Species: ${spDisp} — ${rowsForSpecies.length} peaks`);
      ws.getRangeByIndexes(curRow, 0, 1, 1).getFormat().getFont().setBold(true);
      curRow += 2;

      const tableData = [spHeaders, ...rowsForSpecies];
      const r = ws.getRangeByIndexes(curRow, 0, tableData.length, spHeaders.length);
      r.setValues(tableData);
      ws.addTable(r.getAddress(), true);
      curRow += tableData.length + 2;
    });
  });

  // ---------- Reports + Provenance + Stats + Log ----------
  writeCanonicalizationReport(workbook, canonCounts);

  writeProvenance(PROV, [
    ["Run timestamp (UTC)", NOW],
    ["pipeline_version", params.pipelineVersion],
    ["certainty_threshold", String(params.certaintyThreshold)],
    ["frequency_min", String(params.frequencyMin)],
    ["site_mode", params.siteMode],
    ["tables_scanned", String(tablesScanned)],
    ["rows_considered", String(rowsIn)],
    ["rows_after_threshold", String(rowsKept)],
    ["groups_after_frequency", String(rows.length)],
    ["canonical_map_rules", String(canonRules)],
    ["names_canonicalized", String(canonChanged)],
    ["class_map_rules", String(classRules)],
    ["require_full_class_coverage", String(params.requireFullClassCoverage)],
    ["normalization", "lowercase, trim, collapse whitespace, α→alpha, β→beta, unify comma/hyphen spacing, strip trailing punctuation/hyphen"],
    ["grouping_key", "(Species, Canonical Compound) after normalization"]
  ]);
  appendRow(STATS, [NOW, "30_Filter_Aggregate", "rows_considered", rowsIn]);
  appendRow(STATS, [NOW, "30_Filter_Aggregate", "rows_after_threshold", rowsKept]);
  appendRow(STATS, [NOW, "30_Filter_Aggregate", "groups_after_frequency", rows.length]);
  appendRow(STATS, [NOW, "30_Filter_Aggregate", "canonical_map_rules", canonRules]);
  appendRow(STATS, [NOW, "30_Filter_Aggregate", "names_canonicalized", canonChanged]);
  appendRow(STATS, [NOW, "30_Filter_Aggregate", "class_map_rules", classRules]);
  appendRow(LOG, [NOW, "30_Filter_Aggregate", "INFO", "I-OK", "Aggregation complete (with canonicalization + class map)", "", "", "", ""]);

  // ---------- Helpers ----------
  function ensureSheet(workbookRef: ExcelScript.Workbook, name: string): ExcelScript.Worksheet {
    let ws = workbookRef.getWorksheet(name);
    if (!ws) ws = workbookRef.addWorksheet(name);
    return ws;
  }

  function writeProvenance(ws: ExcelScript.Worksheet, kv: [string, string][]): void {
    ws.getUsedRange()?.clear(ExcelScript.ClearApplyTo.all);
    ws.getRangeByIndexes(0, 0, 1, 2).setValues([["Provenance", ""]]);
    ws.getRange("A1:B1").getFormat().getFont().setBold(true);
    ws.getRangeByIndexes(1, 0, kv.length, 2).setValues(kv);
  }

  function writeCanonicalizationReport(workbookRef: ExcelScript.Workbook, counts: Map<string, number>): void {
    let ws = workbookRef.getWorksheet("Canonicalization_Report");
    if (!ws) ws = workbookRef.addWorksheet("Canonicalization_Report"); else ws.getUsedRange()?.clear(ExcelScript.ClearApplyTo.all);
    const rowsArr: (string | number | boolean)[][] = [["RawName → CanonicalName", "Count"]];
    Array.from(counts.entries())
      .sort((a, b) => b[1] - a[1])
      .forEach(([pair, c]) => rowsArr.push([pair, c]));
    const rng = ws.getRangeByIndexes(0, 0, rowsArr.length, 2);
    rng.setValues(rowsArr);
    ws.addTable(rng.getAddress(), true);
  }

  function writeClassIssues(
    workbookRef: ExcelScript.Workbook,
    unmapped: Set<string>,
    conflicts: Array<{ compound: string; dataClass: string; mapClass: string }>
  ): void {
    let ws = workbookRef.getWorksheet("Class_Issues");
    if (!ws) ws = workbookRef.addWorksheet("Class_Issues"); else ws.getUsedRange()?.clear(ExcelScript.ClearApplyTo.all);

    const a: (string | number | boolean)[][] = [["Issue", "Compound", "DataClass", "MapClass"]];
    unmapped.forEach((c) => a.push(["UNMAPPED", c, "", ""]));
    conflicts.forEach((x) => a.push(["CONFLICT", x.compound, x.dataClass, x.mapClass]));

    const rng = ws.getRangeByIndexes(0, 0, a.length, 4);
    rng.setValues(a);
    ws.addTable(rng.getAddress(), true);
  }

  function normalizeSpecies(s: string): string {
    return String(s).trim().replace(/\s+/g, " ").toLowerCase();
  }

  function normalizeCompound(s: string): string {
    let t = String(s);
    const G: Record<string, string> = {
      "α": "alpha", "β": "beta", "γ": "gamma", "δ": "delta", "ε": "epsilon",
      "ζ": "zeta", "η": "eta", "θ": "theta", "ι": "iota", "κ": "kappa",
      "λ": "lambda", "μ": "mu", "ν": "nu", "ξ": "xi", "ο": "omicron",
      "π": "pi", "ρ": "rho", "σ": "sigma", "τ": "tau", "υ": "upsilon",
      "φ": "phi", "χ": "chi", "ψ": "psi", "ω": "omega"
    };
    Object.entries(G).forEach(([g, latin]) => { t = t.split(g).join(latin); });
    t = t.replace(/\u2013|\u2014/g, "-");
    t = t.replace(/\s*,\s*/g, ", ");
    t = t.replace(/\s*-\s*/g, "-");
    t = t.replace(/[,\-;:]+$/g, "");
    t = t.trim().replace(/\s+/g, " ").toLowerCase();
    return t;
  }

  function tidyDisplay(s: string): string {
    let t = String(s).trim();
    t = t.replace(/\u2013|\u2014/g, "-");
    t = t.replace(/\s*,\s*/g, ", ");
    t = t.replace(/\s*-\s*/g, "-");
    t = t.replace(/[,\-;:]+$/g, "");
    t = t.replace(/\s+/g, " ").trim();
    return t;
  }

  function median(a: number[]): number {
    const b = a.filter((x) => !Number.isNaN(x)).sort((x, y) => x - y);
    const n = b.length; if (!n) return NaN;
    const m = Math.floor(n / 2);
    return n % 2 ? b[m] : (b[m - 1] + b[m]) / 2;
  }
  function mean(a: number[]): number {
    const b = a.filter((x) => !Number.isNaN(x));
    return b.length ? b.reduce((p, c) => p + c, 0) / b.length : NaN;
  }
  function min(a: number[]): number {
    const b = a.filter((x) => !Number.isNaN(x));
    return b.length ? Math.min(...b) : NaN;
  }
  function max(a: number[]): number {
    const b = a.filter((x) => !Number.isNaN(x));
    return b.length ? Math.max(...b) : NaN;
  }
  function safeSheetName(name: string): string {
    const cleaned = name.replace(/[\[\]\*\?:\/\\]/g, "-");
    return cleaned.length > 31 ? cleaned.slice(0, 31) : cleaned;
  }

  function getOrCreateAppendTable(
    workbookRef: ExcelScript.Workbook,
    sheetName: string,
    headers: string[]
  ): ExcelScript.Table {
    let ws = workbookRef.getWorksheet(sheetName);
    if (!ws) {
      ws = workbookRef.addWorksheet(sheetName);
      const range = ws.getRangeByIndexes(0, 0, 1, headers.length);
      range.setValues([headers]);
      return ws.addTable(range.getAddress(), true);
    }
    const existing = ws.getTables();
    if (existing.length === 0) {
      const range = ws.getRangeByIndexes(0, 0, 1, headers.length);
      range.setValues([headers]);
      return ws.addTable(range.getAddress(), true);
    }
    return existing[0];
  }
  function appendRow(tbl: ExcelScript.Table, values: (string | number | boolean)[]): void {
    const rowVals = values.map((v) => (v === undefined || v === null) ? "" : v);
    tbl.addRow(-1, rowVals);
  }

  // ---- Params & Maps ----
  function readParamsStrict(workbookRef: ExcelScript.Workbook) {
    const ws = workbookRef.getWorksheet("Parameters");
    if (!ws) throw new Error(`Parameters sheet not found.`);
    const ur = ws.getUsedRange(); if (!ur) throw new Error(`Parameters sheet is empty.`);
    const vals = ur.getValues();
    if (vals.length < 2 || vals[0].length < 2) throw new Error(`Parameters sheet must have headers "key | value".`);
    const header = vals[0].map((v) => String(v).trim().toLowerCase());
    if (header[0] !== "key" || header[1] !== "value") throw new Error(`Parameters sheet must have headers "key | value".`);
    const map = new Map<string, string>();
    for (let r = 1; r < vals.length; r++) {
      const k = String(vals[r][0] ?? "").trim().toLowerCase();
      const v = String(vals[r][1] ?? "").trim();
      if (k) map.set(k, v);
    }
    const get = (k: string, req = true): string => {
      if (!map.has(k)) { if (req) throw new Error(`Parameters missing key: ${k}`); else return ""; }
      return map.get(k)!;
    };
    const toBool = (s: string): boolean => /^(true|1|yes)$/i.test(s);
    const toNum = (s: string, name: string): number => {
      const n = Number(s);
      if (Number.isNaN(n)) throw new Error(`Parameter "${name}" not numeric: ${s}`);
      return n;
    };

    const certaintyThreshold = toNum(get("certainty_threshold"), "certainty_threshold");
    const frequencyMin = Math.trunc(toNum(get("frequency_min"), "frequency_min"));
    const tablePrefix = get("table_name_prefix");
    const siteModeRaw = get("site_mode").toLowerCase();
    if (!["sheetname", "column"].includes(siteModeRaw)) throw new Error(`site_mode must be "sheetname" or "column".`);
    const strictFail = toBool(get("strict_fail"));
    const makePerSpeciesSheets = /^(true|1|yes)$/i.test(get("make_per_species_sheets", false));
    const pipelineVersion = get("pipeline_version", false) || "";
    const requireFullClassCoverage = toBool(get("require_full_class_coverage", false));

    return {
      certaintyThreshold,
      frequencyMin,
      tablePrefix,
      siteMode: siteModeRaw as "sheetname" | "column",
      strictFail,
      makePerSpeciesSheets,
      pipelineVersion,
      requireFullClassCoverage
    };
  }

  function readCanonicalMap(workbookRef: ExcelScript.Workbook): Map<string, string> {
    const ws = workbookRef.getWorksheet("CanonicalMap");
    const m: Map<string, string> = new Map();
    if (!ws) return m;
    const ur = ws.getUsedRange(); if (!ur) return m;
    const vals = ur.getValues(); if (vals.length < 2) return m;
    const header = vals[0].map((v) => String(v).trim().toLowerCase());
    const iFrom = header.indexOf("from"), iTo = header.indexOf("to");
    if (iFrom < 0 || iTo < 0) throw new Error(`CanonicalMap must have headers: From | To`);
    const seen: Map<string, string> = new Map();
    for (let r = 1; r < vals.length; r++) {
      const fromRaw = vals[r][iFrom], toRaw = vals[r][iTo];
      if (!fromRaw || !toRaw) throw new Error(`CanonicalMap row ${r + 1}: blank From/To not allowed.`);
      const fromNorm = normalizeCompound(String(fromRaw));
      const toDisp = tidyDisplay(String(toRaw));
      if (seen.has(fromNorm) && seen.get(fromNorm)!.toLowerCase() !== toDisp.toLowerCase()) {
        throw new Error(`CanonicalMap conflict for "${fromRaw}": maps to both "${seen.get(fromNorm)}" and "${toDisp}".`);
      }
      seen.set(fromNorm, toDisp);
      m.set(fromNorm, toDisp);
    }
    return m;
  }

  function readClassMap(workbookRef: ExcelScript.Workbook): Map<string, string> {
    const ws = workbookRef.getWorksheet("CompoundClassMap");
    const m: Map<string, string> = new Map();
    if (!ws) return m; // optional but recommended; strict can enforce coverage
    const ur = ws.getUsedRange(); if (!ur) return m;
    const vals = ur.getValues(); if (vals.length < 2) return m;
    const header = vals[0].map((v) => String(v).trim().toLowerCase());
    const iName = header.indexOf("compound_name"), iClass = header.indexOf("compound_class");
    if (iName < 0 || iClass < 0) throw new Error(`CompoundClassMap must have headers: compound_name | compound_class`);
    for (let r = 1; r < vals.length; r++) {
      const nRaw = vals[r][iName], cRaw = vals[r][iClass];
      if (!nRaw || !cRaw) throw new Error(`CompoundClassMap row ${r + 1}: blank name/class not allowed.`);
      const key = normalizeCompound(String(nRaw)); // match on canonicalized key
      const cls = String(cRaw).trim();
      m.set(key, cls);
    }
    return m;
  }
}
