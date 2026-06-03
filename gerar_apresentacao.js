// Gera a apresentação (PPTX) do projeto DashVoosBrasil.
const pptxgen = require("pptxgenjs");
const p = new pptxgen();
p.layout = "LAYOUT_WIDE";            // 13.333 x 7.5
p.author = "Equipe DashVoosBrasil";
p.title = "DashVoosBrasil — Apresentação";

const W = 13.333, H = 7.5;
// Paleta (identidade do projeto)
const NAVY = "0A2342", NAVY2 = "12305A", AZUL = "1565C0", AZ2 = "2196F3",
      ICE = "CADCFC", CORAL = "E8563A", VERDE = "1FA37C", AMBAR = "F2A900",
      CIANO = "00ACC1", INK = "1A2332", MUT = "5B6B7F", PANEL = "F2F6FB",
      LINE = "DCE6F0", WHITE = "FFFFFF";
const HF = "Trebuchet MS", BF = "Calibri", MF = "Consolas";

const IMG = "assets/";
const DIM = { // dimensões nativas (px) para preservar proporção
  mapa: [1520, 1440], share: [1280, 940], evolucao: [1800, 860], hubs: [1520, 880],
  fabricante: [1480, 860], relacoes: [1760, 860], rkm: [1440, 860], cresc: [1680, 940],
};
const sh = () => ({ type: "outer", color: "0A2342", blur: 9, offset: 3, angle: 135, opacity: 0.16 });

function footer(s, n) {
  s.addText("DashVoosBrasil · Banco de Dados Avançado", {
    x: 0.55, y: 7.08, w: 7, h: 0.3, fontFace: BF, fontSize: 9, color: MUT, align: "left", margin: 0 });
  s.addText(String(n), { x: 12.4, y: 7.08, w: 0.4, h: 0.3, fontFace: BF, fontSize: 9, color: MUT, align: "right", margin: 0 });
}
function kicker(s, txt, color = AZ2) {
  s.addText(txt.toUpperCase(), { x: 0.57, y: 0.42, w: 11, h: 0.3, fontFace: HF, fontSize: 12.5,
    bold: true, color, charSpacing: 2, margin: 0 });
}
function title(s, txt) {
  s.addText(txt, { x: 0.55, y: 0.72, w: 12.2, h: 0.7, fontFace: HF, fontSize: 30, bold: true,
    color: NAVY, margin: 0 });
}
function fitImg(s, key, box) {
  const [nw, nh] = DIM[key], ar = nw / nh;
  let w = box.w, h = w / ar;
  if (h > box.h) { h = box.h; w = h * ar; }
  s.addImage({ path: IMG + key + ".png", x: box.x + (box.w - w) / 2, y: box.y + (box.h - h) / 2, w, h });
}
function statCard(s, x, y, w, h, big, small, accent) {
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: WHITE }, rectRadius: 0.09, line: { color: LINE, width: 1 }, shadow: sh() });
  s.addShape(p.shapes.RECTANGLE, { x: x + 0.001, y, w: 0.09, h, fill: { color: accent } });
  s.addText(big, { x: x + 0.2, y: y + 0.12, w: w - 0.3, h: h * 0.52, fontFace: HF, fontSize: 27, bold: true, color: accent, valign: "middle", margin: 0 });
  s.addText(small, { x: x + 0.2, y: y + h * 0.55, w: w - 0.35, h: h * 0.4, fontFace: BF, fontSize: 11.5, color: MUT, valign: "top", margin: 0 });
}
function panel(s, x, y, w, h, fill = PANEL) {
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill }, rectRadius: 0.08, line: { color: LINE, width: 1 } });
}
function bullets(s, items, x, y, w, h, opts = {}) {
  s.addText(items.map((t, i) => ({ text: t, options: { bullet: { code: "2022", indent: 14 }, breakLine: true, paraSpaceAfter: (opts.gap ?? 7) } })),
    { x, y, w, h, fontFace: BF, fontSize: opts.size ?? 14, color: opts.color ?? INK, valign: "top", margin: 0, lineSpacingMultiple: 1.02 });
}

