import subprocess, sys

for pkg in ["requests", "websocket-client", "playwright"]:
    try:
        __import__(pkg.replace("-", "_"))
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg])

# Garante que o Chromium do Playwright está instalado
subprocess.run([sys.executable, "-m", "playwright", "install", "chromium", "--quiet"],
               capture_output=True)

import requests, json, websocket, threading, time, os, ssl, random, string
from datetime import datetime
from playwright.sync_api import sync_playwright

# ── configurações ─────────────────────────────────────────────────────────────

USUARIO      = "seu@email.com"          # e-mail de login no Tangerino
SENHA        = "suaSenha"               # senha do Tangerino
STATIC_AUTH  = ""                       # chave base64 da API — obtida via DevTools após login
WORKPLACE_ID = 0                        # ID do local de trabalho (ver rede do navegador)
USER_CODE    = 0                        # ID do usuário (ver rede do navegador)
USER_NAME    = "SEU NOME COMPLETO"      # nome exibido no relatório
USER_TYPE    = "ADMINISTRATOR"

REPORT_API  = "https://report.tangerino.com.br/async-reports"
WS_BASE     = "wss://report.tangerino.com.br/websocket"
WS_DEST     = f"/app/session/report/time-sheet/{USER_TYPE}_{USER_CODE}"
LOGIN_URL   = "https://app.tangerino.com.br/Tangerino/pages/LoginPage"
FOLHA_URL   = "https://app.tangerino.com.br/Tangerino/pages/folha-ponto?funcionalidade=24&wicket:pageMapName=wicket-0"

PASTA_DESTINO = os.path.join(os.path.expanduser("~"), "Documents", "conferencia diária")
os.makedirs(PASTA_DESTINO, exist_ok=True)

# ── 1. captura token via Playwright headless ──────────────────────────────────

def obter_token():
    print("[Token] Fazendo login (modo silencioso)...")
    token_holder = [None]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        def interceptar(request):
            t = request.headers.get("tng-web-token")
            if t and not token_holder[0]:
                token_holder[0] = t

        page.on("request", interceptar)

        # Login
        page.goto(LOGIN_URL, wait_until="domcontentloaded")

        # Clica na aba Empregador
        try:
            page.locator("text=Empregador").first.click()
            page.wait_for_timeout(800)
        except Exception:
            pass

        # Preenche credenciais
        page.fill('input[name="login"]', USUARIO)
        page.fill('input[name="password"]', SENHA)
        page.click('input[name="btnLogin"]')

        # Aguarda dashboard carregar
        try:
            page.wait_for_load_state("networkidle", timeout=15000)
        except Exception:
            pass

        # Navega para a página de folha (carrega o iframe do report)
        page.goto(FOLHA_URL, wait_until="domcontentloaded")

        # Aguarda até capturar o token (máx 15s)
        for _ in range(30):
            if token_holder[0]:
                break
            page.wait_for_timeout(500)

        browser.close()

    if token_holder[0]:
        print("[Token] Capturado com sucesso.")
    else:
        print("[Token] Não foi possível capturar automaticamente.")

    return token_holder[0]

# ── 2. POST para gerar relatório ──────────────────────────────────────────────

def solicitar_relatorio(token, data_str):
    headers = {
        "tng-web-token": token,
        "authorization": STATIC_AUTH,
        "Content-Type": "application/json",
        "Origin": "https://report-web.tangerino.com.br",
        "Referer": "https://report-web.tangerino.com.br/",
    }
    payload = {
        "authorization": STATIC_AUTH,
        "filter": {
            "employee": None, "employeeId": None,
            "company": None,  "companyId": None,
            "workPlace": None, "workPlaceId": WORKPLACE_ID,
            "manager": None,  "managerId": None,
            "jobRole": None,  "jobRoleId": None,
            "costCenter": None,
            "startDate": data_str,
            "endDate":   data_str,
            "format": "PDF",
            "statusEmployee": "ADMITIDOS",
            "showHourBalance": True,
            "showOnlyEmployeesWithPunch": True,
            "showDsr": False,
            "showHorasInterjornada": False,
            "showHorasIntrajornada": False,
        },
        "type": "TIME_SHEET",
        "user": {"name": USER_NAME, "type": USER_TYPE},
    }
    resp = requests.post(REPORT_API, json=payload, headers=headers, timeout=30)
    print(f"[API] Status: {resp.status_code}")
    return resp.status_code == 200

