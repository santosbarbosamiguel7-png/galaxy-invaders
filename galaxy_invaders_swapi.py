
import tkinter as tk
import random
import math
import json
import queue
import threading
from urllib.request import Request, urlopen

# API REST publica usada no projeto da faculdade:
# GET https://swapi.info/api/starships
API_URL = "https://swapi.info/api/starships"
API_TIMEOUT = 8  # segundos

# =====================================
# CONFIGURAÇÕES
# =====================================

LARGURA = 900
ALTURA = 650
ESCALA = 5

janela = tk.Tk()
janela.title("GALAXY INVADERS - Space Shooter")
janela.geometry(f"{LARGURA}x{ALTURA}")
janela.resizable(False, False)
janela.configure(bg="#080b18")

tela = tk.Canvas(
    janela,
    width=LARGURA,
    height=ALTURA,
    bg="#080b18",
    highlightthickness=0
)
tela.pack()

# =====================================
# VARIÁVEIS
# =====================================

pontos = 0
vidas = 3
frame = 0
tempo_tiro = 0
jogo_ativo = True

teclas = set()
tiros = []
inimigos = []
estrelas = []

nave = None
numero_inimigo = 0

# Dados da API sao recebidos fora do thread da interface e entregues via fila.
# A janela Tkinter nunca e modificada dentro do thread de rede.
naves_da_api = []
fila_api = queue.Queue()
consultando_api = False

# =====================================
# FUNÇÃO PARA DESENHAR PIXEL ART
# =====================================

def desenhar_pixel_art(x, y, matriz, cor, tag, escala=ESCALA):
    for linha, conteudo in enumerate(matriz):
        for coluna, pixel in enumerate(conteudo):
            if pixel == "1":
                tela.create_rectangle(
                    x + coluna * escala,
                    y + linha * escala,
                    x + (coluna + 1) * escala,
                    y + (linha + 1) * escala,
                    fill=cor,
                    outline=cor,
                    tags=("dinamico", tag)
                )

# =====================================
# SPRITES PIXEL ART
# =====================================

NAVE_SPRITE = [
    "00000100000",
    "00011111000",
    "00111111100",
    "01111111110",
    "11111111111",
    "11101110111",
    "00101110100",
    "00101110100",
    "00001010000",
    "00011111000"
]

# Formatos de meia silhueta para gerar alienigenas simetricos em pixel art.
ALIEN_FORMATOS = [
    [0, 1, 3, 5, 6, 5, 4, 2, 0],
    [2, 3, 5, 6, 5, 5, 3, 2, 0],
    [1, 2, 4, 5, 6, 6, 5, 4, 1],
    [0, 1, 5, 6, 4, 6, 3, 1, 0],
    [2, 4, 6, 6, 6, 5, 4, 3, 2],
    [1, 3, 6, 4, 6, 5, 6, 2, 0],
]
ALIEN_PALETAS = [
    ("#f64e82", "#ffb1d0", "#7d2754", "#fff185", "#d4faff"),
    ("#ab69ff", "#d9b9ff", "#502b95", "#54f8ff", "#fff5bd"),
    ("#ff9d42", "#ffda94", "#86411c", "#80f8fe", "#fff0b3"),
    ("#40d8b3", "#b7ffe7", "#147562", "#ffde62", "#e6ffff"),
    ("#ff665b", "#ffb2a4", "#902e39", "#fff2a7", "#9ef5ff"),
    ("#519dff", "#bcdeff", "#234b91", "#ffcce6", "#e0faff"),
]


