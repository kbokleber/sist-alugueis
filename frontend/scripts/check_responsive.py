"""Verificacao visual responsiva do checklist de conferencia.

Roda o app (dev server em 127.0.0.1:5173) em varios viewports (celular e
tablet), autentica via API local, abre o checklist de saida, entra em uma
area, clica na miniatura do item e valida o lightbox (imagem ampliada).

A credencial NAO tem valor padrao: o dev.db local pode conter usuarios reais
importados do dump de producao. Informe as variaveis de ambiente:

    $env:APP_EMAIL = "seu.usuario@dominio.com"
    $env:APP_PASSWORD = "sua-senha-de-dev"
    python frontend/scripts/check_responsive.py
"""

import json
import os
import sys
import urllib.request

from playwright.sync_api import sync_playwright

APP_URL = os.environ.get("APP_URL", "http://127.0.0.1:5173")
API_URL = os.environ.get("API_URL", "http://127.0.0.1:8000")
EMAIL = os.environ.get("APP_EMAIL", "")
PASSWORD = os.environ.get("APP_PASSWORD", "")

VIEWPORTS = [
    ("celular-360", 360, 740),
    ("celular-390", 390, 844),
    ("tablet-768", 768, 1024),
    ("tablet-820", 820, 1180),
]

# Telas principais do app (rota do React Router) + rotulos de acao opcionais.
PAGES = [
    ("dashboard", "/dashboard", None),
    ("imoveis", "/properties", None),
    ("receitas", "/revenues", None),
    ("despesas", "/expenses", None),
    ("conferencias", "/checklists", None),
    ("categorias", "/categories", None),
    ("cat-inventario", "/inventory-categories", None),
    ("usuarios", "/users", None),
    ("auditoria", "/audit", None),
]

OUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_shots")


