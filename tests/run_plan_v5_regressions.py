#!/usr/bin/env python3
import csv
import json
import io
import sys
import tempfile
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from collectors.dividends.b3_cash_dividend_form_collector import collect_b3_cash_dividends
from collectors.dividends.b3_cash_dividend_form_collector import discover_b3_documents
from collectors.dividends.cvm_ipe_dividend_collector import collect_cvm_ipe_dividends, discover_cvm_ipe_documents
from collectors.dividend_collector import collect_dividends
from collectors.dividends.official_dividend_collector import OfficialDividendCollector
from collectors.dividends.dividend_reconciler import reconcile_dividend_events
from collectors.dividends.ri_dividend_collector import collect_ri_dividends, discover_ri_dividend_documents
from collectors import market_data_collector
from collectors import ri_crawler
from valuation.method_role_selector import select_method_roles
from valuation.validate_valuation_sanity import validate_valuation_sanity
from valuation_core import calculate_valuation, classify_dividend_recurrence


FIXTURES = ROOT / "tests" / "fixtures"


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def load_fixture(name):
    path = FIXTURES / name
    if name.endswith(".json"):
        return json.loads(path.read_text(encoding="utf-8"))
    return path.read_text(encoding="utf-8")


def build_cvm_ipe_zip():
    rows = [
        {
            "CD_CVM": "2453",
            "CATEGORIA": "Aviso aos Acionistas",
            "ASSUNTO": "JCP e dividendos",
            "LINK_DOC": "http://example.test/cvm-doc.pdf",
            "PROTOCOLO": "123",
        }
    ]
    output = io.StringIO()
    fields = list(rows[0].keys())
    writer = csv.DictWriter(output, fieldnames=fields, delimiter=";")
    writer.writeheader()
    writer.writerows(rows)
    payload = io.BytesIO()
    with zipfile.ZipFile(payload, "w") as archive:
        archive.writestr("ipe_sample.csv", output.getvalue().encode("latin1"))
    return payload.getvalue()


def test_cvm_dividend_parser_extracts_jcp():
    fixture = load_fixture("dividends_cvm_ipe_sample.json")
    result = collect_cvm_ipe_dividends("CMIG4", {"cvm_code": "2453", "share_class": "PN"}, [fixture])
    assert_true(len(result["events"]) == 1, result)
    assert_true(result["events"][0]["type"] == "jcp", result["events"][0])
    assert_true(abs(result["events"][0]["amount_per_share"] - 0.45) < 1e-9, result["events"][0])


def test_ri_table_parser_extracts_dividend():
    html = load_fixture("dividends_ri_table_sample.html")
    result = collect_ri_dividends("CMIG4", {"cvm_code": "2453", "share_class": "PN"}, [{"html": html, "url": "https://ri.local/dividendos"}])
    assert_true(result["events"], result)
    assert_true(abs(result["events"][0]["amount_per_share"] - 1.20) < 1e-9, result["events"][0])
    assert_true(result["events"][0]["source"] == "RI", result["events"][0])


def test_b3_parser_extracts_dividend():
    text = load_fixture("dividends_b3_form_sample.pdf.txt")
    result = collect_b3_cash_dividends("CMIG4", {"cvm_code": "2453", "share_class": "PN"}, [{"text": text, "url": "https://b3.local/doc"}])
    assert_true(result["events"], result)
    assert_true(result["events"][0]["source"] == "B3", result["events"][0])


def test_reconciler_removes_duplicates():
    event_a = {"ticker": "CMIG4", "share_class": "PN", "type": "dividend", "amount_per_share": 1.0, "gross_amount_per_share": 1.0, "payment_date": "2024-06-20", "source": "RI", "event_id": "a"}
    event_b = {"ticker": "CMIG4", "share_class": "PN", "type": "dividend", "amount_per_share": 1.0, "gross_amount_per_share": 1.0, "payment_date": "2024-06-20", "source": "AGGREGATOR", "event_id": "b"}
    result = reconcile_dividend_events([event_a], [event_b])
    assert_true(len(result["events"]) == 1, result)
    assert_true(result["events"][0]["source"] == "RI", result["events"][0])
    assert_true(result["events"][0]["reconciled_event_id"], result["events"][0])


