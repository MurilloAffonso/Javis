from __future__ import annotations

import json
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont


BASE_DIR = Path(__file__).resolve().parent
FONT_DIR = BASE_DIR / "assets" / "fonts"
OUTPUTS_DIR = BASE_DIR / "outputs"

WIDTH = 1080
HEIGHT = 1350
MARGIN = 92
SOCIAL = "@vempassearjampa"

COLORS = {
    "background": "#0a1628",
    "accent": "#00d4ff",
    "gold": "#f59e0b",
    "text": "#ffffff",
    "muted": "#94a3b8",
}

FONT_URLS = {
    "Montserrat-ExtraBold.ttf": [
        "https://github.com/google/fonts/raw/main/ofl/montserrat/Montserrat%5Bwght%5D.ttf",
    ],
    "Inter-Regular.ttf": [
        "https://github.com/google/fonts/raw/main/ofl/inter/Inter%5Bwght%5D.ttf",
        "https://github.com/google/fonts/raw/main/ofl/inter/Inter%5Bopsz%2Cwght%5D.ttf",
    ],
}

THEMES: list[dict[str, Any]] = [
    {
        "abordagem": "Tutorial",
        "subtema": "Piscinas naturais do Seixas",
        "titulo_capa": "Como acertar o passeio nas piscinas do Seixas",
        "gancho": "A mare certa muda o passeio inteiro. Vem entender antes de reservar.",
        "cta": "MANDA 'MARE' NO WHATS",
        "topicos": [
            {
                "titulo": "Comece pela mare",
                "corpo": "Piscina natural depende de mare baixa. Antes de escolher o dia, confira a janela do passeio e evite chegar quando o mar ja subiu.",
                "bullets": [
                    "Olhe a tabua de mare antes da reserva",
                    "Priorize a saida mais perto da mare baixa",
                    "Confirme horario com a equipe local",
                ],
            },
            {
                "titulo": "Reserve com margem",
                "corpo": "Em alta temporada, as melhores janelas ficam disputadas. Deixar para o ultimo minuto pode limitar o horario ou a vaga.",
                "bullets": [
                    "Fim de semana lota mais rapido",
                    "Familia e grupo precisam se organizar antes",
                    "Vaga boa combina data, mare e embarque",
                ],
            },
            {
                "titulo": "Leve o basico certo",
                "corpo": "O passeio fica mais leve quando voce leva pouca coisa e escolhe itens que podem molhar. Celular protegido salva o dia.",
                "bullets": [
                    "Protetor, toalha e agua",
                    "Bolsa pequena e roupa confortavel",
                    "Capa para celular ou saquinho estanque",
                ],
            },
            {
                "titulo": "Va pronto para fotos",
                "corpo": "O visual costuma render boas fotos, mas luz, tempo e transparencia variam. A melhor estrategia e chegar orientado.",
                "bullets": [
                    "Use roupa clara se quiser destacar no mar",
                    "Evite prometer foto perfeita todo dia",
                    "Aproveite os primeiros minutos no local",
                ],
            },
            {
                "titulo": "Pergunte antes de fechar",
                "corpo": "Seixas e lindo, mas o melhor dia para voce depende da sua data em Joao Pessoa. Uma pergunta simples evita frustracao.",
                "bullets": [
                    "Informe quantas pessoas vao",
                    "Diga sua data de chegada e saida",
                    "Peca orientacao sobre melhor horario",
                ],
            },
        ],
        "legenda_post": (
            "A mare certa muda tudo nas piscinas naturais do Seixas.\n"
            "Com orientacao local, voce escolhe melhor o dia, o horario e o que levar.\n"
            "Quer saber qual janela combina com sua viagem?\n"
            "Manda 'MARE' no WhatsApp pelo link da bio."
        ),
        "hashtags": [
            "#JoaoPessoa",
            "#JoaoPessoaPB",
            "#Seixas",
            "#PiscinasNaturais",
            "#TurismoJoaoPessoa",
            "#PasseiosEmJoaoPessoa",
            "#Paraiba",
            "#RoteiroJoaoPessoa",
        ],
    },
    {
        "abordagem": "Curiosidade",
        "subtema": "Piscinas do Picaozinho",
        "titulo_capa": "Picaozinho nao e so mar bonito",
        "gancho": "O passeio tem horario, travessia, peixinhos e detalhes que fazem diferenca.",
        "cta": "QUERO VER PICAOZINHO",
        "topicos": [
            {
                "titulo": "Fica perto da orla",
                "corpo": "Picaozinho e uma das piscinas naturais mais lembradas por quem fica na regiao de Tambau. A praticidade ajuda muito quem tem poucos dias.",
                "bullets": [
                    "Bom para roteiro curto",
                    "Facil de encaixar na viagem",
                    "Ideal para primeira vez em JP",
                ],
            },
            {
                "titulo": "A travessia faz parte",
                "corpo": "O caminho ate as piscinas ja cria expectativa. Por isso, horario e organizacao importam desde antes do embarque.",
                "bullets": [
                    "Chegue com antecedencia",
                    "Use roupa pratica para embarcar",
                    "Confirme ponto de encontro",
                ],
            },
            {
                "titulo": "Peixinhos aparecem com cuidado",
                "corpo": "A vida marinha e parte da experiencia, mas precisa de respeito. Passeio bonito tambem e passeio responsavel.",
                "bullets": [
                    "Nao toque nos animais",
                    "Evite alimentar peixes",
                    "Siga as orientacoes do guia",
                ],
            },
            {
                "titulo": "Familia aproveita melhor preparada",
                "corpo": "Com crianca, o passeio fica mais tranquilo quando a familia sabe duracao, embarque e itens basicos antes de sair.",
                "bullets": [
                    "Leve agua e protecao solar",
                    "Combine horario de retorno",
                    "Pergunte sobre colete e seguranca",
                ],
            },
            {
                "titulo": "Nao depende so de vontade",
                "corpo": "A natureza manda no ritmo. Mar, vento e mare podem mudar a experiencia, entao vale decidir com orientacao local.",
                "bullets": [
                    "A melhor data muda toda semana",
                    "Clima tambem entra na conta",
                    "Reserva boa comeca com informacao",
                ],
            },
        ],
        "legenda_post": (
            "Picaozinho parece simples: mar bonito, barco e fotos.\n"
            "Mas o passeio melhora muito quando voce entende horario, mare e travessia.\n"
            "Voce quer fazer Picaozinho em qual dia da viagem?\n"
            "Chama no WhatsApp e a gente orienta."
        ),
        "hashtags": [
            "#Picaozinho",
            "#JoaoPessoa",
            "#JoaoPessoaPB",
            "#PiscinasNaturaisJoaoPessoa",
            "#PasseiosEmJoaoPessoa",
            "#TurismoNaParaiba",
            "#ViagemEmFamilia",
            "#NordesteBrasil",
        ],
    },
    {
        "abordagem": "Tendencia",
        "subtema": "Litoral Norte",
        "titulo_capa": "Litoral Norte e o passeio para sair do obvio",
        "gancho": "Quando voce quer mais praia, estrada bonita e um dia com cara de descoberta.",
        "cta": "MANDA 'LITORAL' NO WHATS",
        "topicos": [
            {
                "titulo": "Mais que uma parada",
                "corpo": "O Litoral Norte combina praias, mirantes e ritmos diferentes no mesmo roteiro. E uma boa escolha para quem ja viu a orla central.",
                "bullets": [
                    "Visual muda ao longo do dia",
                    "Bom para quem gosta de explorar",
                    "Rende conteudo e memoria",
                ],
            },
            {
                "titulo": "Perfil aventureiro combina",
                "corpo": "Esse passeio conversa com quem quer sair do basico sem complicar a viagem. A ideia e aproveitar com guia e rota clara.",
                "bullets": [
                    "Otimo para casais e grupos",
                    "Menos cara de passeio apressado",
                    "Mais variedade de paisagem",
                ],
            },
            {
                "titulo": "O tempo precisa ser pensado",
                "corpo": "Como envolve deslocamento, vale separar o dia com calma. Entrar espremido na agenda pode tirar o melhor da experiencia.",
                "bullets": [
                    "Reserve uma janela maior",
                    "Evite marcar compromisso colado",
                    "Confirme horario de saida e retorno",
                ],
            },
            {
                "titulo": "Fotos ficam diferentes",
                "corpo": "Nem todo post precisa ser piscina natural. Praia aberta, coqueiro, estrada e por do sol tambem vendem Joao Pessoa.",
                "bullets": [
                    "Leve celular carregado",
                    "Pense em roupa confortavel",
                    "Aproveite pontos de parada",
                ],
            },
            {
                "titulo": "Roteiro bom tem curadoria",
                "corpo": "A diferenca esta em saber onde parar, quanto tempo ficar e como montar o dia sem correria desnecessaria.",
                "bullets": [
                    "Pergunte o roteiro antes",
                    "Avise seu perfil de viagem",
                    "Combine expectativa com realidade",
                ],
            },
        ],
        "legenda_post": (
            "Nem todo passeio em Joao Pessoa precisa terminar no mesmo lugar.\n"
            "O Litoral Norte e para quem quer explorar mais, com rota clara e tempo bem usado.\n"
            "Voce prefere praia tranquila ou passeio cheio de paradas?\n"
            "Manda 'LITORAL' no WhatsApp."
        ),
        "hashtags": [
            "#LitoralNortePB",
            "#JoaoPessoa",
            "#PraiasDaParaiba",
            "#TurismoJoaoPessoa",
            "#RoteiroJoaoPessoa",
            "#NordesteBrasil",
            "#Paraiba",
            "#PasseiosEmJoaoPessoa",
        ],
    },
    {
        "abordagem": "Tutorial",
        "subtema": "Combo Duplo",
        "titulo_capa": "Seixas + Picaozinho no roteiro sem se enrolar",
        "gancho": "Da para combinar passeios, mas so quando data, mare e tempo conversam.",
        "cta": "PEDE O COMBO CERTO",
        "topicos": [
            {
                "titulo": "Nao junte por impulso",
                "corpo": "Combo bom nao e empilhar passeio. E montar uma sequencia que respeita mare, deslocamento e energia do grupo.",
                "bullets": [
                    "Confira a janela de mare",
                    "Veja se o grupo aguenta o ritmo",
                    "Evite prometer dois lugares a qualquer custo",
                ],
            },
            {
                "titulo": "Compare os perfis",
                "corpo": "Seixas e Picaozinho podem parecer parecidos para quem ainda nao foi, mas a experiencia, o acesso e o clima do passeio mudam.",
                "bullets": [
                    "Um pode encaixar melhor na sua data",
                    "Familia pode preferir praticidade",
                    "Casal pode buscar visual e fotos",
                ],
            },
            {
                "titulo": "Use a agenda a seu favor",
                "corpo": "Quem fica 3 a 7 dias em Joao Pessoa tem margem para escolher melhor. O erro e reservar sem olhar a viagem inteira.",
                "bullets": [
                    "Informe chegada e volta",
                    "Separe os dias mais livres",
                    "Deixe plano B se o clima virar",
                ],
            },
            {
                "titulo": "Pense no descanso",
                "corpo": "Passeio bom tambem precisa terminar bem. Correr demais pode transformar um roteiro bonito em cansaco.",
                "bullets": [
                    "Evite agenda colada com aeroporto",
                    "Combine almoco e retorno",
                    "Leve agua e protetor",
                ],
            },
            {
                "titulo": "Fale com quem opera localmente",
                "corpo": "A melhor combinacao muda conforme semana, mare e disponibilidade. Com orientacao, voce fecha com menos duvida.",
                "bullets": [
                    "Mande a palavra COMBO",
                    "Diga quantas pessoas vao",
                    "Peca a melhor opcao para sua data",
                ],
            },
        ],
        "legenda_post": (
            "Combo bom nao e fazer tudo correndo.\n"
            "E encaixar Seixas, Picaozinho e sua agenda do jeito certo.\n"
            "Voce tem quantos dias em Joao Pessoa?\n"
            "Manda 'COMBO' no WhatsApp."
        ),
        "hashtags": [
            "#ComboJoaoPessoa",
            "#Seixas",
            "#Picaozinho",
            "#PiscinasNaturais",
            "#JoaoPessoaPB",
            "#TurismoJoaoPessoa",
            "#RoteiroJoaoPessoa",
            "#PasseiosEmJoaoPessoa",
        ],
    },
    {
        "abordagem": "Tutorial",
        "subtema": "Dicas praticas",
        "titulo_capa": "Checklist simples para nao passar perrengue no passeio",
        "gancho": "O que levar, o que evitar e o que perguntar antes de sair.",
        "cta": "SALVA ESSE CHECKLIST",
        "topicos": [
            {
                "titulo": "Leve pouco e leve certo",
                "corpo": "Em passeio de mar, excesso atrapalha. O ideal e levar o que resolve calor, sol, agua e pequenas esperas.",
                "bullets": [
                    "Protetor solar e agua",
                    "Toalha compacta",
                    "Roupa leve que possa molhar",
                ],
            },
            {
                "titulo": "Proteja o celular",
                "corpo": "A foto e importante, mas o celular tambem. Uma protecao simples evita dor de cabeca no embarque e dentro do mar.",
                "bullets": [
                    "Use capinha impermeavel",
                    "Carregue bateria antes",
                    "Evite levar documento solto",
                ],
            },
            {
                "titulo": "Com crianca, antecipe",
                "corpo": "Familia aproveita melhor quando ja sabe tempo de passeio, ponto de encontro e estrutura antes de chegar.",
                "bullets": [
                    "Pergunte sobre seguranca",
                    "Leve lanche simples se precisar",
                    "Combine pausas e horario de retorno",
                ],
            },
            {
                "titulo": "Pergunte sobre a mare",
                "corpo": "Mare nao e detalhe tecnico. Ela define o melhor horario e pode mudar a experiencia nas piscinas naturais.",
                "bullets": [
                    "Nao escolha so pelo menor preco",
                    "Confirme a janela do dia",
                    "Tenha flexibilidade quando puder",
                ],
            },
            {
                "titulo": "Evite promessas milagrosas",
                "corpo": "Mar bonito depende de natureza. Uma operadora seria orienta sem vender certeza absoluta sobre clima ou transparencia.",
                "bullets": [
                    "Desconfie de garantia total",
                    "Prefira orientacao clara",
                    "Pergunte o que acontece se o clima mudar",
                ],
            },
        ],
        "legenda_post": (
            "Vai fazer passeio de mar em Joao Pessoa?\n"
            "Esse checklist evita os perrengues mais comuns e deixa o dia mais leve.\n"
            "Qual item voce sempre esquece quando viaja?\n"
            "Salva e chama no WhatsApp para escolher sua data."
        ),
        "hashtags": [
            "#DicasDeViagem",
            "#JoaoPessoa",
            "#JoaoPessoaPB",
            "#PiscinasNaturais",
            "#ViagemEmFamilia",
            "#TurismoJoaoPessoa",
            "#PraiasDaParaiba",
            "#RoteiroJoaoPessoa",
        ],
    },
    {
        "abordagem": "Curiosidade",
        "subtema": "Bastidores",
        "titulo_capa": "O passeio comeca antes de voce embarcar",
        "gancho": "Enquanto o turista se arruma, a equipe ja esta checando rota, horario e mar.",
        "cta": "VEM COM A GENTE",
        "topicos": [
            {
                "titulo": "A mare e conferida antes",
                "corpo": "A organizacao comeca olhando a janela certa. Isso evita improviso e ajuda o turista a entender o melhor horario.",
                "bullets": [
                    "Mare baixa orienta o plano",
                    "Horario precisa ser claro",
                    "Mudanca de clima exige comunicacao",
                ],
            },
            {
                "titulo": "O embarque tem ritmo",
                "corpo": "Um bom passeio nao comeca na pressa. Ponto de encontro, lista e orientacao deixam a saida mais tranquila.",
                "bullets": [
                    "Chegue alguns minutos antes",
                    "Tenha documento e contato facil",
                    "Escute as instrucoes iniciais",
                ],
            },
            {
                "titulo": "Guia evita duvida",
                "corpo": "Turista de primeira viagem costuma ter perguntas simples. O cuidado esta em responder antes de virar inseguranca.",
                "bullets": [
                    "Onde pisar",
                    "Quanto tempo ficar",
                    "O que fazer se cansar",
                ],
            },
            {
                "titulo": "Seguranca vem antes da foto",
                "corpo": "Foto linda importa, mas nao passa na frente de orientacao, limite do grupo e respeito ao ambiente.",
                "bullets": [
                    "Siga a area orientada",
                    "Nao force pose perigosa",
                    "Respeite mar e vida marinha",
                ],
            },
            {
                "titulo": "Experiencia boa parece simples",
                "corpo": "Quando tudo flui, o turista so percebe o mar, as fotos e a memoria. Esse e o valor de ter bastidor organizado.",
                "bullets": [
                    "Menos duvida no caminho",
                    "Mais tempo aproveitando",
                    "Mais confianca para reservar",
                ],
            },
        ],
        "legenda_post": (
            "A parte que voce nao ve no Instagram tambem faz o passeio acontecer.\n"
            "Mare, horario, embarque e orientacao precisam estar alinhados antes da primeira foto.\n"
            "Voce gosta de ver bastidores dos passeios?\n"
            "Vem com a gente pelo WhatsApp."
        ),
        "hashtags": [
            "#Bastidores",
            "#JoaoPessoa",
            "#TurismoJoaoPessoa",
            "#PasseiosEmJoaoPessoa",
            "#PiscinasNaturais",
            "#Paraiba",
            "#ViagemSegura",
            "#VemPassearJampa",
        ],
    },
    {
        "abordagem": "Tendencia",
        "subtema": "Prova social",
        "titulo_capa": "A melhor propaganda e turista voltando feliz",
        "gancho": "Antes de reservar, muita gente quer saber se o passeio e tranquilo de verdade.",
        "cta": "QUERO VIVER ESSE PASSEIO",
        "topicos": [
            {
                "titulo": "Confianca vem de detalhe",
                "corpo": "Quem compra pelo WhatsApp quer clareza. Explicar horario, roteiro e condicoes reduz inseguranca antes da reserva.",
                "bullets": [
                    "Resposta direta",
                    "Informacao sem exagero",
                    "Orientacao sobre mare e clima",
                ],
            },
            {
                "titulo": "Familia olha seguranca",
                "corpo": "Para quem viaja com crianca, a duvida nao e so beleza. E saber se o passeio cabe no ritmo da familia.",
                "bullets": [
                    "Perguntas precisam ser acolhidas",
                    "Horario deve ser claro",
                    "Orientacao local faz diferenca",
                ],
            },
            {
                "titulo": "Casal quer memoria",
                "corpo": "Muita gente procura um passeio bonito, tranquilo e facil de lembrar depois. O visual ajuda, mas a experiencia completa pesa.",
                "bullets": [
                    "Fotos bonitas contam",
                    "Sem correria fica melhor",
                    "Roteiro alinhado evita stress",
                ],
            },
            {
                "titulo": "Grupo quer praticidade",
                "corpo": "Quanto mais gente, maior a chance de duvida. Centralizar a orientacao ajuda o grupo a decidir sem confusao.",
                "bullets": [
                    "Uma pessoa pode chamar no WhatsApp",
                    "Datas e vagas precisam bater",
                    "Combo pode economizar tempo",
                ],
            },
            {
                "titulo": "Depoimento bom vira roteiro",
                "corpo": "Quando o cliente volta feliz, ele mostra o caminho para o proximo turista: reservar melhor, sair no horario certo e curtir.",
                "bullets": [
                    "Prova social reduz medo",
                    "Experiencia real inspira reserva",
                    "Atendimento claro vende sem forcar",
                ],
            },
        ],
        "legenda_post": (
            "Turista feliz conta mais que qualquer promessa.\n"
            "O passeio certo combina orientacao, horario, seguranca e aquele visual que Joao Pessoa entrega quando a natureza ajuda.\n"
            "Voce ja fez passeio de piscina natural por aqui?\n"
            "Chama no WhatsApp e veja as vagas da semana."
        ),
        "hashtags": [
            "#VemPassearJampa",
            "#JoaoPessoa",
            "#JoaoPessoaPB",
            "#TurismoJoaoPessoa",
            "#PiscinasNaturais",
            "#ViagemEmFamilia",
            "#PasseiosEmJoaoPessoa",
            "#NordesteBrasil",
        ],
    },
]


def hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))


def download_font(file_name: str, urls: list[str]) -> None:
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    path = FONT_DIR / file_name
    if path.exists():
        return

    for url in urls:
        try:
            with urllib.request.urlopen(url, timeout=20) as response:
                data = response.read()
            if len(data) < 50_000 or data[:1] == b"<":
                raise ValueError("arquivo de fonte invalido ou incompleto")
            path.write_bytes(data)
            return
        except Exception as exc:
            print(f"AVISO: falha ao baixar {file_name} de {url}: {exc}")

    print(f"AVISO: usando fonte PIL default para {file_name}")


def prepare_fonts() -> None:
    for file_name, urls in FONT_URLS.items():
        download_font(file_name, urls)


def fallback_font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def apply_variation(font: ImageFont.FreeTypeFont, weight: int) -> None:
    try:
        axes = font.get_variation_axes()
    except Exception:
        return

    values: list[int] = []
    for axis in axes:
        raw_name = axis.get("name", b"")
        name = raw_name.decode("utf-8", "ignore").lower() if isinstance(raw_name, bytes) else str(raw_name).lower()
        default_value = int(axis.get("default", weight))
        min_value = int(axis.get("minimum", default_value))
        max_value = int(axis.get("maximum", default_value))
        if "weight" in name or "wght" in name:
            values.append(max(min(weight, max_value), min_value))
        else:
            values.append(default_value)

    try:
        font.set_variation_by_axes(values)
    except Exception:
        return