def gerar_alienigena(classe_nave=None):
    """Gera pixel art. A classe da SWAPI define base de formato/cor, se disponivel."""
    if classe_nave:
        codigo = sum((i + 1) * ord(c) for i, c in enumerate(classe_nave.lower()))
        formato = ALIEN_FORMATOS[codigo % len(ALIEN_FORMATOS)]
        paleta = ALIEN_PALETAS[(codigo // 7) % len(ALIEN_PALETAS)]
    else:
        formato = random.choice(ALIEN_FORMATOS)
        paleta = random.choice(ALIEN_PALETAS)
    matriz = [["0"] * 13 for _ in range(9)]

    def espelhar(linha, distancia, valor):
        matriz[linha][6 - distancia] = valor
        matriz[linha][6 + distancia] = valor

    for linha in range(9):
        variacao = random.choice((-1, 1)) if 0 < linha < 8 and random.random() < 0.42 else 0
        metade = max(0, min(6, formato[linha] + variacao))
        for d in range(metade + 1):
            pixel = "2" if linha < 3 else "3" if linha > 5 else "1"
            if d >= max(1, metade - 1):
                pixel = "3"
            if d >= 3 and 2 <= linha <= 6 and random.random() < 0.19:
                pixel = "0"
            espelhar(linha, d, pixel)

    cabine = random.choice((3, 4))
    matriz[cabine - 1][6] = "4"
    espelhar(cabine, 1, "4")
    matriz[cabine][6] = "4"
    espelhar(random.randint(3, 5), random.randint(3, 5), "5")
    espelhar(7, random.choice((1, 2)), "5")
    return matriz, paleta


def desenhar_alienigena(x, y, tag, classe_nave=None):
    """Desenha um alienigena usando sua classe SWAPI, quando existente."""
    matriz, paleta = gerar_alienigena(classe_nave)
    for linha, conteudo in enumerate(matriz):
        for coluna, pixel in enumerate(conteudo):
            if pixel != "0":
                cor = paleta[int(pixel) - 1]
                tela.create_rectangle(
                    x + coluna * ESCALA,
                    y + linha * ESCALA,
                    x + (coluna + 1) * ESCALA,
                    y + (linha + 1) * ESCALA,
                    fill=cor,
                    outline=cor,
                    tags=("dinamico", tag),
                )


# =====================================
# FUNDO ESPACIAL
# =====================================

def criar_fundo():
    global estrelas

    for i in range(110):
        x = random.randint(0, LARGURA)
        y = random.randint(0, ALTURA)
        tamanho = random.choice([2, 2, 3, 4])

        estrela = tela.create_rectangle(
            x, y,
            x + tamanho, y + tamanho,
            fill=random.choice(["#ffffff", "#8da8d8", "#5d77a8"]),
            outline=""
        )

        estrelas.append(estrela)

    # Estrelas maiores decorativas
    for x, y in [(100, 160), (760, 200), (650, 420), (220, 500)]:
        tela.create_rectangle(
            x, y, x + 4, y + 4,
            fill="#00e5ff",
            outline=""
        )

# =====================================
# INTERFACE
# =====================================

criar_fundo()

tela.create_rectangle(
    0, 0, LARGURA, 75,
    fill="#10172c",
    outline=""
)

tela.create_text(
    450, 29,
    text="GALAXY INVADERS",
    fill="#00e5ff",
    font=("Consolas", 24, "bold")
)

tela.create_text(
    450, 57,
    text="DEFENDA A GALAXIA",
    fill="#7186b5",
    font=("Consolas", 9, "bold")
)

texto_pontos = tela.create_text(
    105, 105,
    text="SCORE: 0000",
    fill="#ffe66d",
    font=("Consolas", 17, "bold")
)

texto_vidas = tela.create_text(
    790, 105,
    text="VIDAS: 3",
    fill="#ff5277",
    font=("Consolas", 17, "bold")
)

texto_nave_api = tela.create_text(
    450, 109,
    text="NAVE SWAPI: aguardando dados...",
    fill="#8ceaff",
    font=("Consolas", 9, "bold")
)

tela.create_line(
    25, 135, 875, 135,
    fill="#263653",
    width=2
)

texto_status_api = tela.create_text(
    450, 598,
    text="SWAPI: aguardando consulta... | C: recarregar API",
    fill="#8ee4ff",
    font=("Consolas", 10, "bold")
)

tela.create_text(
    450, 625,
    text="WASD / SETAS: MOVIMENTAR     |     ESPACO: ATIRAR",
    fill="#7186b5",
    font=("Consolas", 11, "bold")
)

# =====================================
# API SWAPI - REQUISICAO GET / JSON / THREAD
# =====================================

def normalizar_naves(payload):
    """Transforma os registros JSON em objetos seguros para a logica do jogo."""
    if isinstance(payload, list):
        registros = payload
    elif isinstance(payload, dict) and isinstance(payload.get("results"), list):
        registros = payload["results"]
    else:
        raise ValueError("JSON da API nao possui uma lista de naves")

    naves = []
    for item in registros:
        if not isinstance(item, dict):
            continue
        nome = item.get("name")
        if not isinstance(nome, str) or not nome.strip():
            continue
        classe = item.get("starship_class")
        if not isinstance(classe, str) or not classe.strip():
            classe = "Desconhecida"
        mglt_str = str(item.get("MGLT", "n/a"))
        try:
            mglt = float(mglt_str.replace(",", ""))
            if not math.isfinite(mglt) or mglt < 0:
                mglt = None
        except ValueError:
            mglt = None
        naves.append({
            "nome": nome.strip()[:70],
            "classe": classe.strip()[:80],
            "mglt": mglt,
            "mglt_texto": mglt_str[:16],
        })
    return naves


def consultar_api_em_background():
    """Faz GET numa thread para nao congelar o jogo."""
    try:
        print(f"[SWAPI] GET {API_URL}", flush=True)
        req = Request(API_URL, headers={
            "Accept": "application/json",
            "User-Agent": "GalaxyInvaders-Faculdade/1.0",
        })
        with urlopen(req, timeout=API_TIMEOUT) as resposta:
            status = resposta.status
            if status != 200:
                raise RuntimeError(f"HTTP {status}")
            dados = json.load(resposta)

        naves = normalizar_naves(dados)
        if not naves:
            raise ValueError("Resposta JSON nao contem naves validas")
        print(f"[SWAPI] HTTP {status} OK - {len(naves)} naves recebidas", flush=True)
        print(f"[SWAPI] Exemplo do JSON: {naves[0]}", flush=True)
        fila_api.put(("sucesso", naves))
    except Exception as erro:
        print(f"[SWAPI] Falha de consulta: {erro}", flush=True)
        fila_api.put(("erro", str(erro)))


def iniciar_consulta_api():
    """Pode ser acionada no inicio ou pela tecla C."""
    global consultando_api
    if consultando_api:
        return
    consultando_api = True
    tela.itemconfig(texto_status_api,
                    text="SWAPI: CONECTANDO... | C: recarregar API",
                    fill="#ffe66d")
    threading.Thread(target=consultar_api_em_background, daemon=True).start()


def processar_resposta_api():
    """Aplica o resultado no thread principal do Tkinter, durante o loop do jogo."""
    global consultando_api, naves_da_api
    while True:
        try:
            estado, conteudo = fila_api.get_nowait()
        except queue.Empty:
            break
        consultando_api = False
        if estado == "sucesso":
            naves_da_api = conteudo
            tela.itemconfig(texto_status_api,
                            text=f"SWAPI: CONECTADA ({len(naves_da_api)} naves) | C: recarregar API",
                            fill="#55efc4")
            tela.itemconfig(texto_nave_api,
                            text="NAVE SWAPI: dados recebidos! Inimigos usam classe e MGLT.")
        else:
            # Falha real indicada na tela; sem valores inventados da API.
            naves_da_api = []
            tela.itemconfig(texto_status_api,
                            text="SWAPI: OFFLINE - geracao local | C: tentar de novo",
                            fill="#ff9f43")
            tela.itemconfig(texto_nave_api, text="NAVE SWAPI: sem conexao (modo local)")

# =====================================
# CRIAR NAVE
# =====================================

def criar_nave():
    tag = "nave"

    x = 425
    y = 510

    desenhar_pixel_art(
        x, y,
        NAVE_SPRITE,
        "#00d9ff",
        tag,
        5
    )

    # Detalhe da cabine
    tela.create_rectangle(
        x + 25, y + 15,
        x + 30, y + 25,
        fill="#ffffff",
        outline="",
        tags=("dinamico", tag)
    )

    return tag

nave = criar_nave()

# =====================================
# MOVIMENTAR NAVE
# =====================================

def mover_nave():
    pos = tela.bbox(nave)

    if not pos:
        return

    velocidade = 7
    dx = 0
    dy = 0

    if "left" in teclas or "a" in teclas:
        dx -= velocidade

    if "right" in teclas or "d" in teclas:
        dx += velocidade

    if "up" in teclas or "w" in teclas:
        dy -= velocidade

    if "down" in teclas or "s" in teclas:
        dy += velocidade

    if dx != 0 and dy != 0:
        dx /= math.sqrt(2)
        dy /= math.sqrt(2)

    if pos[0] + dx < 10:
        dx = 10 - pos[0]

    if pos[2] + dx > LARGURA - 10:
        dx = LARGURA - 10 - pos[2]

    if pos[1] + dy < 150:
        dy = 150 - pos[1]

    if pos[3] + dy > ALTURA - 45:
        dy = ALTURA - 45 - pos[3]

    tela.move(nave, dx, dy)

# =====================================
# ATIRAR
# =====================================

def atirar():
    pos = tela.bbox(nave)

    if not pos:
        return

    centro = (pos[0] + pos[2]) / 2
    topo = pos[1]

    tag = f"tiro_{random.randint(100000, 999999)}_{frame}"

    # Tiro em pixel art
    tela.create_rectangle(
        centro - 3, topo - 12,
        centro + 3, topo,
        fill="#ffe66d",
        outline="",
        tags=("dinamico", tag)
    )

    tela.create_rectangle(
        centro - 1, topo - 17,
        centro + 1, topo - 12,
        fill="#ffffff",
        outline="",
        tags=("dinamico", tag)
    )

    tiros.append(tag)

# =====================================
# CRIAR INIMIGOS
# =====================================

def criar_inimigo():
    global numero_inimigo

    numero_inimigo += 1

    x = random.randint(50, LARGURA - 110)
    y = 155

    tag = f"inimigo_{numero_inimigo}"

    # Cada inimigo escolhe uma ficha obtida pela API, se houver conexao.
    ficha = random.choice(naves_da_api) if naves_da_api else None
    classe = ficha["classe"] if ficha else None
    desenhar_alienigena(x, y, tag, classe_nave=classe)

    velocidade_base = min(2 + pontos // 150, 7)
    # MGLT controla o bonus, com limite para preservar a jogabilidade.
    bonus = min(3.0, ficha["mglt"] / 40.0) if ficha and ficha["mglt"] is not None else 0.0
    velocidade = min(9.0, velocidade_base + bonus)

    if ficha:
        nome = ficha["nome"][:32]
        tela.itemconfig(texto_nave_api,
                        text=f"SWAPI: {nome} | MGLT: {ficha['mglt_texto']} | Vel: {velocidade:.1f}")

    inimigos.append({
        "tag": tag,
        "velocidade": velocidade,
        "nave_swapi": ficha["nome"] if ficha else None,
    })

# =====================================
# ATUALIZAR INTERFACE
# =====================================

def atualizar_hud():
    tela.itemconfig(
        texto_pontos,
        text=f"SCORE: {pontos:04d}"
    )

    tela.itemconfig(
        texto_vidas,
        text=f"VIDAS: {vidas}"
    )

# =====================================
# EFEITO DE EXPLOSÃO
# =====================================

def explosao(x, y):
    cores = ["#ffe66d", "#ff9f43", "#ff477e"]

    for i in range(7):
        dx = random.randint(-15, 15)
        dy = random.randint(-15, 15)

        tela.create_rectangle(
            x + dx, y + dy,
            x + dx + 5, y + dy + 5,
            fill=random.choice(cores),
            outline="",
            tags="efeito"
        )

    janela.after(150, lambda: tela.delete("efeito"))

# =====================================
# COLISÃO
# =====================================

def colidiu(objeto1, objeto2):
    caixa1 = tela.bbox(objeto1)
    caixa2 = tela.bbox(objeto2)

    if not caixa1 or not caixa2:
        return False

    return (
        caixa1[0] < caixa2[2]
        and caixa1[2] > caixa2[0]
        and caixa1[1] < caixa2[3]
        and caixa1[3] > caixa2[1]
    )

# =====================================
# PERDER VIDA
# =====================================

def perder_vida():
    global vidas

    vidas -= 1
    atualizar_hud()

    if vidas <= 0:
        fim_de_jogo()

# =====================================
# GAME OVER
# =====================================

def fim_de_jogo():
    global jogo_ativo

    jogo_ativo = False
    teclas.clear()

    tela.create_rectangle(
        170, 210, 730, 430,
        fill="#111a30",
        outline="#ff477e",
        width=3,
        tags="fim"
    )

    tela.create_text(
        450, 275,
        text="GAME OVER",
        fill="#ff477e",
        font=("Consolas", 38, "bold"),
        tags="fim"
    )

    tela.create_text(
        450, 335,
        text=f"PONTUACAO FINAL: {pontos}",
        fill="#ffe66d",
        font=("Consolas", 19, "bold"),
        tags="fim"
    )

    tela.create_text(
        450, 385,
        text="PRESSIONE R PARA REINICIAR",
        fill="#00e5ff",
        font=("Consolas", 14, "bold"),
        tags="fim"
    )

# =====================================
# REINICIAR JOGO
# =====================================

def reiniciar():
    global pontos, vidas, frame
    global tempo_tiro, jogo_ativo
    global tiros, inimigos, nave, numero_inimigo

    pontos = 0
    vidas = 3
    frame = 0
    tempo_tiro = 0
    numero_inimigo = 0

    tiros = []
    inimigos = []

    teclas.clear()

    tela.delete("dinamico")
    tela.delete("fim")
    tela.delete("efeito")

    nave = criar_nave()

    jogo_ativo = True

    atualizar_hud()

# =====================================
# TECLADO
# =====================================

def pressionar_tecla(event):
    global tempo_tiro

    tecla = event.keysym.lower()

    if tecla == "r" and not jogo_ativo:
        reiniciar()
        return

    if tecla == "c":
        iniciar_consulta_api()
        return

    if not jogo_ativo:
        return

    teclas.add(tecla)

    if tecla == "space" and tempo_tiro <= 0:
        atirar()
        tempo_tiro = 9

def soltar_tecla(event):
    tecla = event.keysym.lower()
    teclas.discard(tecla)

janela.bind("<KeyPress>", pressionar_tecla)
janela.bind("<KeyRelease>", soltar_tecla)

# =====================================
# LOOP PRINCIPAL
# =====================================

def atualizar_jogo():
    global frame, tempo_tiro, pontos

    processar_resposta_api()

    if jogo_ativo:
        frame += 1

        mover_nave()

        if tempo_tiro > 0:
            tempo_tiro -= 1

        # Disparo contínuo enquanto segura espaço
        if "space" in teclas and tempo_tiro <= 0:
            atirar()
            tempo_tiro = 9

        # Movimento das estrelas
        for estrela in estrelas:
            tela.move(estrela, 0, 1)

            pos = tela.coords(estrela)

            if pos and pos[1] > ALTURA:
                x = random.randint(0, LARGURA)
                tela.coords(estrela, x, 0, x + 3, 3)

        # Criar inimigos
        intervalo = max(18, 48 - pontos // 100)

        if frame % intervalo == 0:
            criar_inimigo()

        # Movimentar tiros
        for tiro in tiros[:]:
            tela.move(tiro, 0, -12)

            pos = tela.bbox(tiro)

            if not pos or pos[3] < 140:
                tela.delete(tiro)
                tiros.remove(tiro)

        # Movimentar inimigos
        for inimigo in inimigos[:]:
            tag = inimigo["tag"]

            if not tela.bbox(tag):
                inimigos.remove(inimigo)
                continue

            tela.move(tag, 0, inimigo["velocidade"])

            pos = tela.bbox(tag)

            # Inimigo chegou ao fim
            if pos and pos[1] > ALTURA:
                tela.delete(tag)
                inimigos.remove(inimigo)
                perder_vida()

                if not jogo_ativo:
                    break

                continue

            # Inimigo atingiu a nave
            if colidiu(tag, nave):
                centro_x = (pos[0] + pos[2]) / 2
                centro_y = (pos[1] + pos[3]) / 2

                explosao(centro_x, centro_y)

                tela.delete(tag)
                inimigos.remove(inimigo)

                perder_vida()

                if not jogo_ativo:
                    break

        # Cada tiro atinge apenas um inimigo.
        # Os outros inimigos continuam na tela.
        for tiro in tiros[:]:
            if not tela.bbox(tiro):
                if tiro in tiros:
                    tiros.remove(tiro)
                continue

            for inimigo in inimigos[:]:
                tag = inimigo["tag"]

                if colidiu(tiro, tag):
                    pos = tela.bbox(tag)

                    if pos:
                        centro_x = (pos[0] + pos[2]) / 2
                        centro_y = (pos[1] + pos[3]) / 2
                        explosao(centro_x, centro_y)

                    # Remove somente o tiro que acertou
                    tela.delete(tiro)

                    if tiro in tiros:
                        tiros.remove(tiro)

                    # Remove somente o inimigo atingido
                    tela.delete(tag)
                    inimigos.remove(inimigo)

                    pontos += 10
                    atualizar_hud()

                    break

    janela.after(16, atualizar_jogo)

# =====================================
# INICIAR
# =====================================

iniciar_consulta_api()
atualizar_jogo()
janela.focus_force()
janela.mainloop()