def test_reconciler_uses_tolerance_for_amount_and_date():
    event_a = {"ticker": "CMIG4", "share_class": "PN", "type": "dividend", "amount_per_share": 1.0000, "gross_amount_per_share": 1.0000, "payment_date": "2024-06-20", "source": "CVM_IPE", "event_id": "a"}
    event_b = {"ticker": "CMIG4", "share_class": "PN", "type": "dividend", "amount_per_share": 1.0040, "gross_amount_per_share": 1.0040, "payment_date": "2024-06-23", "source": "AGGREGATOR", "event_id": "b"}
    result = reconcile_dividend_events([event_a], [event_b])
    assert_true(len(result["events"]) == 1, result)
    assert_true(result["events"][0]["source"] == "CVM_IPE", result["events"][0])
    assert_true(result["reconciliation"]["matching_policy"]["date_tolerance_days"] == 7, result["reconciliation"])


def test_reconciler_does_not_merge_different_types():
    event_a = {"ticker": "CMIG4", "share_class": "PN", "type": "jcp", "amount_per_share": 1.0, "gross_amount_per_share": 1.0, "payment_date": "2024-06-20", "source": "RI", "event_id": "a"}
    event_b = {"ticker": "CMIG4", "share_class": "PN", "type": "dividend", "amount_per_share": 1.0, "gross_amount_per_share": 1.0, "payment_date": "2024-06-20", "source": "AGGREGATOR", "event_id": "b"}
    result = reconcile_dividend_events([event_a], [event_b])
    assert_true(len(result["events"]) == 2, result)


def test_extraordinary_dividend_does_not_enter_recurring_bridge():
    recurrence = classify_dividend_recurrence([
        {"date": "2024-03-01", "year": 2024, "amount_per_share": 1.0, "source": "RI", "source_confidence": "high", "is_recurring": True, "type": "dividend"},
        {"date": "2024-09-01", "year": 2024, "amount_per_share": 4.0, "source": "RI", "source_confidence": "high", "is_extraordinary": True, "type": "capital_reduction"},
    ])
    assert_true(abs(recurrence["annual_dpa_recurring"][2024] - 1.0) < 1e-9, recurrence)
    assert_true(abs(recurrence["annual_dpa_extraordinary"][2024] - 4.0) < 1e-9, recurrence)


def test_bazin_is_blocked_with_only_low_confidence_sources():
    data = load_fixture("valuation_utility_sample.json")
    data["dividend_events"] = [
        {"date": "2024-01-01", "year": 2024, "amount_per_share": 1.0, "source": "AGGREGATOR", "source_confidence": "low", "is_recurring": True},
    ]
    valuation = calculate_valuation(data)
    assert_true(valuation["diagnosis"]["dividend_policy"]["low_confidence_only"] is True, valuation["diagnosis"]["dividend_policy"])
    assert_true(valuation["valuation"]["bazin"]["weight"] == 0.0, valuation["valuation"]["bazin"])


def test_ddm_is_flagged_when_ke_is_not_above_growth():
    sanity = validate_valuation_sanity({"valuation": {"ddm": {"inputs": {"ke": 0.08, "g": 0.08}}}, "ceiling_prices": {"recommended": {}}, "calculation_metadata": {}})
    assert_true(any(item["check"] == "ddm_ke_vs_g" and item["status"] == "invalid" for item in sanity["sanity_checks"]), sanity)


def test_dcf_warns_when_perpetuity_share_is_too_high():
    sanity = validate_valuation_sanity({
        "valuation": {"ddm": {"inputs": {"ke": 0.12, "g": 0.04}}, "dcf_fcfe": {"details": {"terminal_value_share": 0.84}}, "dcf_fcff": {"details": {}}},
        "ceiling_prices": {"recommended": {}},
        "calculation_metadata": {},
    })
    assert_true(any(item["check"] == "dcf_fcfe_terminal_value_share" for item in sanity["sanity_checks"]), sanity)