def font(file_name: str, size: int, weight: int = 400) -> ImageFont.ImageFont:
    path = FONT_DIR / file_name
    if path.exists():
        try:
            loaded = ImageFont.truetype(str(path), size=size)
            if isinstance(loaded, ImageFont.FreeTypeFont):
                apply_variation(loaded, weight)
            return loaded
        except Exception as exc:
            print(f"AVISO: falha ao carregar {file_name}: {exc}. Usando fonte PIL default.")
    return fallback_font(size)


def text_size(draw: ImageDraw.ImageDraw, text: str, text_font: ImageFont.ImageFont) -> tuple[int, int]:
    bbox = draw.textbbox((0, 0), text, font=text_font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


def wrap_text(draw: ImageDraw.ImageDraw, text: str, text_font: ImageFont.ImageFont, max_width: int) -> list[str]:
    lines: list[str] = []
    for paragraph in text.splitlines() or [text]:
        words = paragraph.split()
        if not words:
            lines.append("")
            continue

        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            if text_size(draw, candidate, text_font)[0] <= max_width:
                current = candidate
            else:
                lines.append(current)
                current = word
        lines.append(current)
    return lines


def fit_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    file_name: str,
    start_size: int,
    min_size: int,
    max_width: int,
    max_lines: int,
    weight: int = 400,
) -> ImageFont.ImageFont:
    for size in range(start_size, min_size - 1, -2):
        candidate = font(file_name, size, weight=weight)
        if len(wrap_text(draw, text, candidate, max_width)) <= max_lines:
            return candidate
    return font(file_name, min_size, weight=weight)


