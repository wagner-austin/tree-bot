from __future__ import annotations

from typing import TypedDict, Optional, Mapping


class SchemaConfig(TypedDict):
    version: str
    strip_suffixes: list[str]
    aliases: Mapping[str, list[str]]
    old_schema: list[str]
    new_schema: list[str]


class ManifestInputsEntry(TypedDict):
    path: str
    sha256: str


class ManifestInputs(TypedDict):
    results: ManifestInputsEntry
    classes: ManifestInputsEntry


class ManifestParameters(TypedDict):
    certainty_threshold: int
    frequency_min: int
    site_mode: str
    strict_fail: bool
    make_per_species_sheets: bool
    max_errors: int


class ManifestEnvironment(TypedDict):
    python: str
    platform: str
    pandas: str


class Manifest(TypedDict):
    pipeline_version: str
    started_at: str
    finished_at: str
    inputs: ManifestInputs
    parameters: ManifestParameters
    environment: ManifestEnvironment


class ConfigOverrides(TypedDict, total=False):
    pipeline_version: str
    certainty_threshold: int
    frequency_min: int
    site_mode: str
    strict_fail: bool
    make_per_species_sheets: bool
    max_errors: int
    pipeline_stage: str


class YamlConfig(TypedDict, total=False):
    pipeline_version: str
    certainty_threshold: int
    frequency_min: int
    site_mode: str
    strict_fail: bool
    make_per_species_sheets: bool
    max_errors: int
    pipeline_stage: str


class ForwardFillCounts(TypedDict):
    DataFolderName: int
    CartridgeNum: int


class ForwardFillExamples(TypedDict):
    DataFolderName: list[int]
    CartridgeNum: list[int]


class ForwardFillValues(TypedDict):
    DataFolderName: list[str]
    CartridgeNum: list[str]


class SectionStats(TypedDict):
    unique_compounds: int
    total_peaks: int
    unique_compounds_all: int
    peaks_all: int
