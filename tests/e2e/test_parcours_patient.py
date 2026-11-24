"""
Tests End-to-End (Selenium) — MedConnect, Groupe 12.

Objectif : valider dans un vrai navigateur (Chrome) les parcours critiques de
l'interface SPA : connexion, gestion des patients, confidentialité du dossier
médical (RBAC) et création d'une consultation par le médecin.

Prérequis : serveur Django démarré sur http://127.0.0.1:8000
Lancement : python -m pytest tests/e2e/test_parcours_patient.py -v --html=reports/e2e.html
"""

from pathlib import Path
import time

import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE = "http://127.0.0.1:8000/"
SHOTS = Path(__file__).resolve().parents[2] / "report" / "screenshots"
SHOTS.mkdir(parents=True, exist_ok=True)
WAIT = 15


@pytest.fixture
def driver():
    opts = Options()
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1440,1000")
    d = webdriver.Chrome(options=opts)
    d.implicitly_wait(5)
    yield d
    d.quit()


def attend(driver, by, value, timeout=WAIT):
    return WebDriverWait(driver, timeout).until(EC.presence_of_element_located((by, value)))


def connexion(driver, utilisateur="sec.demo"):
    driver.get(BASE)
    attend(driver, By.ID, "u")
    driver.find_element(By.ID, "u").clear()
    driver.find_element(By.ID, "u").send_keys(utilisateur)
    driver.find_element(By.ID, "p").clear()
    driver.find_element(By.ID, "p").send_keys("Demo@1234")
    driver.find_element(By.ID, "go").click()
    # La page de connexion contient déjà "#/login" : attendre l'URL exacte "#/"
    # et un élément présent uniquement dans le shell authentifié.
    WebDriverWait(driver, WAIT).until(lambda d: d.current_url.endswith("#/"))
    attend(driver, By.ID, "switch-role")


def capture(driver, nom):
    time.sleep(0.4)
    driver.save_screenshot(str(SHOTS / nom))


def test_UT_E2E_01_connexion_et_liste_patients(driver):
    """UT-E2E-01 : connexion secrétaire puis affichage et recherche des patients."""
    connexion(driver)
    driver.get(BASE + "#/patients")
    lignes = attend(driver, By.ID, "rows").find_elements(By.TAG_NAME, "tr")
    assert len(lignes) > 1, "La liste des patients doit contenir au moins une ligne"
    driver.find_element(By.ID, "sq").send_keys("AB123")
    driver.find_element(By.ID, "sbtn").click()
    time.sleep(1)
    assert "AB123" in driver.find_element(By.ID, "rows").text
    capture(driver, "e2e_01_patients.png")


def test_UT_E2E_02_rbac_dossier_refuse(driver):
    """UT-E2E-02 : la secrétaire ne doit pas accéder au dossier médical."""
    connexion(driver)
    driver.get(BASE + "#/dossier")
    time.sleep(1)
    assert "Accès réservé aux médecins" in driver.find_element(By.TAG_NAME, "main").text
    capture(driver, "e2e_02_rbac.png")


def test_UT_E2E_03_medecin_dossier_patient(driver):
    """UT-E2E-03 : le médecin ouvre un dossier et voit les actions cliniques."""
    connexion(driver, "dr.demo")
    driver.get(BASE + "#/dossier")
    attend(driver, By.ID, "rows")
    lien = driver.find_element(By.CSS_SELECTOR, '#rows a[href*="/dossier/"]')
    lien.click()
    time.sleep(1.2)
    assert driver.find_element(By.TAG_NAME, "h1").text
    assert "Nouvelle consultation" in driver.find_element(By.TAG_NAME, "main").text
    capture(driver, "e2e_03_dossier.png")


def test_UT_E2E_04_creation_consultation(driver):
    """UT-E2E-04 : le médecin crée une consultation depuis l'interface."""
    connexion(driver, "dr.demo")
    driver.get(BASE + "#/dossier")
    attend(driver, By.ID, "rows")
    driver.find_element(By.CSS_SELECTOR, '#rows a[href*="/dossier/"]').click()
    time.sleep(1)
    driver.find_element(By.CSS_SELECTOR, 'a[href*="consultation/new"]').click()
    attend(driver, By.ID, "cm")
    motif = "Consultation QA Selenium"
    driver.find_element(By.ID, "cm").send_keys(motif)
    driver.find_element(By.ID, "cdiag").send_keys("Contrôle automatisé E2E")
    capture(driver, "e2e_04_formulaire.png")
    driver.find_element(By.ID, "save").click()
    time.sleep(1.5)
    assert motif in driver.find_element(By.TAG_NAME, "main").text
    capture(driver, "e2e_04_consultation_creee.png")