def api_login():
    """Autentica direto na API local e devolve o par (token, user)."""
    if not EMAIL or not PASSWORD:
        raise RuntimeError(
            "Defina APP_EMAIL e APP_PASSWORD no ambiente antes de rodar. "
            "Ex.: $env:APP_EMAIL='...' ; $env:APP_PASSWORD='...'"
        )

    payload = json.dumps({"email": EMAIL, "password": PASSWORD}).encode()
    req = urllib.request.Request(
        f"{API_URL}/api/v1/auth/login",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        body = json.loads(resp.read())

    token = body["data"]["access_token"]
    user = {
        "id": body["data"].get("user_id") or "00000000-0000-0000-0000-000000000000",
        "email": EMAIL,
        "name": "Verificacao Responsiva",
        "role": "admin",
        "is_superuser": True,
        "type": "access",
    }
    return token, user


def inject_session(context, token, user):
    """Grava a sessao no zustand persist (auth-storage) antes de qualquer script do app.

    Precisa ser um init_script: a tela /login dispara o redirect do Keycloak
    assim que carrega, entao escrever no localStorage depois LandingPage ja
    estaria gravando no dominio errado (auth.kbosolucoes.com.br).
    """
    payload = json.dumps({"user": user, "token": token})
    context.add_init_script(
        """
        (() => {
            try {
                if (location.origin !== 'http://127.0.0.1:5173' &&
                    location.origin !== 'http://localhost:5173') {
                    return;
                }
                localStorage.setItem('auth-storage', JSON.stringify({
                    state: {
                        user: PAYLOAD.user,
                        token: PAYLOAD.token,
                        authProvider: 'legacy',
                        isAuthenticated: true,
                    },
                    version: 0,
                }));
            } catch (e) {
                // origem diferente: ignora
            }
        })();
        """.replace("PAYLOAD", payload)
    )


def js_click_by_text(page, text, exact=True):
    """Clica via JS (ignora actionability), util em tabelas com scroll horizontal."""
    return page.evaluate(
        """([text, exact]) => {
            const nodes = Array.from(document.querySelectorAll('button'));
            const target = nodes.find((b) => {
                const t = (b.textContent || '').trim();
                return exact ? t === text : t.includes(text);
            });
            if (!target) return false;
            target.scrollIntoView({block: 'center'});
            target.click();
            return true;
        }""",
        [text, exact],
    )


def open_checklist_and_category(page):
    page.goto(f"{APP_URL}/revenues", wait_until="networkidle")
    page.wait_for_timeout(2500)
    print("   [1] pagina carregada:", page.url)

    if not js_click_by_text(page, "Saída", exact=True):
        raise RuntimeError("botao 'Saida' nao encontrado")
    print("   [2] modal de checklist aberto")
    page.wait_for_timeout(3500)

    if not js_click_by_text(page, "Cozinha", exact=False):
        raise RuntimeError("area 'Cozinha' nao encontrada")
    print("   [3] area Cozinha aberta")
    page.wait_for_timeout(2500)


def check_lightbox(page, name="x"):
    thumbs = page.query_selector_all("button[aria-label*='Ampliar']")
    if not thumbs:
        return {"ok": False, "erro": "nenhuma miniatura encontrada"}
    thumbs[0].click()
    page.wait_for_timeout(2000)
    result = page.evaluate(
        """() => {
            const dialog = document.querySelector('[aria-modal="true"]');
            if (!dialog) return {ok: false, erro: 'lightbox nao abriu'};
            const img = dialog.querySelector('img');
            const rect = img ? img.getBoundingClientRect() : null;
            return {
                ok: true,
                imgW: img ? img.naturalWidth : 0,
                imgH: img ? img.naturalHeight : 0,
                visivel: img ? !img.className.includes('hidden') : false,
                renderW: rect ? Math.round(rect.width) : 0,
                renderH: rect ? Math.round(rect.height) : 0,
                cabeNaTela: rect ? (rect.width <= window.innerWidth && rect.height <= window.innerHeight) : false,
                bodyOverflow: document.body.style.overflow,
            };
        }"""
    )
    page.screenshot(path=os.path.join(OUT_DIR, f"lightbox-{name}.png"))
    page.keyboard.press("Escape")
    page.wait_for_timeout(600)
    return result


def check_horizontal_overflow(page):
    """Detecta elementos que estouram a largura da tela (scroll horizontal real).

    Ignora elementos que estao dentro de um container com overflow-x proprio
    (tabelas com rolagem lateral, carousels, etc.).
    """
    return page.evaluate(
        """() => {
            const limit = window.innerWidth;
            const hasScrollableAncestor = (el) => {
                let node = el.parentElement;
                while (node && node !== document.body) {
                    const ox = getComputedStyle(node).overflowX;
                    if (ox === 'auto' || ox === 'scroll') return true;
                    node = node.parentElement;
                }
                return false;
            };
            const bad = [];
            document.querySelectorAll('body *').forEach((el) => {
                const rect = el.getBoundingClientRect();
                if (rect.width === 0 || rect.height === 0) return;
                if (rect.right <= limit + 2) return;
                if (hasScrollableAncestor(el)) return;
                bad.push({
                    tag: el.tagName.toLowerCase(),
                    cls: (el.className || '').toString().slice(0, 70),
                    right: Math.round(rect.right),
                });
            });
            return {
                docScrollW: document.documentElement.scrollWidth,
                viewportW: window.innerWidth,
                temScrollH: document.documentElement.scrollWidth > window.innerWidth + 1,
                estourando: bad.slice(0, 8),
                total: bad.length,
            };
        }"""
    )


def check_pages(page, viewport_name):
    """Percorre as telas principais e detecta scroll horizontal indevido."""
    findings = []
    for label, route, _ in PAGES:
        page.goto(f"{APP_URL}{route}", wait_until="networkidle")
        page.wait_for_timeout(1800)
        overflow = check_horizontal_overflow(page)
        status = "OK" if not overflow.get("temScrollH") else "SCROLL-H"
        print(f"   [{status}] {label} ({route}) scrollW={overflow['docScrollW']} vw={overflow['viewportW']}")
        if overflow.get("temScrollH"):
            findings.append({
                "tela": label,
                "rota": route,
                "scrollW": overflow["docScrollW"],
                "viewportW": overflow["viewportW"],
                "estourando": overflow["estourando"],
            })
    return findings


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    token, user = api_login()
    report = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for name, width, height in VIEWPORTS:
            context = browser.new_context(
                viewport={"width": width, "height": height},
                device_scale_factor=2,
                is_mobile=width < 768,
                has_touch=width < 768,
            )
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda e: errors.append(str(e)))
            try:
                inject_session(context, token, user)
                open_checklist_and_category(page)
                page.screenshot(path=os.path.join(OUT_DIR, f"itens-{name}.png"))
                overflow = check_horizontal_overflow(page)
                result = check_lightbox(page, name)
                result["viewport"] = {"width": width, "height": height}
                result["overflow"] = overflow
                result["errosJs"] = errors
                report[name] = result
                print(f"{name}: lightbox {json.dumps(result, ensure_ascii=False)}")

                print(f"-- varredura de telas ({name}) --")
                scroll_problems = check_pages(page, name)
                report[name]["telasComScrollH"] = scroll_problems
                if scroll_problems:
                    print(f"   ATENCAO: {len(scroll_problems)} tela(s) com scroll horizontal")
            except Exception as exc:  # noqa: BLE001
                report[name] = {"ok": False, "erro": str(exc), "errosJs": errors}
                print(f"{name}: ERRO {exc}")
            finally:
                context.close()
        browser.close()

    print("\n=== RESUMO ===")
    for name, result in report.items():
        status = "OK" if result.get("ok") else "FALHOU"
        print(f"{name}: {status} {result.get('erro', '')}")
    return 0 if all(r.get("ok") for r in report.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