def test_bank_excludes_ev_ebitda_and_fcff_as_primary():
    roles = select_method_roles("banks")
    excluded = {item["method"] for item in roles["excluded_methods"]}
    assert_true("ev_ebitda" in excluded, roles)
    assert_true("dcf_fcff" in excluded, roles)


def test_holding_uses_nav_or_sotp():
    roles = select_method_roles("holding", has_sotp=True)
    assert_true("sotp" in roles["primary_methods"], roles)


def test_projected_ceiling_is_present_value_entry():
    data = load_fixture("valuation_utility_sample.json")
    valuation = calculate_valuation(data)
    assert_true(valuation["projected_ceiling_prices"][-1]["price_semantics"] == "preco_presente_de_entrada", valuation["projected_ceiling_prices"][-1])
    assert_true(valuation["ceiling_prices"]["projected"]["entry_projected_ceiling_price"] == valuation["projected_ceiling_price"], valuation["ceiling_prices"]["projected"])


def test_peter_lynch_never_has_direct_weight():
    data = load_fixture("valuation_utility_sample.json")
    valuation = calculate_valuation(data)
    assert_true(valuation["valuation"]["peter_lynch"]["weight"] == 0.0, valuation["valuation"]["peter_lynch"])


def test_missing_share_count_blocks_full_valuation():
    data = load_fixture("valuation_bad_data_sample.json")
    valuation = calculate_valuation(data)
    assert_true(valuation["calculation_metadata"]["valuation_status"] == "partial", valuation["calculation_metadata"])


def test_yahoo_is_not_called_by_default():
    original_fetch = market_data_collector.fetch_url
    calls = []
    brapi_payload = {"results": [{"symbol": "CMIG4", "regularMarketPrice": 10.0, "currency": "BRL", "dividendsData": {"cashDividends": []}}]}
    try:
        def fake_fetch(url):
            calls.append(url)
            if "query1.finance.yahoo.com" in url:
                raise AssertionError("Yahoo nao deveria ser chamado por padrao")
            return json.dumps(brapi_payload).encode("utf-8")
        market_data_collector.fetch_url = fake_fetch
        result = market_data_collector.collect_market_data("CMIG4")
    finally:
        market_data_collector.fetch_url = original_fetch
    assert_true(result["current_price"] == 10.0, result)
    assert_true(any("brapi.dev" in url for url in calls), calls)


def test_yahoo_is_only_called_when_explicitly_enabled():
    original_fetch = market_data_collector.fetch_url
    original_flag = market_data_collector.data_source_flag
    calls = []
    yahoo_payload = {
        "chart": {
            "result": [{
                "meta": {"marketCap": 1000, "currency": "BRL"},
                "indicators": {"quote": [{"close": [9.0, 10.0]}]},
                "events": {"dividends": {}},
            }]
        }
    }
    try:
        market_data_collector.data_source_flag = lambda name, default=None: True if name == "allow_yahoo_fallback" else default
        def fake_fetch(url):
            calls.append(url)
            if "brapi.dev" in url:
                raise RuntimeError("offline")
            return json.dumps(yahoo_payload).encode("utf-8")
        market_data_collector.fetch_url = fake_fetch
        result = market_data_collector.collect_market_data("CMIG4")
    finally:
        market_data_collector.fetch_url = original_fetch
        market_data_collector.data_source_flag = original_flag
    assert_true(result["current_price"] == 10.0, result)
    assert_true(any("query1.finance.yahoo.com" in url for url in calls), calls)


def test_official_dividend_collector_prioritizes_official_sources_and_builds_summary():
    fixture = load_fixture("dividends_cvm_ipe_sample.json")
    html = load_fixture("dividends_ri_table_sample.html")
    text = load_fixture("dividends_b3_form_sample.pdf.txt")
    collector = OfficialDividendCollector()
    result = collector.collect(
        "CMIG4",
        {"cvm_code": "2453", "share_class": "PN"},
        test_overrides={
            "cvm_documents": [fixture],
            "b3_documents": [{"text": text, "url": "https://b3.local/doc"}],
            "ri_documents": [{"html": html, "url": "https://ri.local/dividendos"}],
            "aggregator_page": "R$ 0,44",
            "aggregator_url": "https://agg.local/cmig4",
        },
        cache_dir=ROOT / "tests" / "tmp-cache",
        years=[2024],
    )
    assert_true(result["events"], result)
    assert_true(result["events"][0]["source"] in {"CVM_IPE", "B3", "RI"}, result["events"][0])
    assert_true(result["source_summary"]["cvm"]["attempted"] is True, result["source_summary"])
    assert_true("aggregator" in result["source_summary"], result["source_summary"])


