import sys
import time
from playwright.sync_api import sync_playwright

TARGET_URL = "https://ott.lleidatv.cat/ca/pl/6"
OUTPUT_FILE = "playlist.m3u"
CHANNEL_NAME = "Lleida TV"

def extract_m3u8():
    m3u8_urls = []

    def handle_request(request):
        url = request.url
        # Escortem totes les peticions .m3u8 i evitem duplicats
        if ".m3u8" in url and url not in m3u8_urls:
            print(f"[+] URL m3u8 trobada: {url}")
            m3u8_urls.append(url)

    with sync_playwright() as p:
        # Iniciem el navegador Chromium en mode headless
        browser = p.chromium.launch(headless=True)
        
        # Simulem un agent d'usuari de navegador d'escriptori real
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        # Escortem les peticions de xarxa
        page.on("request", handle_request)

        print(f"Navegant a {TARGET_URL}...")
        try:
            page.goto(TARGET_URL, wait_until="networkidle", timeout=30000)
            
            # Esperem uns segons per assegurar que el reproductor carregui les variants de qualitat
            time.sleep(5)
            
        except Exception as e:
            print(f"Nota durant la navegació: {e}")

        browser.close()

    if m3u8_urls:
        # Triem la darrera URL trobada o la variant principal si existeix
        # Moltes vegades la darrera és la 'chunklist' directa de reproducció
        final_m3u8 = m3u8_urls[-1]
        
        # Incloem directives #EXTVLCOPT i paràmetres de Referer per a reproductors d'IPTV (Tivimate, VLC, etc.)
        m3u_content = (
            "#EXTM3U\n"
            f'#EXTINF:-1 tvg-id="LleidaTV" group-title="Locals", {CHANNEL_NAME}\n'
            "#EXTVLCOPT:http-referrer=https://ott.lleidatv.cat/\n"
            "#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\n"
            f"{final_m3u8}|Referer=https://ott.lleidatv.cat/&User-Agent=Mozilla/5.0\n"
        )

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(m3u_content)

        print(f"\n[SUCCÉS] S'ha generat l'arxiu '{OUTPUT_FILE}' correctament:")
        print(m3u_content)
    else:
        print("\n[ERROR] No s'ha trobat cap URL .m3u8 a la pàgina.")
        sys.exit(1)

if __name__ == "__main__":
    extract_m3u8()