/* ───────────────── 1. CAPA ───────────────── */
let s = p.addSlide();
s.background = { color: NAVY };
s.addShape(p.shapes.RECTANGLE, { x: 0, y: 0, w: 0.18, h: H, fill: { color: AZ2 } });
s.addText("DASHVOOSBRASIL", { x: 0.7, y: 1.85, w: 8.2, h: 1.0, fontFace: HF, fontSize: 50, bold: true, color: WHITE, charSpacing: 1, margin: 0 });
s.addText("Da coleta bruta à decisão: 3 milhões de voos da aviação brasileira em dois painéis interativos.",
  { x: 0.72, y: 2.95, w: 7.7, h: 0.9, fontFace: BF, fontSize: 17, color: ICE, margin: 0, lineSpacingMultiple: 1.1 });
s.addText("Projeto Final · Banco de Dados Avançado", { x: 0.72, y: 4.0, w: 7.5, h: 0.4, fontFace: HF, fontSize: 14, bold: true, color: AMBAR, margin: 0 });
s.addText([
  { text: "Caio Adamo Scomparin   ·   Rafael Tamura", options: { breakLine: true } },
  { text: "Fábio Su Li   ·   Henrique Zaccarias Martelini" },
], { x: 0.72, y: 5.7, w: 7.6, h: 0.9, fontFace: BF, fontSize: 13, color: "9FC0E6", margin: 0, lineSpacingMultiple: 1.25 });
// mapa em cartão branco à direita
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 8.85, y: 1.25, w: 4.0, h: 5.0, fill: { color: WHITE }, rectRadius: 0.12, shadow: sh() });
fitImg(s, "mapa", { x: 9.0, y: 1.5, w: 3.7, h: 4.2 });
s.addText("A malha aérea nacional", { x: 8.95, y: 5.78, w: 3.8, h: 0.35, fontFace: BF, fontSize: 11, italic: true, color: MUT, align: "center", margin: 0 });

/* ───────────────── 2. O DESAFIO ───────────────── */
s = p.addSlide(); s.background = { color: WHITE };
kicker(s, "Contexto", CORAL); title(s, "O desafio");
s.addText([
  { text: "A ANAC publica, mês a mês, o registro de ", options: {} },
  { text: "todos os voos comerciais do Brasil", options: { bold: true } },
  { text: ". É um tesouro de informação — mas chega ", options: {} },
  { text: "bruto, gigante e desorganizado", options: { bold: true } },
  { text: ": acentos quebrados, códigos em vez de nomes, dados faltando.", options: {} },
], { x: 0.57, y: 1.7, w: 7.0, h: 1.6, fontFace: BF, fontSize: 16, color: INK, valign: "top", margin: 0, lineSpacingMultiple: 1.18 });
s.addText("Nosso objetivo: transformar esse dado bruto em informação que qualquer pessoa consiga explorar e entender.",
  { x: 0.57, y: 3.5, w: 7.0, h: 1.0, fontFace: BF, fontSize: 16, italic: true, color: AZUL, valign: "top", margin: 0, lineSpacingMultiple: 1.18 });
statCard(s, 8.0, 1.7, 2.3, 1.45, "3,07 mi", "voos analisados", AZ2);
statCard(s, 10.5, 1.7, 2.3, 1.45, "490", "aeroportos", VERDE);
statCard(s, 8.0, 3.35, 2.3, 1.45, "150", "companhias", CORAL);
statCard(s, 10.5, 3.35, 2.3, 1.45, "2022–25", "período coberto", AMBAR);
panel(s, 0.57, 5.0, 12.2, 1.55);
s.addText("Por que isso é um projeto de Banco de Dados?", { x: 0.8, y: 5.18, w: 11.7, h: 0.4, fontFace: HF, fontSize: 14, bold: true, color: NAVY, margin: 0 });
s.addText("Porque o coração do trabalho é o ciclo do dado — coletar, limpar, integrar, transformar e disponibilizar de forma rápida e confiável. O painel é só a ponta visível de todo esse processo.",
  { x: 0.8, y: 5.58, w: 11.7, h: 0.9, fontFace: BF, fontSize: 13.5, color: INK, margin: 0, lineSpacingMultiple: 1.12 });
