"""Capture les rapports HTML des outils QA sous forme de figures LaTeX.

Usage : python tests/qualite/capture_reports.py
Prérequis : Chrome installé + selenium (voir requirements-qa.txt).
"""

from pathlib import Path
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options

ROOT = Path(__file__).resolve().parents[2]
SHOTS = ROOT / "report" / "screenshots"
SHOTS.mkdir(parents=True, exist_ok=True)

CAPTURES = [
    ("reports/pytest.html", "qa_pytest_html.png", 2),
    ("reports/coverage/html_unitaire/index.html", "qa_coverage_unitaire.png", 2),
    ("reports/coverage/html_api/index.html", "qa_coverage_api.png", 2),
    ("reports/newman/newman.html", "qa_postman_newman.png", 3),
    ("reports/e2e.html", "qa_e2e_report.png", 2),
    ("reports/jmeter/dashboard/index.html", "qa_jmeter_dashboard.png", 4),
    ("reports/qa_summary/analyse_statique.html", "qa_ruff.png", 1),
    ("reports/qa_summary/dependances.html", "qa_pip_audit.png", 1),
    ("reports/qa_summary/sonarqube.html", "qa_sonarqube.png", 1),
    ("reports/qa_summary/zap_fallback.html", "qa_zap.png", 1),
]


def main():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--hide-scrollbars")
    opts.add_argument("--window-size=1600,1000")
    driver = webdriver.Chrome(options=opts)
    try:
        for rel, name, pause in CAPTURES:
            path = ROOT / rel
            if not path.exists():
                print(f"SKIP (absent) : {rel}")
                continue
            driver.get(path.as_uri())
            time.sleep(pause)
            out = SHOTS / name
            driver.save_screenshot(str(out))
            print(f"OK : {out.name} <- {rel}")
    finally:
        driver.quit()


if __name__ == "__main__":
    main()