def test_cvm_discovery_downloads_original_document_and_extracts_text():
    original_fetch = __import__("collectors.dividends.cvm_ipe_dividend_collector", fromlist=["fetch_url"]).fetch_url
    import collectors.dividends.cvm_ipe_dividend_collector as cvm_module
    pdf_bytes = b"%PDF-1.4\n( Aviso aos Acionistas R$ 0,45 por acao data ex 27/12/2024 pagamento 30/06/2025 )\n%%EOF"
    try:
        def fake_fetch(url, timeout=30):
            del timeout
            if url.endswith(".zip"):
                return build_cvm_ipe_zip()
            if "cvm-doc.pdf" in url:
                return pdf_bytes
            raise RuntimeError(url)
        cvm_module.fetch_url = fake_fetch
        with tempfile.TemporaryDirectory() as tmp:
            result = discover_cvm_ipe_documents("CMIG4", {"cvm_code": "2453", "share_class": "PN"}, [2024], tmp)
    finally:
        cvm_module.fetch_url = original_fetch
    assert_true(result["documents"], result)
    assert_true("R$ 0,45" in result["documents"][0]["text"] or "0,45" in result["documents"][0]["text"], result["documents"][0])
    assert_true(result["documents"][0]["url"] == "http://example.test/cvm-doc.pdf", result["documents"][0])


def test_b3_discovery_fetches_linked_document():
    import collectors.dividends.b3_cash_dividend_form_collector as b3_module
    original_fetch = b3_module.fetch_url
    overview_html = """
    <html><body>
      <a href="/docs/provento.pdf">Formulario de Provento em Dinheiro Aprovado</a>
    </body></html>
    """.encode("utf-8")
    pdf_bytes = b"%PDF-1.4\n( Formulario de Provento em Dinheiro Aprovado R$ 0,50 por acao data ex 11/04/2024 pagamento 20/05/2024 )\n%%EOF"
    try:
        def fake_fetch(url, timeout=30):
            del timeout
            if "overview" in url:
                return overview_html
            if "provento.pdf" in url:
                return pdf_bytes
            raise RuntimeError(url)
        b3_module.fetch_url = fake_fetch
        result = discover_b3_documents("CMIG4", {"name": "CEMIG", "cvm_code": "2453", "share_class": "PN"})
    finally:
        b3_module.fetch_url = original_fetch
    assert_true(result["documents"], result)
    assert_true("0,50" in result["documents"][0]["text"], result["documents"][0])


def test_ri_discovery_fetches_sitemap_and_pdf_document():
    original_fetch = ri_crawler.fetch_url
    sitemap = """
    <urlset><url><loc>https://ri.example/dividendos</loc></url></urlset>
    """.encode("utf-8")
    landing = """
    <html><body><a href="/docs/dividendos.pdf">Dividendos</a></body></html>
    """.encode("utf-8")
    pdf_bytes = b"%PDF-1.4\n( Dividendos R$ 1,20 por acao data ex 10/05/2024 pagamento 20/06/2024 )\n%%EOF"
    try:
        def fake_fetch(url, timeout=30):
            del timeout
            if url.endswith("/sitemap.xml"):
                return sitemap
            if url == "https://ri.example" or url == "https://ri.example/dividendos":
                return landing
            if "dividendos.pdf" in url:
                return pdf_bytes
            raise RuntimeError(url)
        ri_crawler.fetch_url = fake_fetch
        import collectors.dividends.ri_dividend_collector as ri_div_module
        original_collect = ri_div_module.collect_ri_documents
        original_ri_fetch = ri_div_module.fetch_url
        ri_div_module.collect_ri_documents = lambda ticker: {"documents": ri_crawler.crawl_ri("https://ri.example")["documents"], "ri_url": "https://ri.example"}
        ri_div_module.fetch_url = fake_fetch
        try:
            result = discover_ri_dividend_documents("CMIG4", {"share_class": "PN"})
            parsed = collect_ri_dividends("CMIG4", {"cvm_code": "2453", "share_class": "PN"}, result["documents"])
        finally:
            ri_div_module.collect_ri_documents = original_collect
            ri_div_module.fetch_url = original_ri_fetch
    finally:
        ri_crawler.fetch_url = original_fetch
    assert_true(result["documents"], result)
    assert_true(parsed["events"], parsed)
    assert_true(abs(parsed["events"][0]["amount_per_share"] - 1.2) < 1e-9, parsed["events"][0])