footer(s, 2);

/* ───────────────── 3. A SOLUÇÃO ───────────────── */
s = p.addSlide(); s.background = { color: WHITE };
kicker(s, "Visão geral"); title(s, "A solução: dois painéis sobre um mesmo pipeline");
// dois cartões
function dashCard(x, tit, sub, items, accent) {
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y: 1.65, w: 3.55, h: 4.55, fill: { color: WHITE }, rectRadius: 0.1, line: { color: LINE, width: 1 }, shadow: sh() });
  s.addShape(p.shapes.RECTANGLE, { x: x + 0.001, y: 1.65, w: 3.55, h: 0.12, fill: { color: accent } });
  s.addText(tit, { x: x + 0.25, y: 1.9, w: 3.1, h: 0.45, fontFace: HF, fontSize: 17, bold: true, color: NAVY, margin: 0 });
  s.addText(sub, { x: x + 0.25, y: 2.35, w: 3.1, h: 0.4, fontFace: BF, fontSize: 12, italic: true, color: accent, margin: 0 });
  bullets(s, items, x + 0.25, 2.85, 3.15, 3.2, { size: 12.5, gap: 7 });
}
dashCard(0.57, "Painel Executivo", "a visão de diretoria", [
  "8 indicadores com variação ano a ano", "Mapa da malha aérea do país",
  "Concentração de mercado e frota", "Leitura em 5 segundos"], AZ2);
dashCard(4.32, "Painel de Exploração", "o painel do analista", [
  "8 abas temáticas e filtros encadeados", "Pontualidade, frota, tarifas, geografia",
  "Aba de curiosidades e correlações", "Tabela com download em CSV"], CORAL);
// imagem evolução à direita
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 8.25, y: 1.65, w: 4.55, h: 4.55, fill: { color: PANEL }, rectRadius: 0.1, line: { color: LINE, width: 1 } });
s.addText("Mesmo dado, perguntas diferentes", { x: 8.45, y: 1.82, w: 4.2, h: 0.4, fontFace: HF, fontSize: 13.5, bold: true, color: NAVY, margin: 0 });
fitImg(s, "evolucao", { x: 8.4, y: 2.45, w: 4.25, h: 3.4 });
footer(s, 3);

/* ───────────────── 4. ARQUITETURA (restaurante) ───────────────── */
s = p.addSlide(); s.background = { color: WHITE };
kicker(s, "Arquitetura"); title(s, "Pense em um restaurante: cada arquivo, uma estação");
const etapas = [
  ["1", "O entregador", "coleta_dados.py", "Robô que baixa os dados da ANAC automaticamente (com nova tentativa e cache).", AZ2],
  ["2", "A faxina e o preparo", "prepara_dados.py", "Limpa, padroniza, junta os arquivos e calcula atraso, rota, região...", VERDE],
  ["3", "A despensa inteligente", "lib_dados.py", "Enriquece os dados e os guarda prontos para uso instantâneo (cache).", CORAL],
  ["4", "O prato executivo", "dashboard_visao_geral.py", "Painel resumido — a visão estratégica do setor.", AMBAR],
  ["5", "O prato de degustação", "dashboard_exploratorio.py", "Painel detalhado — 8 abas para explorar a fundo.", CIANO],
];
let yy = 1.7;
etapas.forEach(([num, role, file, desc, c]) => {
  s.addShape(p.shapes.OVAL, { x: 0.6, y: yy + 0.05, w: 0.62, h: 0.62, fill: { color: c } });
  s.addText(num, { x: 0.6, y: yy + 0.05, w: 0.62, h: 0.62, fontFace: HF, fontSize: 20, bold: true, color: WHITE, align: "center", valign: "middle", margin: 0 });
  s.addText(role, { x: 1.45, y: yy, w: 3.4, h: 0.38, fontFace: HF, fontSize: 15, bold: true, color: NAVY, margin: 0 });
  s.addText(file, { x: 1.45, y: yy + 0.38, w: 3.4, h: 0.32, fontFace: MF, fontSize: 11.5, color: c, margin: 0 });
  s.addText(desc, { x: 5.1, y: yy + 0.02, w: 7.6, h: 0.72, fontFace: BF, fontSize: 13, color: INK, valign: "middle", margin: 0, lineSpacingMultiple: 1.05 });
  yy += 0.95;
});
s.addText("Princípio: separação de responsabilidades — cada arquivo faz uma coisa só, e bem feita.",
  { x: 0.6, y: 6.55, w: 12, h: 0.4, fontFace: BF, fontSize: 13, italic: true, color: AZUL, margin: 0 });
