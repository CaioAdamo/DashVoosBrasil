# -*- coding: utf-8 -*-
"""Gera o PDF 'Guia de Apresentação' do projeto DashVoosBrasil."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak, ListFlowable, ListItem, HRFlowable)

NAVY = colors.HexColor("#0A2342")
AZUL = colors.HexColor("#1565C0")
AZUL2 = colors.HexColor("#2196F3")
CINZA = colors.HexColor("#5B6B7F")
BG = colors.HexColor("#EAF2FB")
VERDE = colors.HexColor("#1FA37C")

ARQ = "DashVoosBrasil_Guia_Apresentacao.pdf"
MARGEM = 1.9 * cm
CW = A4[0] - 2 * MARGEM  # largura útil

ss = getSampleStyleSheet()
S = {}
S["body"] = ParagraphStyle("body", parent=ss["Normal"], fontName="Helvetica", fontSize=10.5,
                           leading=15.5, alignment=TA_JUSTIFY, textColor=colors.HexColor("#1A2332"),
                           spaceAfter=7)
S["h1"] = ParagraphStyle("h1", parent=ss["Heading1"], fontName="Helvetica-Bold", fontSize=15,
                         textColor=NAVY, spaceBefore=16, spaceAfter=7, leading=18)
S["h2"] = ParagraphStyle("h2", parent=ss["Heading2"], fontName="Helvetica-Bold", fontSize=12,
                         textColor=AZUL, spaceBefore=10, spaceAfter=4, leading=15)
S["bullet"] = ParagraphStyle("bullet", parent=S["body"], leftIndent=16, bulletIndent=3,
                             spaceAfter=4, alignment=TA_LEFT)
S["callout"] = ParagraphStyle("callout", parent=S["body"], fontSize=10, leading=14.5,
                              textColor=NAVY, spaceAfter=0, alignment=TA_LEFT)
S["banner_t"] = ParagraphStyle("bt", parent=ss["Title"], fontName="Helvetica-Bold", fontSize=30,
                               textColor=colors.white, leading=34, spaceAfter=0)
S["banner_s"] = ParagraphStyle("bs", parent=ss["Normal"], fontName="Helvetica", fontSize=13,
                               textColor=colors.HexColor("#BBD3EA"), leading=17)
S["lead"] = ParagraphStyle("lead", parent=S["body"], fontSize=11.5, leading=17, textColor=CINZA)
S["small"] = ParagraphStyle("small", parent=S["body"], fontSize=8.5, leading=11, textColor=CINZA,
                            alignment=TA_LEFT)
S["th"] = ParagraphStyle("th", parent=S["body"], fontName="Helvetica-Bold", fontSize=9.5,
                         textColor=colors.white, leading=12, spaceAfter=0, alignment=TA_LEFT)
S["td"] = ParagraphStyle("td", parent=S["body"], fontSize=9.5, leading=12.5, spaceAfter=0,
                         alignment=TA_LEFT)
S["tdb"] = ParagraphStyle("tdb", parent=S["td"], fontName="Helvetica-Bold", textColor=NAVY)

story = []


def H1(txt): story.append(Paragraph(txt, S["h1"]))
def H2(txt): story.append(Paragraph(txt, S["h2"]))
def P(txt): story.append(Paragraph(txt, S["body"]))
def SP(h=6): story.append(Spacer(1, h))


def lista(itens):
    story.append(ListFlowable(
        [ListItem(Paragraph(t, S["bullet"]), value="•") for t in itens],
        bulletType="bullet", bulletColor=AZUL2, leftIndent=10, spaceAfter=6))


def callout(txt, rotulo="Para a banca:", cor=AZUL2, fundo=BG):
    p = Paragraph(f'<b><font color="{cor.hexval()}">{rotulo}</font></b> {txt}', S["callout"])
    t = Table([[p]], colWidths=[CW])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), fundo),
        ("LINEBEFORE", (0, 0), (0, -1), 3, cor),
        ("LEFTPADDING", (0, 0), (-1, -1), 11), ("RIGHTPADDING", (0, 0), (-1, -1), 11),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t)
    SP(8)


def tabela(linhas, larguras, cabecalho=True):
    dados = []
    for i, row in enumerate(linhas):
        est = S["th"] if (cabecalho and i == 0) else S["td"]
        dados.append([Paragraph(c, est) for c in row])
    t = Table(dados, colWidths=larguras, repeatRows=1 if cabecalho else 0)
    estilo = [
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1 if cabecalho else 0), (-1, -1),
         [colors.white, colors.HexColor("#F4F8FC")]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.4, colors.HexColor("#DCE6F0")),
    ]
    if cabecalho:
        estilo += [("BACKGROUND", (0, 0), (-1, 0), NAVY)]
    t.setStyle(TableStyle(estilo))
    story.append(t)
    SP(10)


# ───────────────────────────── CAPA / BANNER ─────────────────────────────
banner = Table([[Paragraph("DashVoosBrasil", S["banner_t"])],
                [Paragraph("Guia de Apresentação do Projeto", S["banner_s"])]],
               colWidths=[CW])
banner.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, -1), NAVY),
    ("LEFTPADDING", (0, 0), (-1, -1), 20), ("RIGHTPADDING", (0, 0), (-1, -1), 20),
    ("TOPPADDING", (0, 0), (0, 0), 22), ("BOTTOMPADDING", (0, 0), (0, 0), 2),
    ("TOPPADDING", (0, 1), (0, 1), 2), ("BOTTOMPADDING", (0, 1), (0, 1), 22),
]))
story.append(banner)
SP(4)
faixa = Table([[""]], colWidths=[CW], rowHeights=[5])
faixa.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), AZUL2)]))
story.append(faixa)
SP(16)
P('<b>Projeto Final — Banco de Dados Avançado.</b> Este guia explica o projeto de forma '
  'didática, sem jargão: o que ele é, como foi montado (a arquitetura), o raciocínio de '
  'programação por trás de cada parte e <b>em qual arquivo cada funcionalidade está</b> — '
  'pensado para uma apresentação a uma banca e para ser entendido por qualquer pessoa.')
SP(2)
story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#DCE6F0")))
SP(8)

# ───────────────────────────── 1 ─────────────────────────────
H1("1. O que é o projeto, em uma frase")
P("É um sistema que pega os dados públicos de <b>todos os voos comerciais do Brasil</b> "
  "(divulgados pela ANAC), faz uma faxina e uma organização nesses dados, e os apresenta em "
  "<b>dois painéis interativos</b> no navegador, onde qualquer pessoa pode explorar, filtrar e "
  "descobrir padrões da aviação brasileira — são cerca de <b>3 milhões de voos</b>, de 2022 ao "
  "início de 2025.")
P("O ponto importante para a banca: o projeto não é apenas um gráfico bonito. Ele é um "
  "<b>caminho completo do dado</b>, da coleta bruta até a informação pronta para decisão.")

# ───────────────────────────── 2 ─────────────────────────────
H1("2. A grande ideia: pense em um restaurante")
P("A melhor forma de entender a arquitetura é imaginar um <b>restaurante</b>. O dado cru é o "
  "ingrediente que chega do fornecedor; o painel na tela é o prato servido. Entre um e outro "
  "existe uma cozinha organizada, com etapas bem separadas. Cada arquivo do projeto é uma "
  "estação dessa cozinha:")
tabela([
    ["Estação da cozinha", "Arquivo", "O que faz"],
    ["O entregador", "coleta_dados.py", "Vai até a ANAC e baixa os dados"],
    ["A faxina e o preparo", "prepara_dados.py", "Limpa e organiza os ingredientes"],
    ["A despensa inteligente", "lib_dados.py", "Enriquece e guarda tudo pronto para uso rápido"],
    ["O prato executivo", "dashboard_visao_geral.py", "Painel resumido, visão de diretoria"],
    ["O prato de degustação", "dashboard_exploratorio.py", "Painel detalhado, 8 abas para explorar"],
], [3.6 * cm, 5.0 * cm, CW - 8.6 * cm])
P("O raciocínio central por trás disso tem um nome: <b>separação de responsabilidades</b>. Cada "
  "arquivo faz uma coisa só, e bem feita. Quem baixa não limpa; quem limpa não desenha gráfico. "
  "É o que diferencia um projeto amador (tudo num arquivo bagunçado) de um profissional.")

# ───────────────────────────── 3 ─────────────────────────────
H1("3. O caminho do dado, etapa por etapa")

H2("Etapa 1 — A coleta (arquivo coleta_dados.py)")
P("A ANAC publica um arquivo para cada mês. Baixar isso na mão seria trabalhoso e sujeito a "
  "erro. Então esse arquivo é um <b>robô coletor</b> (um crawler): acessa o site automaticamente "
  "e baixa cada arquivo mensal. Ele é esperto em três sentidos: se a internet falhar, "
  "<b>tenta de novo</b> sozinho; se o arquivo <b>já foi baixado antes</b>, não baixa de novo; e "
  "trata os erros sem quebrar.")
callout("essa automação da coleta costuma valer <b>ponto bônus</b>, porque mostra que os dados "
        "não foram pegos na mão — o sistema se vira sozinho.", cor=VERDE, fundo=colors.HexColor("#EAF6F1"))

H2("Etapa 2 — A faxina e a organização (arquivo prepara_dados.py)")
P("Aqui mora a parte que mais interessa a um professor de Banco de Dados: a etapa clássica de "
  "<b>tratamento de dados</b> (na indústria, chamada de ETL — Extrair, Transformar, Carregar). "
  "Dado da vida real vem sujo, e este arquivo resolve isso, nesta ordem:")
lista([
    "<b>Juntar tudo.</b> Pega os 30+ arquivos mensais separados e os empilha num só — como juntar "
    "páginas avulsas num único caderno.",
    "<b>Ler corretamente.</b> Arquivos do governo costumam vir com acentos quebrados — o nome "
    "'Galeão', por exemplo, chega escrito com símbolos estranhos no lugar dos acentos. O código "
    "detecta o formato certo e conserta automaticamente.",
    "<b>Padronizar os nomes.</b> A ANAC chama uma coluna de 'Sigla ICAO Empresa Aérea'; o código "
    "renomeia tudo para nomes curtos e consistentes (EMPRESA, ORIGEM, DESTINO).",
    "<b>Calcular o que importa.</b> A partir do horário previsto e do real, cria informações que "
    "não existiam: quantos minutos atrasou, se foi atrasado (regra: +15 min), se foi cancelado, "
    "qual a rota, e de qual mês/ano/dia/região o voo é.",
    "<b>Jogar fora o lixo.</b> Remove voos duplicados e dados impossíveis (datas inválidas).",
])
P("No fim, esse arquivo entrega uma planilha limpa e padronizada (dataset_final.csv).")
callout("o código tem até um <b>plano B</b>: se os dados reais não estiverem disponíveis, ele "
        "gera dados simulados realistas para a demonstração continuar funcionando. Isso é "
        "programação defensiva ('e se der errado?').")

H2("Etapa 3 — A despensa inteligente (arquivo lib_dados.py)")
P("Este é o <b>coração técnico</b> do projeto e o ponto mais forte para defender. Ele resolve "
  "dois problemas de uma vez: <b>velocidade</b> e <b>inteligência dos dados</b>.")
P("<b>Velocidade.</b> A planilha limpa tem 3 milhões de linhas e pesa mais de 1 gigabyte. Se "
  "cada painel tivesse que abrir esse arquivo gigante toda vez, demoraria mais de meio minuto e "
  "consumiria muita memória. A solução é a ideia mais elegante do projeto: <b>fazer o trabalho "
  "pesado uma vez só</b>. Este arquivo lê o dado gigante uma única vez, processa tudo e salva uma "
  "versão compacta e otimizada (formato Parquet). Os painéis passam a ler essa versão pronta. "
  "Resultado real:")
lista([
    "abertura caiu de <b>~33 segundos para ~0,3 segundo</b> (mais de 100× mais rápido);",
    "memória usada caiu de <b>~2,6 GB para ~0,7 GB</b>.",
])
P("É como ter uma despensa onde os ingredientes já vêm picados e temperados: na hora de "
  "cozinhar, é instantâneo. E o sistema só refaz esse preparo se o dado original mudar.")
P("<b>Inteligência dos dados.</b> O dado bruto fala em código; este arquivo traduz para humano e "
  "adiciona camadas de conhecimento que o original não tinha:")
lista([
    "traduz o código da companhia (AZU) para o nome (Azul) e agrupa por bloco econômico;",
    "a partir do modelo do avião, descobre o fabricante (Airbus, Boeing, Embraer, ATR);",
    "calcula a <b>distância de cada rota</b> usando as coordenadas geográficas;",
    "calcula se o voo, depois de sair atrasado, <b>recuperou tempo no ar</b>;",
    "resolve um detalhe técnico: os voos usam um tipo de código de aeroporto (ICAO, 'SBGR') e as "
    "tarifas usam outro (IATA, 'GRU') — o arquivo <b>faz a tradução entre os dois</b> para "
    "conseguir cruzar as bases.",
])
P("Ele guarda também o <b>padrão visual</b> (cores, fontes) e a <b>formatação em português</b> "
  "(escrever '1.234.567' e 'R$ 559' no padrão brasileiro). Por que num só lugar? Porque os dois "
  "painéis usam este mesmo arquivo: ficam visualmente idênticos, e mudar uma cor se faz num ponto "
  "só. Esse princípio se chama <b>'não se repita'</b> (DRY).")
callout("'Esse módulo é a fundação compartilhada: transforma dado bruto em dado inteligente e o "
        "serve pronto e rápido para os dois painéis.'", rotulo="Frase de efeito:")

H2("Etapa 4 — Os dois painéis")
P("Com o dado limpo, enriquecido e rápido, faltam as telas. São dois painéis porque atendem a "
  "<b>dois tipos de pergunta diferentes</b>:")
P("<b>Painel 1 — Visão Geral (dashboard_visao_geral.py)</b> é o painel de diretoria: a visão de "
  "cima. Em 5 segundos você entende o setor — total de voos, pontualidade, cancelamentos, quem "
  "domina o mercado, o mapa das rotas pelo Brasil, quais aviões mais voam. Tem um filtro simples "
  "(o ano) e, ao escolher um ano, mostra a <b>variação em relação ao ano anterior</b> "
  "(a seta verde/vermelha), como num relatório financeiro.")
P("<b>Painel 2 — Exploração (dashboard_exploratorio.py)</b> é o painel do analista: para mergulhar "
  "fundo. Tem uma <b>barra lateral de filtros</b> e <b>8 abas temáticas</b>, cada uma respondendo "
  "uma pergunta: Visão (rotas e volume), Pontualidade (quando e por que atrasa), Frota & "
  "Capacidade, Malha & Geografia (o mapa e o fluxo entre regiões), Tarifas (preços), Curiosidades "
  "& Correlações (os fatos surpreendentes), Comparativo (o usuário monta o próprio gráfico) e "
  "Tabela (os dados crus, com botão de <b>baixar em CSV/Excel</b>).")

# ───────────────────────────── 4 ─────────────────────────────
H1("4. A lógica que faz os painéis reagirem")
P("Quando você mexe num filtro — por exemplo, desmarca a companhia 'Gol' — <b>todos os gráficos "
  "se atualizam sozinhos</b> na hora. Como? A lógica se chama <b>programação reativa</b> e "
  "funciona como uma receita de 'quando isso, faça aquilo':")
callout("'Quando o usuário mudar qualquer filtro, pegue só os voos que correspondem a essa "
        "escolha, recalcule os gráficos e redesenhe a tela.'", rotulo="A regra:")
P("No código, isso é uma função chamada <i>callback</i>. Existe uma função central — em ambos os "
  "painéis — chamada <b>filtrar</b>, que é o porteiro: recebe as escolhas do usuário e devolve "
  "<b>apenas o pedaço dos dados</b> que interessa. Os gráficos são sempre desenhados a partir "
  "desse pedaço filtrado. Por isso tudo se mantém coerente: mudou o filtro, muda o pedaço, mudam "
  "os gráficos.")
lista([
    "<b>Eficiência:</b> no painel de exploração, cada aba só calcula seus gráficos quando você "
    "realmente a abre. Se nunca abrir 'Tarifas', o computador nem perde tempo com ela.",
    "<b>Diferencial:</b> os textos de insights e os cartões de curiosidades <b>não são fixos</b> "
    "— são recalculados a partir do que está filtrado. Não é texto decorado; é o sistema lendo os "
    "próprios dados e contando o que encontrou.",
])

# ───────────────────────────── 5 ─────────────────────────────
H1("5. Mapa rápido: se a banca perguntar X, está em Y")
tabela([
    ["Se perguntarem...", "A resposta está em..."],
    ["De onde vêm os dados?", "coleta_dados.py (robô que baixa da ANAC)"],
    ["Como limparam os dados sujos?", "prepara_dados.py (faxina, padronização, duplicados)"],
    ["Como ficou rápido com 3 milhões de linhas?", "lib_dados.py (o cache Parquet)"],
    ["Como cruzaram voos com tarifas?", "lib_dados.py (tradução ICAO e IATA)"],
    ["Onde estão os indicadores e o mapa?", "dashboard_visao_geral.py"],
    ["Onde está a análise detalhada e os filtros?", "dashboard_exploratorio.py"],
    ["Os gráficos atualizam sozinhos?", "Sim — função filtrar + callbacks em cada painel"],
], [8.1 * cm, CW - 8.1 * cm])

# ───────────────────────────── 6 ─────────────────────────────
H1("6. As sacadas do projeto (o que falar para ganhar pontos)")
lista([
    "<b>Pipeline completo e organizado</b> — cobre o ciclo inteiro (coleta, limpeza, "
    "enriquecimento, visualização), com cada etapa isolada em seu arquivo.",
    "<b>Engenharia de dados de verdade</b> — o cache que deixou tudo 100× mais rápido e a "
    "tradução entre os dois padrões de código de aeroporto mostram preocupação real com "
    "performance e integração de bases.",
    "<b>Dados que viram informação</b> — o sistema calcula correlações e curiosidades sozinho "
    "(ex.: voo curto custa cerca de 18× mais por km que voo longo; a partir de 2024 os voos do "
    "Santos Dumont migraram para o Galeão).",
    "<b>Robustez</b> — trata acentos quebrados, dados ausentes, tem plano B com dados simulados "
    "e mostra mensagem amigável quando um filtro não retorna nada.",
])

# ───────────────────────────── 7 ─────────────────────────────
H1("7. Roteiro sugerido de apresentação (8 a 10 minutos)")
lista([
    "<b>Abertura (30s):</b> 'Analisamos 3 milhões de voos do Brasil e transformamos isso em dois "
    "painéis interativos.' Mostre o Painel 1 já aberto.",
    "<b>O caminho do dado (2 min):</b> conte a história do restaurante — coleta, faxina, despensa "
    "rápida, painéis.",
    "<b>A sacada técnica (1,5 min):</b> explique o cache (33s para 0,3s) e a tradução ICAO/IATA. "
    "É aqui que você ganha a banca.",
    "<b>Demonstração ao vivo (3 min):</b> mexa num filtro e mostre tudo reagindo; abra a aba "
    "Curiosidades e leia 2 ou 3 fatos; mostre o mapa.",
    "<b>Fechamento (1 min):</b> 'Não entregamos um gráfico; entregamos um caminho do dado bruto "
    "à decisão.'",
])
SP(6)
story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#DCE6F0")))
SP(4)
story.append(Paragraph("Para rodar: <b>python dashboard_visao_geral.py</b> (porta 8050) e "
                       "<b>python dashboard_exploratorio.py</b> (porta 8051). A primeira execução "
                       "monta o cache (~30s); depois cada painel sobe em ~1s.", S["small"]))


# ───────────────────────────── RODAPÉ ─────────────────────────────
def rodape(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#DCE6F0"))
    canvas.line(MARGEM, 1.3 * cm, A4[0] - MARGEM, 1.3 * cm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(CINZA)
    canvas.drawString(MARGEM, 0.95 * cm, "DashVoosBrasil — Guia de Apresentação")
    canvas.drawRightString(A4[0] - MARGEM, 0.95 * cm, f"Página {doc.page}")
    canvas.restoreState()


doc = SimpleDocTemplate(ARQ, pagesize=A4, topMargin=1.6 * cm, bottomMargin=1.8 * cm,
                        leftMargin=MARGEM, rightMargin=MARGEM,
                        title="DashVoosBrasil — Guia de Apresentação",
                        author="Projeto Final - Banco de Dados Avançado")
doc.build(story, onFirstPage=rodape, onLaterPages=rodape)
print("PDF gerado:", ARQ)