def test_collect_dividends_reports_official_auxiliary_and_not_found_status():
    fixture = load_fixture("dividends_cvm_ipe_sample.json")
    official = collect_dividends("CMIG4", {"cvm_code": "2453", "share_class": "PN"}, test_overrides={"cvm_documents": [fixture], "disable_brapi": True})
    assert_true(official["source_status"] == "oficial", official)
    auxiliary = collect_dividends("CMIG4", {"cvm_code": "2453", "share_class": "PN"}, test_overrides={"aggregator_page": "R$ 0,44", "aggregator_url": "https://agg.local", "disable_brapi": True})
    assert_true(auxiliary["source_status"] == "auxiliar", auxiliary)
    empty = collect_dividends("CMIG4", {"cvm_code": "2453", "share_class": "PN"}, test_overrides={"cvm_documents": [], "b3_documents": [], "ri_documents": [], "disable_brapi": True})
    assert_true(empty["source_status"] == "nao_encontrado", empty)


def test_official_dividend_collector_can_discover_sources_without_manual_evidence():
    original_cvm = OfficialDividendCollector._discover_documents
    try:
        def fake_discovery(self, ticker, company_profile, cache_dir, years, test_overrides):
            del self, cache_dir, years, test_overrides
            fixture = load_fixture("dividends_cvm_ipe_sample.json")
            return (
                {"documents": [fixture], "warnings": [], "source_urls": ["https://dados.cvm.gov.br/sample"]},
                {"documents": [], "warnings": [], "source_urls": ["https://b3.local"]},
                {"documents": [], "warnings": [], "source_urls": ["https://ri.local"]},
            )
        OfficialDividendCollector._discover_documents = fake_discovery
        result = OfficialDividendCollector().collect("CMIG4", {"cvm_code": "2453", "share_class": "PN"})
    finally:
        OfficialDividendCollector._discover_documents = original_cvm
    assert_true(result["events"], result)
    assert_true(result["source_summary"]["cvm"]["succeeded"] is True, result["source_summary"])


def main():
    test_cvm_dividend_parser_extracts_jcp()
    test_ri_table_parser_extracts_dividend()
    test_b3_parser_extracts_dividend()
    test_reconciler_removes_duplicates()
    test_reconciler_uses_tolerance_for_amount_and_date()
    test_reconciler_does_not_merge_different_types()
    test_extraordinary_dividend_does_not_enter_recurring_bridge()
    test_bazin_is_blocked_with_only_low_confidence_sources()
    test_ddm_is_flagged_when_ke_is_not_above_growth()
    test_dcf_warns_when_perpetuity_share_is_too_high()
    test_bank_excludes_ev_ebitda_and_fcff_as_primary()
    test_holding_uses_nav_or_sotp()
    test_projected_ceiling_is_present_value_entry()
    test_peter_lynch_never_has_direct_weight()
    test_missing_share_count_blocks_full_valuation()
    test_yahoo_is_not_called_by_default()
    test_yahoo_is_only_called_when_explicitly_enabled()
    test_official_dividend_collector_prioritizes_official_sources_and_builds_summary()
    test_collect_dividends_reports_official_auxiliary_and_not_found_status()
    test_official_dividend_collector_can_discover_sources_without_manual_evidence()
    test_cvm_discovery_downloads_original_document_and_extracts_text()
    test_b3_discovery_fetches_linked_document()
    test_ri_discovery_fetches_sitemap_and_pdf_document()
    print("ok")


if __name__ == "__main__":
    main()