footer(s, 4);

/* ───────────────── 5. ENGENHARIA (cache) ───────────────── */
s = p.addSlide(); s.background = { color: WHITE };
kicker(s, "Engenharia de dados", CORAL); title(s, "A sacada: fazer o trabalho pesado uma vez só");
statCard(s, 0.57, 1.75, 3.85, 1.6, "33 s → 0,3 s", "tempo para abrir cada painel", AZ2);
statCard(s, 4.62, 1.75, 3.85, 1.6, "2,6 GB → 0,7 GB", "memória usada (−72%)", VERDE);
statCard(s, 8.67, 1.75, 4.1, 1.6, "+100×", "mais rápido que ler o arquivo original", CORAL);
panel(s, 0.57, 3.65, 6.0, 2.9);
s.addText("Como?", { x: 0.8, y: 3.82, w: 5.5, h: 0.4, fontFace: HF, fontSize: 15, bold: true, color: NAVY, margin: 0 });
s.addText([
  { text: "O arquivo original tem 3 milhões de linhas e pesa mais de 1 GB. Em vez de relê-lo a cada vez, processamos ", options: {} },
  { text: "uma única vez", options: { bold: true } },
  { text: " e salvamos uma versão compacta e otimizada (formato ", options: {} },
  { text: "Parquet", options: { bold: true } },
  { text: "). Os painéis passam a abrir essa versão pronta — como uma despensa com tudo já picado e temperado.", options: {} },
], { x: 0.8, y: 4.25, w: 5.55, h: 2.2, fontFace: BF, fontSize: 13.5, color: INK, valign: "top", margin: 0, lineSpacingMultiple: 1.18 });
panel(s, 6.77, 3.65, 6.0, 2.9, "EAF2FB");
s.addText("E um detalhe que integra duas bases", { x: 7.0, y: 3.82, w: 5.5, h: 0.4, fontFace: HF, fontSize: 15, bold: true, color: NAVY, margin: 0 });
s.addText([
  { text: "Os voos identificam aeroportos por um código (ICAO: ", options: {} },
  { text: "SBGR", options: { bold: true, fontFace: MF } },
  { text: ") e as tarifas por outro (IATA: ", options: {} },
  { text: "GRU", options: { bold: true, fontFace: MF } },
  { text: "). Sem tradução, as bases não conversam. Criamos a ", options: {} },
  { text: "ponte ICAO ↔ IATA", options: { bold: true } },
  { text: " que permite cruzar voos e preços por rota.", options: {} },
], { x: 7.0, y: 4.25, w: 5.55, h: 2.2, fontFace: BF, fontSize: 13.5, color: INK, valign: "top", margin: 0, lineSpacingMultiple: 1.18 });
footer(s, 5);

