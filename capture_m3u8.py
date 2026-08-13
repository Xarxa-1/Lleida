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
        if ".m3u8" in url and url not in m3u8_urls:
            print(f"[+] URL m3u8 detectada: {url}")
            m3u8_urls.append(url)

    with sync_playwright() as p:
        # Executem el navegador Chromium
        browser = p.chromium.launch(headless=True)
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()

        # Escortem totes les peticions de xarxa
        page.on("request", handle_request)

        print(f"Navegant a {TARGET_URL}...")
        try:
            page.goto(TARGET_URL, wait_until="networkidle", timeout=30000)
            
            # Esperem que es carreguin tots els iframes i reproductors
            time.sleep(5)

            # Si hi ha un iframe de La Xarxa o un reproductor, interactuem per activar la petició
            for frame in page.frames:
                try:
                    frame.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                except Exception:
                    pass

            time.sleep(5)

        except Exception as e:
            print(f"Alerta durant la navegació: {e}")

        browser.close()

    # Filtrem prioritzant les URL de CloudFront (La Xarxa+) que contenen el token JWT
    cloudfront_urls = [u for u in m3u8_urls if "cloudfront.net" in u]
    
    if cloudfront_urls:
        final_m3u8 = cloudfront_urls[-1]
        print(f"\n[OK] S'ha seleccionat la URL de CloudFront: {final_m3u8}")
    elif m3u8_urls:
        # Si no troba cloudfront, agafa la darrera que no sigui cdnmedia si és possible
        non_cdnmedia = [u for u in m3u8_urls if "cdnmedia.tv" not in u]
        final_m3u8 = non_cdnmedia[-1] if non_cdnmedia else m3u8_urls[-1]
        print(f"\n[AVÍS] No s'ha trobat CloudFront. S'utilitza: {final_m3u8}")
    else:
        print("\n[ERROR] No s'ha trobat cap URL .m3u8.")
        sys.exit(1)

    # Construcció de l'arxiu .m3u compatible amb Smart TV i VLC
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

    print(f"\n[SUCCÉS] S'ha generat l'arxiu '{OUTPUT_FILE}' correctament.")

if __name__ == "__main__":
    extract_m3u8()
