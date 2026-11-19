#!/usr/bin/env python3
# ==============================================================================
#            ORION MOBILE SERVER — TUNNEL MONDIAL SÉCURISÉ CLOUDFLARE
# ==============================================================================

import http.server
import threading
import subprocess
import socket
import os
import sys
import time
import re
import qrcode
import io

PORT = 8080
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web_mobile")
CLOUDFLARED_EXE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cloudflared.exe")

class OrionHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def end_headers(self):
        self.send_header('Cross-Origin-Opener-Policy', 'same-origin')
        self.send_header('Cross-Origin-Embedder-Policy', 'require-corp')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

def run_http_server():
    server_address = ('127.0.0.1', PORT)
    httpd = http.server.HTTPServer(server_address, OrionHandler)
    httpd.serve_forever()

def main():
    # 1. Démarrer le serveur HTTP local en arrière-plan
    t = threading.Thread(target=run_http_server, daemon=True)
    t.start()

    print("\n" + "=" * 65)
    print("      🚀 ORION MOBILE — GÉNÉRATION DU LIEN SÉCURISÉ MONDIAL 📱")
    print("=" * 65)
    print("Connexion au réseau sécurisé Cloudflare en cours (zéro avertissement)...")

    # 2. Lancer Cloudflare Tunnel pour obtenir un vrai domaine HTTPS certifié
    cmd = [CLOUDFLARED_EXE, "tunnel", "--url", f"http://127.0.0.1:{PORT}"]
    proc = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.DEVNULL, text=True)

    public_url = None
    start_time = time.time()

    while time.time() - start_time < 15:
        line = proc.stderr.readline()
        match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
        if match:
            public_url = match.group(0)
            break

    if not public_url:
        print("Erreur : Impossible d'obtenir le tunnel public. Vérifiez votre connexion Internet.")
        sys.exit(1)

    # Sauvegarder le lien sur le Bureau pour que Christian puisse le copier facilement
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    link_file = os.path.join(desktop_path, "LIEN_ORION_POUR_TELEPHONE.txt")
    with open(link_file, "w", encoding="utf-8") as f:
        f.write(f"VOICI LE LIEN D'ORION POUR TON TÉLÉPHONE :\n\n{public_url}\n\nOuvre-le dans Google Chrome sur ton téléphone !")

    print("\n" + "*" * 65)
    print("✨ SUCCÈS ! TON LIEN SÉCURISÉ EST PRÊT (ZÉRO AVERTISSEMENT) ✨")
    print("*" * 65)
    print(f"\n👉 Ouvre ce lien sur ton téléphone (ou envoie-le toi par message) :")
    print(f"\n   {public_url}\n")
    print(f"(Le lien a aussi été enregistré dans un fichier sur ton Bureau :")
    print(f" 'LIEN_ORION_POUR_TELEPHONE.txt')\n")
    print("*" * 65)

    # Affichage QR code pour ceux qui veulent juste pointer leur caméra
    try:
        qr = qrcode.QRCode(border=1)
        qr.add_data(public_url)
        qr.make(fit=True)
        f = io.StringIO()
        qr.print_ascii(out=f, invert=True)
        f.seek(0)
        print("\nOu scanne le QR code avec la caméra du téléphone :\n")
        print(f.read())
    except Exception:
        pass

    print("=" * 65)
    print("1. Ce lien est 100% officiel, sécurisé avec le cadenas vert 🔒.")
    print("2. Zéro avertissement rouge, zéro message bizarre !")
    print("3. Dès que la page s'ouvre, autorise le micro et discute avec Orion !")
    print("=" * 65)
    print("\n(Laisse cette fenêtre ouverte tant que tu utilises l'application sur ton téléphone)\n")

    try:
        proc.wait()
    except KeyboardInterrupt:
        print("\nArrêt d'Orion Mobile.")
        proc.terminate()

if __name__ == "__main__":
    main()