/* ───────────────── 6. PAINEL EXECUTIVO ───────────────── */
s = p.addSlide(); s.background = { color: WHITE };
kicker(s, "Dashboard 1"); title(s, "Painel Executivo — a leitura de 5 segundos");
bullets(s, [
  "8 indicadores-chave com a variação em relação ao ano anterior (a seta verde/vermelha).",
  "Mapa da malha aérea: aeroportos como bolhas, rotas como linhas.",
  "Concentração de mercado por grupo, com o índice HHI.",
  "Ranking de hubs, mix de frota e pontualidade por companhia.",
  "Tudo recalcula ao trocar o ano ou o segmento.",
], 0.57, 1.75, 6.0, 4.4, { size: 15, gap: 12 });
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 6.95, y: 1.7, w: 5.85, h: 4.7, fill: { color: WHITE }, rectRadius: 0.1, line: { color: LINE, width: 1 }, shadow: sh() });
s.addText("Concentração de mercado (Azul + LATAM + Gol = 86%)", { x: 7.15, y: 1.85, w: 5.5, h: 0.4, fontFace: BF, fontSize: 12, italic: true, color: MUT, align: "center", margin: 0 });
fitImg(s, "share", { x: 7.15, y: 2.3, w: 5.45, h: 3.95 });
footer(s, 6);

/* ───────────────── 7. PAINEL EXPLORAÇÃO ───────────────── */
s = p.addSlide(); s.background = { color: WHITE };
kicker(s, "Dashboard 2"); title(s, "Painel de Exploração — 8 abas para investigar");
const abas = [["Visão", "rotas e volume"], ["Pontualidade", "quando e por que atrasa"],
  ["Frota & Capacidade", "aviões e assentos"], ["Malha & Geografia", "mapa e fluxos"],
  ["Tarifas", "preços por rota"], ["Curiosidades", "correlações e fatos"],
  ["Comparativo", "monte seu gráfico"], ["Tabela", "dados crus + download"]];
let ax = 0.57, ay = 1.75;
abas.forEach((a, i) => {
  const col = i % 2, row = Math.floor(i / 2);
  const x = 0.57 + col * 3.05, y = 1.75 + row * 1.07;
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y, w: 2.9, h: 0.92, fill: { color: PANEL }, rectRadius: 0.07, line: { color: LINE, width: 1 } });
  s.addText(a[0], { x: x + 0.18, y: y + 0.12, w: 2.6, h: 0.34, fontFace: HF, fontSize: 13.5, bold: true, color: NAVY, margin: 0 });
  s.addText(a[1], { x: x + 0.18, y: y + 0.47, w: 2.6, h: 0.3, fontFace: BF, fontSize: 11, color: MUT, margin: 0 });
});
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 6.95, y: 1.7, w: 5.85, h: 4.7, fill: { color: WHITE }, rectRadius: 0.1, line: { color: LINE, width: 1 }, shadow: sh() });
s.addText("Exemplo: os aeroportos mais movimentados", { x: 7.15, y: 1.85, w: 5.5, h: 0.4, fontFace: BF, fontSize: 12, italic: true, color: MUT, align: "center", margin: 0 });
fitImg(s, "hubs", { x: 7.15, y: 2.35, w: 5.45, h: 3.85 });
footer(s, 7);

