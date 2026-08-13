import sys
import time
from playwright.sync_api import sync_playwright

TARGET_URL = "https://ott.lleidatv.cat/ca/pl/6"
OUTPUT_FILE = "playlist.m3u"
CHANNEL_NAME = "LLEIDA TV"
LOGO_URL = "https://pbs.twimg.com/profile_images/1765275511620538368/Hiz43OMZ_400x400.jpg"

def extract_m3u8():
    m3u8_urls = []

    def handle_request(request):
        url = request.url
        # Busquem la URL m3u8 de CloudFront o de l'stream actiu
        if ".m3u8" in url and url not in m3u8_urls:
            print(f"[+] URL m3u8 trobada: {url}")
            m3u8_urls.append(url)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        page.on("request", handle_request)

        print(f"Navegant a {TARGET_URL}...")
        try:
            page.goto(TARGET_URL, wait_until="networkidle", timeout=30000)
            time.sleep(5)
        except Exception as e:
            print(f"Alerta durant la navegació: {e}")

        browser.close()

    if m3u8_urls:
        # Prioritzem la URL de Cloudfront si n'hi ha cap, si no agafem la darrera
        cloudfront_urls = [u for u in m3u8_urls if "cloudfront.net" in u]
        final_m3u8 = cloudfront_urls[-1] if cloudfront_urls else m3u8_urls[-1]
        
        # Format M3U optimitzat per a Smart TVs (LG, Samsung, Android TV, TiviMate, etc.)
        m3u_content = (
            "#EXTM3U\n"
            f'#EXTINF:-1 tvg-id="LLEIDATV.cat" tvg-name="LLEIDATV.cat" tvg-logo="{LOGO_URL}" group-title="Catalunya", {CHANNEL_NAME}\n'
            "#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)\n"
            "#EXTVLCOPT:http-referrer=https://laxarxames.com/\n"
            '#EXTHTTP:{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64)","Referer":"https://laxarxames.com/"}\n'
            f"{final_m3u8}\n"
        )

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(m3u_content)

        print(f"\n[SUCCÉS] S'ha generat l'arxiu '{OUTPUT_FILE}' per a Smart TV.")
    else:
        print("\n[ERROR] No s'ha trobat cap URL .m3u8.")
        sys.exit(1)

if __name__ == "__main__":
    extract_m3u8()
