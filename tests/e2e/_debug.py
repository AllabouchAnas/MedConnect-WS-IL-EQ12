from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

o = Options()
o.add_argument("--headless=new")
o.add_argument("--no-sandbox")
d = webdriver.Chrome(options=o)
d.get("http://127.0.0.1:8000/")
time.sleep(1)
print("URL1", d.current_url)
print("BODY1", d.find_element(By.TAG_NAME, "body").text[:300])
try:
    d.find_element(By.ID, "go").click()
except Exception as e:
    print("GO ERR", e)
time.sleep(2)
print("URL2", d.current_url)
print("BODY2", d.find_element(By.TAG_NAME, "body").text[:300])
d.get("http://127.0.0.1:8000/#/patients")
time.sleep(2)
print("URL3", d.current_url)
print("BODY3", d.find_element(By.TAG_NAME, "body").text[:600])
print("HTML3", d.find_element(By.ID, "app").get_attribute("innerHTML")[:600] if d.find_elements(By.ID, "app") else "NO APP")
d.quit()
