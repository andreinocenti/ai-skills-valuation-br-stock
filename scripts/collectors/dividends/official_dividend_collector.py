#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from collectors.dividends.aggregator_dividend_scraper import scrape_aggregator_dividends
from collectors.dividends.b3_cash_dividend_form_collector import collect_b3_cash_dividends, discover_b3_documents
from collectors.dividends.brapi_free_dividend_collector import collect_brapi_free_dividends
from collectors.dividends.cvm_ipe_dividend_collector import collect_cvm_ipe_dividends, discover_cvm_ipe_documents
from collectors.dividends.dividend_reconciler import reconcile_dividend_events
from collectors.dividends.ri_dividend_collector import collect_ri_dividends, discover_ri_dividend_documents
from config_loader import data_source_flag


class OfficialDividendCollector:
    def _cache_root(self, cache_dir: str | Path | None) -> Path:
        base = Path(cache_dir).expanduser() if cache_dir else (Path.home() / ".valuation-stock-br" / "cache")
        return base / "cvm_ipe"

    def _write_cache(self, cache_root: Path, bucket: str, name: str, payload: Any) -> None:
        path = cache_root / bucket / name
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(payload, bytes):
                path.write_bytes(payload)
            elif isinstance(payload, str):
                path.write_text(payload, encoding="utf-8")
            else:
                path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        except OSError:
            return

    def _coerce_documents(self, raw_documents: list[Any] | None, default_type: str) -> list[dict[str, Any]]:
        documents = []
        for index, raw in enumerate(raw_documents or []):
            if isinstance(raw, dict):
                item = dict(raw)
            else:
                item = {"url": str(raw), "text": ""}
            item.setdefault("id", f"{default_type.lower()}-{index + 1}")
            item.setdefault("document_type", default_type)
            documents.append(item)
        return documents

    def _summary(self, result: dict[str, Any], source_urls: list[str] | None = None) -> dict[str, Any]:
        return {
            "attempted": True,
            "succeeded": bool(result.get("events")),
            "events_found": len(result.get("events", [])),
            "warnings": list(result.get("warnings") or []),
            "source_urls": [url for url in (source_urls or []) if url],
        }

    def _discover_documents(
        self,
        ticker: str,
        company_profile: dict[str, Any],
        cache_dir: str | Path | None,
        years: list[int],
        test_overrides: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
        cvm_discovery = (
            {"documents": self._coerce_documents(test_overrides.get("cvm_documents"), "Aviso aos Acionistas"), "warnings": [], "source_urls": []}
            if "cvm_documents" in test_overrides
            else discover_cvm_ipe_documents(ticker, company_profile, years, cache_dir)
        )
        b3_discovery = (
            {"documents": self._coerce_documents(test_overrides.get("b3_documents"), "Formulário de Provento em Dinheiro Aprovado"), "warnings": [], "source_urls": []}
            if "b3_documents" in test_overrides
            else discover_b3_documents(ticker, company_profile, cache_dir)
        )
        ri_discovery = (
            {"documents": self._coerce_documents(test_overrides.get("ri_documents"), "RI"), "warnings": [], "source_urls": []}
            if "ri_documents" in test_overrides
            else discover_ri_dividend_documents(ticker, company_profile, cache_dir)
        )
        return cvm_discovery, b3_discovery, ri_discovery

    def _aggregator_result(self, ticker: str, test_overrides: dict[str, Any]) -> dict[str, Any]:
        if not data_source_flag("allow_aggregator_scraping", True):
            return {"ticker": ticker.upper(), "events": [], "warnings": ["Scraping de agregadores desabilitado por configuracao."]}
        return scrape_aggregator_dividends(ticker, test_overrides.get("aggregator_page", ""), test_overrides.get("aggregator_url"))

    def _brapi_result(self, ticker: str, test_overrides: dict[str, Any]) -> dict[str, Any]:
        if "brapi_result" in test_overrides:
            return dict(test_overrides["brapi_result"])
        if test_overrides.get("disable_brapi"):
            return {"ticker": ticker.upper(), "events": [], "warnings": ["BRAPI desabilitada por override de teste."]}
        return collect_brapi_free_dividends(ticker)

    def collect(
        self,
        ticker: str,
        company_profile: dict[str, Any],
        *,
        cache_dir: str | Path | None = None,
        years: list[int] | None = None,
        test_overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        test_overrides = test_overrides or {}
        cache_root = self._cache_root(cache_dir)
        years = years or []
        cvm_discovery, b3_discovery, ri_discovery = self._discover_documents(ticker, company_profile, cache_dir, years, test_overrides)
        cvm_docs = self._coerce_documents(cvm_discovery.get("documents"), "Aviso aos Acionistas")
        b3_docs = self._coerce_documents(b3_discovery.get("documents"), "Formulário de Provento em Dinheiro Aprovado")
        ri_docs = self._coerce_documents(ri_discovery.get("documents"), "RI")
        cvm = collect_cvm_ipe_dividends(ticker, company_profile, cvm_docs)
        b3 = collect_b3_cash_dividends(ticker, company_profile, b3_docs)
        ri = collect_ri_dividends(ticker, company_profile, ri_docs)
        brapi = self._brapi_result(ticker, test_overrides)
        aggregator = self._aggregator_result(ticker, test_overrides)
        for year in years:
            self._write_cache(cache_root, "metadata", f"{ticker.lower()}-{year}.json", {"ticker": ticker.upper(), "year": year, "company_cvm_code": company_profile.get("cvm_code")})
        for document in cvm_docs:
            if document.get("text"):
                self._write_cache(cache_root, "raw", f"{document['id']}.txt", document["text"])
        self._write_cache(cache_root, "parsed", f"{ticker.lower()}-events.json", {"cvm": cvm.get("events", []), "b3": b3.get("events", []), "ri": ri.get("events", [])})
        reconciled = reconcile_dividend_events(
            cvm.get("events"),
            b3.get("events"),
            ri.get("events"),
            brapi.get("events"),
            aggregator.get("events"),
        )
        reconciled["collection"] = {
            "cvm": cvm,
            "b3": b3,
            "ri": ri,
            "brapi": brapi,
            "aggregator": aggregator,
        }
        reconciled["warnings"] = list(dict.fromkeys(
            list(cvm_discovery.get("warnings") or [])
            + list(b3_discovery.get("warnings") or [])
            + list(ri_discovery.get("warnings") or [])
            + list(cvm.get("warnings") or [])
            + list(b3.get("warnings") or [])
            + list(ri.get("warnings") or [])
            + list(brapi.get("warnings") or [])
            + list(aggregator.get("warnings") or [])
        ))
        reconciled["source_summary"] = {
            "cvm": self._summary(cvm, cvm_discovery.get("source_urls") or [item.get("url") for item in cvm_docs]),
            "b3": self._summary(b3, b3_discovery.get("source_urls") or [item.get("url") for item in b3_docs]),
            "ri": self._summary(ri, ri_discovery.get("source_urls") or [item.get("url") for item in ri_docs]),
            "brapi": self._summary(brapi, [event.get("source_url") for event in brapi.get("events", [])]),
            "aggregator": self._summary(aggregator, [test_overrides.get("aggregator_url")]),
        }
        return reconciled