/* ───────────────── 8. INSIGHTS DE NEGÓCIO ───────────────── */
s = p.addSlide(); s.background = { color: WHITE };
kicker(s, "Resultados", CORAL); title(s, "Insights que saltam dos dados");
statCard(s, 0.57, 1.7, 2.95, 1.4, "2,5×", "voos da noite atrasam mais que os da manhã", CORAL);
statCard(s, 3.67, 1.7, 2.95, 1.4, "18×", "o km de um voo curto custa mais que o de um longo", AMBAR);
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 0.57, y: 3.3, w: 6.05, h: 3.05, fill: { color: WHITE }, rectRadius: 0.1, line: { color: LINE, width: 1 }, shadow: sh() });
s.addText("Preço por km despenca com a distância", { x: 0.75, y: 3.42, w: 5.7, h: 0.35, fontFace: BF, fontSize: 12, italic: true, color: MUT, margin: 0 });
fitImg(s, "rkm", { x: 0.7, y: 3.85, w: 5.8, h: 2.4 });
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 6.85, y: 1.7, w: 5.95, h: 4.65, fill: { color: WHITE }, rectRadius: 0.1, line: { color: LINE, width: 1 }, shadow: sh() });
s.addText("Êxodo Santos Dumont → Galeão (2024)", { x: 7.05, y: 1.85, w: 5.6, h: 0.35, fontFace: BF, fontSize: 12, italic: true, color: MUT, margin: 0 });
fitImg(s, "cresc", { x: 7.0, y: 2.3, w: 5.7, h: 3.95 });
footer(s, 8);

/* ───────────────── 9. CORRELAÇÕES ───────────────── */
s = p.addSlide(); s.background = { color: WHITE };
kicker(s, "Resultados", CORAL); title(s, "Correlações: o que tem a ver com o quê?");
s.addShape(p.shapes.ROUNDED_RECTANGLE, { x: 0.57, y: 1.7, w: 8.3, h: 4.75, fill: { color: WHITE }, rectRadius: 0.1, line: { color: LINE, width: 1 }, shadow: sh() });
fitImg(s, "relacoes", { x: 0.75, y: 1.95, w: 7.95, h: 4.25 });
panel(s, 9.05, 1.7, 3.75, 4.75, "EAF2FB");
s.addText("A leitura", { x: 9.25, y: 1.9, w: 3.4, h: 0.4, fontFace: HF, fontSize: 15, bold: true, color: NAVY, margin: 0 });
bullets(s, [
  "Traduzimos números abstratos em palavras: 'forte', 'fraca', 'quase nenhuma'.",
  "Só sair e chegar atrasado têm relação quase perfeita.",
  "A grande descoberta: a distância do voo quase não influencia o atraso.",
], 9.25, 2.45, 3.45, 3.7, { size: 13, gap: 12 });
footer(s, 9);

/* ───────────────── 10. COMO FUNCIONA (reativo) ───────────────── */
s = p.addSlide(); s.background = { color: WHITE };
kicker(s, "Por dentro"); title(s, "Como tudo se atualiza sozinho");
const passos = [["Você mexe num filtro", "ex.: desmarca a Gol", AZ2],
  ["A função filtrar recorta", "separa só os voos pedidos", VERDE],
  ["Os callbacks recalculam", "refazem os gráficos", AMBAR],
  ["A tela se redesenha", "gráficos e textos novos", CORAL]];
passos.forEach((pp, i) => {
  const x = 0.57 + i * 3.18;
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y: 2.2, w: 2.8, h: 1.8, fill: { color: WHITE }, rectRadius: 0.1, line: { color: pp[2], width: 1.5 }, shadow: sh() });
  s.addText(String(i + 1), { x: x + 0.15, y: 2.32, w: 0.7, h: 0.6, fontFace: HF, fontSize: 26, bold: true, color: pp[2], margin: 0 });
  s.addText(pp[0], { x: x + 0.2, y: 2.95, w: 2.45, h: 0.55, fontFace: HF, fontSize: 13.5, bold: true, color: NAVY, valign: "top", margin: 0, lineSpacingMultiple: 1.0 });
  s.addText(pp[1], { x: x + 0.2, y: 3.5, w: 2.45, h: 0.4, fontFace: BF, fontSize: 11.5, color: MUT, margin: 0 });
  if (i < 3) s.addText("→", { x: x + 2.78, y: 2.5, w: 0.45, h: 1.2, fontFace: HF, fontSize: 26, bold: true, color: MUT, align: "center", valign: "middle", margin: 0 });
});
panel(s, 0.57, 4.65, 12.2, 1.7, "EAF2FB");
s.addText("O diferencial", { x: 0.8, y: 4.82, w: 11.6, h: 0.4, fontFace: HF, fontSize: 14, bold: true, color: NAVY, margin: 0 });
s.addText("Os textos de insight e os cartões de curiosidades não são fixos: o sistema lê os próprios dados filtrados e escreve as conclusões na hora. Não é texto decorado — é o dado falando.",
  { x: 0.8, y: 5.22, w: 11.7, h: 1.0, fontFace: BF, fontSize: 13.5, color: INK, margin: 0, lineSpacingMultiple: 1.15 });