# ── 3. WebSocket SockJS+STOMP para receber URL do PDF ─────────────────────────

def ws_url():
    sid = "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
    return f"{WS_BASE}/{random.randint(0,999)}/{sid}/websocket"

def aguardar_pdf(token):
    resultado = {"url": None}
    pronto = threading.Event()

    def on_message(ws, msg):
        if msg == "o":
            frame = f"CONNECT\nAuthorization:Bearer {token}\naccept-version:1.0,1.1,1.2\nheart-beat:10000,10000\n\n\x00"
            ws.send(json.dumps([frame]))

        elif msg.startswith("a"):
            for frame in json.loads(msg[1:]):
                if frame.startswith("CONNECTED"):
                    sub = f"SUBSCRIBE\nid:sub-1\ndestination:{WS_DEST}\n\n\x00"
                    ws.send(json.dumps([sub]))
                    print("[WS] Inscrito — aguardando PDF...")

                elif "MESSAGE" in frame and "time-sheet" in frame:
                    body = frame[frame.find("\n\n") + 2:].rstrip("\x00")
                    try:
                        content = json.loads(body).get("content", {})
                        url = content.get("fileUrl")
                        if url:
                            resultado["url"] = url
                            pronto.set()
                            ws.close()
                    except Exception:
                        pass

    def on_error(ws, err):
        print(f"[WS] Erro: {err}")
        pronto.set()

    ws_app = websocket.WebSocketApp(ws_url(), on_message=on_message, on_error=on_error)
    t = threading.Thread(target=ws_app.run_forever,
                         kwargs={"sslopt": {"cert_reqs": ssl.CERT_NONE}},
                         daemon=True)
    t.start()
    pronto.wait(timeout=90)
    return resultado["url"]

# ── 4. download e salvar PDF ──────────────────────────────────────────────────

def baixar_pdf(url, data_display):
    resp = requests.get(url, timeout=60)
    nome = f"folha_ponto_{data_display.replace('/', '-')}.pdf"
    destino = os.path.join(PASTA_DESTINO, nome)
    with open(destino, "wb") as f:
        f.write(resp.content)
    print(f"[Salvo] {destino}")
    return destino

# ── main ──────────────────────────────────────────────────────────────────────

def main():
    hoje_api     = datetime.now().strftime("%Y-%m-%d")
    hoje_display = datetime.now().strftime("%d/%m/%Y")
    print(f"=== Folha de Ponto — {hoje_display} ===\n")

    token = obter_token()
    if not token:
        print("[Erro] Não foi possível obter o token. Verifique as credenciais.")
        return

    print("[WS] Conectando...")
    pdf_url = [None]

    def ws_worker():
        pdf_url[0] = aguardar_pdf(token)

    t = threading.Thread(target=ws_worker, daemon=True)
    t.start()
    time.sleep(2)

    print("[API] Solicitando relatório...")
    if not solicitar_relatorio(token, hoje_api):
        print("[Erro] Falha na requisição da API.")
        return

    t.join(timeout=90)

    if not pdf_url[0]:
        print("[Erro] PDF não recebido no tempo limite.")
        return

    print("[Download] Baixando PDF...")
    caminho_pdf = baixar_pdf(pdf_url[0], hoje_display)
    print("\n=== PDF salvo! Gerando justificativas... ===")

    try:
        import importlib.util, pathlib
        script = pathlib.Path(__file__).parent / "gerar_justificativas.py"
        spec = importlib.util.spec_from_file_location("gerar_justificativas", script)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        mod.main(caminho_pdf)
    except Exception as e:
        print(f"[Aviso] Não foi possível gerar o DOCX: {e}")

    print("\n=== Concluído! ===")

if __name__ == "__main__":
    main()