def draw_wrapped_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[int, int],
    text_font: ImageFont.ImageFont,
    fill: str,
    max_width: int,
    line_spacing: int = 14,
    align: str = "left",
) -> int:
    x, y = xy
    lines = wrap_text(draw, text, text_font, max_width)
    line_height = text_size(draw, "Ag", text_font)[1] + line_spacing
    for line in lines:
        width, _ = text_size(draw, line, text_font)
        if align == "center":
            line_x = x + (max_width - width) // 2
        elif align == "right":
            line_x = x + max_width - width
        else:
            line_x = x
        draw.text((line_x, y), line, font=text_font, fill=fill)
        y += line_height
    return y


def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    center_x: int,
    y: int,
    text_font: ImageFont.ImageFont,
    fill: str,
) -> int:
    width, height = text_size(draw, text, text_font)
    draw.text((center_x - width // 2, y), text, font=text_font, fill=fill)
    return y + height


def new_card() -> Image.Image:
    return Image.new("RGB", (WIDTH, HEIGHT), COLORS["background"])


def add_soft_layers(img: Image.Image, cover: bool = False) -> None:
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    accent = hex_to_rgb(COLORS["accent"])
    gold = hex_to_rgb(COLORS["gold"])

    alpha_top = 34 if cover else 18
    alpha_bottom = 25 if cover else 12
    draw.rectangle((0, 0, WIDTH, HEIGHT // 2 + 120), fill=(*accent, alpha_top))
    draw.rectangle((0, HEIGHT // 3, WIDTH, HEIGHT), fill=(*gold, alpha_bottom))
    draw.rectangle((MARGIN // 2, 54, WIDTH - MARGIN // 2, HEIGHT - 54), outline=(*accent, 38), width=2)

    img.paste(Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB"))


def draw_footer(draw: ImageDraw.ImageDraw) -> None:
    small = font("Inter-Regular.ttf", 25, weight=400)
    y = HEIGHT - 92
    draw.line((MARGIN, y, WIDTH - MARGIN, y), fill=COLORS["accent"], width=2)
    draw_centered_text(draw, SOCIAL, WIDTH // 2, y + 24, small, COLORS["muted"])


def draw_tag(draw: ImageDraw.ImageDraw, text: str, x: int, y: int) -> None:
    tag_font = font("Inter-Regular.ttf", 24, weight=400)
    padding_x = 24
    padding_y = 14
    text_width, text_height = text_size(draw, text, tag_font)
    draw.rounded_rectangle(
        (x, y, x + text_width + padding_x * 2, y + text_height + padding_y * 2),
        radius=12,
        fill="#10233d",
        outline=COLORS["accent"],
        width=2,
    )
    draw.text((x + padding_x, y + padding_y - 1), text, font=tag_font, fill=COLORS["text"])


def draw_cover(theme: dict[str, Any], output_path: Path) -> None:
    img = new_card()
    add_soft_layers(img, cover=True)
    draw = ImageDraw.Draw(img)

    draw_tag(draw, "TURISMO LOCAL | JOAO PESSOA/PB", MARGIN, 82)

    title_font = fit_font(
        draw,
        theme["titulo_capa"],
        "Montserrat-ExtraBold.ttf",
        82,
        52,
        WIDTH - MARGIN * 2,
        4,
        weight=800,
    )
    subtitle_font = font("Inter-Regular.ttf", 38, weight=400)

    title_lines = wrap_text(draw, theme["titulo_capa"], title_font, WIDTH - MARGIN * 2)
    title_line_height = text_size(draw, "Ag", title_font)[1] + 16
    title_block_height = title_line_height * len(title_lines)
    title_y = 410 - title_block_height // 2

    y = draw_wrapped_text(
        draw,
        theme["titulo_capa"],
        (MARGIN, title_y),
        title_font,
        COLORS["text"],
        WIDTH - MARGIN * 2,
        line_spacing=16,
        align="center",
    )
    y += 44
    draw_wrapped_text(
        draw,
        theme["gancho"],
        (MARGIN + 36, y),
        subtitle_font,
        COLORS["muted"],
        WIDTH - (MARGIN + 36) * 2,
        line_spacing=12,
        align="center",
    )

    bar_y = HEIGHT - 210
    draw.rectangle((MARGIN, bar_y, WIDTH - MARGIN, bar_y + 12), fill=COLORS["accent"])
    draw.text((MARGIN, bar_y + 32), theme["abordagem"].upper(), font=font("Inter-Regular.ttf", 28), fill=COLORS["gold"])
    draw_footer(draw)
    img.save(output_path)


def draw_bullet(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    max_width: int,
    bullet_font: ImageFont.ImageFont,
    body_font: ImageFont.ImageFont,
) -> int:
    draw.ellipse((x + 6, y + 14, x + 22, y + 30), fill=COLORS["accent"])
    return draw_wrapped_text(
        draw,
        text,
        (x + 46, y),
        body_font,
        COLORS["text"],
        max_width - 46,
        line_spacing=10,
    ) + 14


def draw_content_card(theme: dict[str, Any], topic: dict[str, Any], index: int, output_path: Path) -> None:
    img = new_card()
    add_soft_layers(img)
    draw = ImageDraw.Draw(img)

    number_font = font("Montserrat-ExtraBold.ttf", 128, weight=800)
    label_font = font("Inter-Regular.ttf", 25, weight=400)
    title_font = fit_font(
        draw,
        topic["titulo"],
        "Montserrat-ExtraBold.ttf",
        58,
        42,
        WIDTH - MARGIN * 2,
        2,
        weight=800,
    )
    body_font = font("Inter-Regular.ttf", 35, weight=400)
    bullet_font = font("Montserrat-ExtraBold.ttf", 38, weight=800)
    bullet_text_font = font("Inter-Regular.ttf", 31, weight=400)

    draw.text((MARGIN, 92), f"CARD {index + 1}/7", font=label_font, fill=COLORS["muted"])
    draw.text((MARGIN, 138), f"{index:02d}", font=number_font, fill=COLORS["accent"])
    draw.line((MARGIN, 292, WIDTH - MARGIN, 292), fill=COLORS["gold"], width=3)

    y = 338
    y = draw_wrapped_text(
        draw,
        topic["titulo"],
        (MARGIN, y),
        title_font,
        COLORS["text"],
        WIDTH - MARGIN * 2,
        line_spacing=12,
    )
    y += 36
    y = draw_wrapped_text(
        draw,
        topic["corpo"],
        (MARGIN, y),
        body_font,
        COLORS["muted"],
        WIDTH - MARGIN * 2,
        line_spacing=14,
    )
    y += 48

    for bullet in topic["bullets"]:
        y = draw_bullet(draw, bullet, MARGIN + 8, y, WIDTH - MARGIN * 2, bullet_font, bullet_text_font)

    draw_footer(draw)
    img.save(output_path)


def draw_cta_card(theme: dict[str, Any], output_path: Path) -> None:
    img = new_card()
    add_soft_layers(img, cover=True)
    draw = ImageDraw.Draw(img)

    draw_tag(draw, "PROXIMO PASSO", MARGIN, 82)

    title = "Bora transformar essa dica em passeio?"
    title_font = fit_font(draw, title, "Montserrat-ExtraBold.ttf", 76, 54, WIDTH - MARGIN * 2, 3, weight=800)
    body_font = font("Inter-Regular.ttf", 38, weight=400)
    button_font = fit_font(draw, theme["cta"], "Montserrat-ExtraBold.ttf", 46, 34, 760, 1, weight=800)

    y = 340
    y = draw_wrapped_text(
        draw,
        title,
        (MARGIN, y),
        title_font,
        COLORS["text"],
        WIDTH - MARGIN * 2,
        line_spacing=14,
        align="center",
    )
    y += 46
    y = draw_wrapped_text(
        draw,
        "A gente te ajuda a escolher data, horario e passeio sem complicar sua viagem em Joao Pessoa.",
        (MARGIN + 28, y),
        body_font,
        COLORS["muted"],
        WIDTH - (MARGIN + 28) * 2,
        line_spacing=14,
        align="center",
    )

    button_w = WIDTH - MARGIN * 2
    button_h = 132
    button_x = MARGIN
    button_y = y + 78
    draw.rectangle((button_x, button_y, button_x + button_w, button_y + button_h), fill=COLORS["accent"])
    button_text_w, button_text_h = text_size(draw, theme["cta"], button_font)
    draw.text(
        (WIDTH // 2 - button_text_w // 2, button_y + button_h // 2 - button_text_h // 2 - 3),
        theme["cta"],
        font=button_font,
        fill=COLORS["background"],
    )

    note_font = font("Inter-Regular.ttf", 31, weight=400)
    draw_wrapped_text(
        draw,
        "Salva este carrossel e envia para quem vai viajar com voce.",
        (MARGIN + 38, button_y + button_h + 64),
        note_font,
        COLORS["text"],
        WIDTH - (MARGIN + 38) * 2,
        line_spacing=10,
        align="center",
    )

    draw_footer(draw)
    img.save(output_path)


def write_caption(theme: dict[str, Any], output_dir: Path) -> None:
    caption = theme["legenda_post"].strip()
    hashtags = " ".join(theme["hashtags"])
    (output_dir / "legenda.txt").write_text(f"{caption}\n\n{hashtags}\n", encoding="utf-8")


def write_meta(theme: dict[str, Any], output_dir: Path, today: date, generated_cards: list[str]) -> None:
    meta = {
        "data": today.isoformat(),
        "tema": theme["titulo_capa"],
        "subtema": theme["subtema"],
        "abordagem": theme["abordagem"],
        "cards_gerados": generated_cards,
        "quantidade_cards": len(generated_cards),
    }
    (output_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    today = date.today()
    theme = THEMES[today.weekday()]
    output_dir = OUTPUTS_DIR / f"carrossel-{today.isoformat()}"
    output_dir.mkdir(parents=True, exist_ok=True)

    prepare_fonts()

    generated_cards: list[str] = []
    cover_name = "card_01.png"
    draw_cover(theme, output_dir / cover_name)
    generated_cards.append(cover_name)

    for offset, topic in enumerate(theme["topicos"], start=2):
        file_name = f"card_{offset:02d}.png"
        draw_content_card(theme, topic, offset - 1, output_dir / file_name)
        generated_cards.append(file_name)

    cta_name = "card_07.png"
    draw_cta_card(theme, output_dir / cta_name)
    generated_cards.append(cta_name)

    write_caption(theme, output_dir)
    write_meta(theme, output_dir, today, generated_cards)

    relative_output = f"_projetos/cerebro-jampa/outputs/carrossel-{today.isoformat()}/"
    print(f"Tema do dia: {theme['titulo_capa']}")
    print(f"Abordagem: {theme['abordagem']}")
    print(f"Cards gerados: {len(generated_cards)}")
    print(f"Pasta: {relative_output}")


if __name__ == "__main__":
    main()