footer(s, 10);

/* ───────────────── 11. TECNOLOGIAS ───────────────── */
s = p.addSlide(); s.background = { color: WHITE };
kicker(s, "Ferramentas"); title(s, "Tecnologias utilizadas");
const techs = [["Python", "linguagem base de todo o projeto", AZ2],
  ["pandas + NumPy", "limpeza, integração e cálculos", VERDE],
  ["Plotly", "todos os gráficos interativos", CORAL],
  ["Dash", "framework dos dois painéis web", AMBAR],
  ["PyArrow / Parquet", "o cache que deixa tudo rápido", CIANO],
  ["requests", "o robô coletor de dados", AZUL]];
techs.forEach((t, i) => {
  const col = i % 3, row = Math.floor(i / 3);
  const x = 0.57 + col * 4.12, y = 2.0 + row * 2.05;
  s.addShape(p.shapes.ROUNDED_RECTANGLE, { x, y, w: 3.9, h: 1.75, fill: { color: WHITE }, rectRadius: 0.1, line: { color: LINE, width: 1 }, shadow: sh() });
  s.addShape(p.shapes.RECTANGLE, { x: x + 0.001, y, w: 0.1, h: 1.75, fill: { color: t[2] } });
  s.addText(t[0], { x: x + 0.3, y: y + 0.3, w: 3.4, h: 0.55, fontFace: HF, fontSize: 19, bold: true, color: NAVY, margin: 0 });
  s.addText(t[1], { x: x + 0.3, y: y + 0.95, w: 3.45, h: 0.65, fontFace: BF, fontSize: 13, color: MUT, margin: 0, lineSpacingMultiple: 1.05 });
});
footer(s, 11);

/* ───────────────── 12. CONCLUSÃO ───────────────── */
s = p.addSlide(); s.background = { color: NAVY };
s.addShape(p.shapes.RECTANGLE, { x: 0, y: 0, w: 0.18, h: H, fill: { color: CORAL } });
s.addText("CONCLUSÃO", { x: 0.8, y: 1.5, w: 8, h: 0.4, fontFace: HF, fontSize: 14, bold: true, color: AMBAR, charSpacing: 2, margin: 0 });
s.addText("Não entregamos um gráfico.\nEntregamos um caminho do dado bruto à decisão.",
  { x: 0.8, y: 2.1, w: 11.6, h: 2.0, fontFace: HF, fontSize: 33, bold: true, color: WHITE, margin: 0, lineSpacingMultiple: 1.12 });
bullets(s, [
  "Pipeline completo: coleta, limpeza, enriquecimento e visualização.",
  "Engenharia real: cache 100× mais rápido e integração de duas bases.",
  "Dados que viram informação — correlações e curiosidades calculadas sozinhas.",
], 0.85, 4.35, 11.0, 1.9, { size: 15, gap: 11, color: ICE });
s.addText("Obrigado!  ·  python dashboard_visao_geral.py (8050)  ·  python dashboard_exploratorio.py (8051)",
  { x: 0.8, y: 6.7, w: 11.8, h: 0.4, fontFace: BF, fontSize: 12, color: "9FC0E6", margin: 0 });

p.writeFile({ fileName: "DashVoosBrasil_Apresentacao.pptx" }).then(f => console.log("Gerado:", f));
