# file: lms_absen.py
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time

# --- Konfigurasi Chrome ---
opts = Options()
# opts.add_argument("--headless=new")   # aktifkan jika ingin tanpa UI
opts.add_argument("--start-maximized")
opts.add_argument("--disable-notifications")
opts.add_argument("--disable-infobars")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-dev-shm-usage")

# --- Inisialisasi Driver ---
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
wait = WebDriverWait(driver, 20)

def safe_click(xpath, desc="elemen"):
    """Klik elemen dengan auto-scroll dan fallback JS click"""
    try:
        elem = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elem)
        wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        try:
            elem.click()
        except:
            driver.execute_script("arguments[0].click();", elem)
        print(f"✅ Klik {desc} berhasil")
        time.sleep(1)
    except Exception as e:
        print(f"❌ Gagal klik {desc}: {type(e).__name__} — {e}")

try:
    # 1️⃣ Buka LMS dan login
    driver.get("https://lms.unm.ac.id/")
    print("🌐 Membuka LMS UNM...")
    print("Title:", driver.title)

    safe_click('/html/body/div[1]/div[1]/header/div/nav/ul[2]/li[1]/a', "Tombol Login")

    username = wait.until(EC.visibility_of_element_located((By.ID, 'login_username')))
    password = wait.until(EC.visibility_of_element_located((By.ID, 'login_password')))
    username.send_keys("240210500024")  # Ganti dengan akun kamu
    password.send_keys("Maba24ft")      # Ganti dengan password kamu

    safe_click('/html/body/div[1]/div[1]/div[3]/div/div/div[2]/div/div/form/button', "Tombol Submit Login")

    # 2️⃣ Tunggu dashboard
    print("⏳ Menunggu halaman utama...")
    time.sleep(10)

    # 3️⃣ Navigasi ke presensi dan isi otomatis
    steps = [
        ('/html/body/div[2]/div[1]/div[3]/div/div/div/div[1]/div/div[3]/div[2]/aside[2]/div[3]/div/div/div/div[2]/div/div/div[1]/div/div/div[21]/div[1]/div/ul/li/a', "Menu Mata Kuliah"),
        ('/html/body/div[1]/div[1]/div[5]/div[3]/div[2]/div/div/div/div/div/div/div/div[2]/div[2]/li[1]/div/div/div[1]/h4/a', "Masuk Halaman Kelas"),
        ('/html/body/div[1]/div[1]/div[5]/div[3]/div[2]/div/div/div/div/div/div/div/div[2]/div[2]/li[1]/div/div/div[2]/div/div[3]/ul/li[3]/div/div/div[2]/div[1]/a/span', "Tautan Presensi"),
        ('/html/body/div[1]/div[1]/div[5]/div[3]/div[2]/div/div/div/div/div/table[1]/tbody/tr[7]/td[3]/a', "Tombol Isi Presensi"),
        ('/html/body/div[1]/div[1]/div[5]/div[3]/div[2]/div/div/div/div/div/form/fieldset/div/div/div[2]/fieldset/div/label[1]/input', "Pilih Hadir"),
        ('/html/body/div[1]/div[1]/div[5]/div[3]/div[2]/div/div/div/div/div/form/div[2]/div[2]/fieldset/div/div[1]/span[2]/input', "Konfirmasi Hadir"),
    ]

    for xpath, desc in steps:
        safe_click(xpath, desc)

    print("🎯 Presensi selesai!")

except Exception as e:
    print(f"❌ Terjadi kesalahan utama: {type(e).__name__} — {e}")

finally:
    driver.quit()
    print("🧹 Browser ditutup.")
