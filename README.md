# ✈ Dashboard Interativo de Voos no Brasil
### Projeto Final - Banco de Dados Avançado

---

## 📋 Visão Geral

Este projeto analisa dados públicos de aviação civil brasileira disponibilizados pela **ANAC (Agência Nacional de Aviação Civil)**, construindo dois dashboards interativos com Dash/Plotly que permitem explorar padrões, tendências e insights sobre os voos no Brasil entre 2022 e 2024.

### Fontes de Dados
| Arquivo | Fonte | Descrição |
|---------|-------|-----------|
| VRA - Voo Regular Ativo | ANAC (gov.br) | Histórico mensal de todos os voos comerciais (origem, destino, companhia, horários, situação) |
| Tarifas Aéreas Domésticas | ANAC (gov.br) | Tarifas médias praticadas por trecho, companhia e período |

---

## 🗂 Estrutura do Projeto

```
voos_brasil/
│
├── coleta_dados.py          ← CRAWLER: baixa dados da ANAC automaticamente (+1 ponto bônus)
├── prepara_dados.py         ← Limpeza, integração e transformação (CSV → dataset_final)
├── lib_dados.py             ← CAMADA ANALÍTICA: cache Parquet, enriquecimento, tema visual
├── dashboard_visao_geral.py ← Dashboard 1: Painel Executivo (porta 8050)
├── dashboard_exploratorio.py← Dashboard 2: Exploração Interativa, 8 abas (porta 8051)
├── requirements.txt
├── README.md
│
├── dados_brutos/
│   ├── vra/                   ← CSVs mensais do VRA
│   ├── tarifas/               ← CSVs trimestrais de tarifas
│   └── vra_consolidado.csv
│
└── dados_processados/
    ├── voos_limpo.csv
    ├── tarifas_limpo.csv
    ├── dataset_final.csv         ← Saída da preparação (VRA limpo)
    └── dataset_analitico.parquet ← Cache enriquecido (gerado por lib_dados, ~50 MB)
```

---

## 🚀 Como Executar

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Coletar os dados (BÔNUS - crawler automático)
```bash
python coleta_dados.py
```
> Baixa automaticamente os arquivos mensais do VRA e trimestrais de tarifas da ANAC.
> Se os arquivos já existirem em cache, são reutilizados.

### 3. Preparar os dados
```bash
python prepara_dados.py
```
> Realiza limpeza, integração (merge) e transformação dos dados.
> **Se os dados brutos não existirem**, gera dados sintéticos realistas para desenvolvimento.

### 4. (Opcional) Construir o cache analítico
```bash
python lib_dados.py
```
> Gera `dataset_analitico.parquet` (enriquecimento + downcast). Se você pular este passo,
> o cache é construído **automaticamente** na primeira execução de um dashboard.

### 5. Executar os Dashboards

Em dois terminais separados:
```bash
# Terminal 1 - Dashboard Executivo
python dashboard_visao_geral.py
# Acesse: http://localhost:8050

# Terminal 2 - Dashboard Exploratório
python dashboard_exploratorio.py
# Acesse: http://localhost:8051
```
> Na **primeira** execução o cache é montado (~30 s lendo o CSV). Depois, cada dashboard
> sobe em **~1 s**.

---

## 📊 Pipeline de Ciência de Dados

### Etapa 1 - Aquisição (coleta_dados.py)
- Crawler automático com `requests`
- Download de arquivos ZIP/CSV mensais do VRA (2022–2024)
- Download de tarifas trimestrais
- Retry automático, cache local, tratamento de erros HTTP

### Etapa 2 - Integração e Limpeza (prepara_dados.py)
- `pd.concat()` para unir arquivos mensais/trimestrais
- `pd.merge()` para cruzar VRA com Tarifas por empresa/rota/mês
- Tratamento de valores ausentes (dropna seletivo, coerção de tipos)
- Padronização de colunas (renomeação, strip, upper)
- Remoção de duplicatas por chave composta
- Remoção de inconsistências (tarifas fora de faixa, datas inválidas)

### Etapa 3 - Transformação (prepara_dados.py)
- Novas variáveis: `ATRASO_MIN`, `ATRASADO`, `CANCELADO`, `ROTA`
- Extração de `ANO`, `MES`, `TRIMESTRE`, `DIA_SEM` da data de partida
- Mapeamento `ORIG_REGIAO` / `DEST_REGIAO` (Norte, Nordeste, etc.)
- Coordenadas geográficas dos aeroportos (lat/lon para mapa)
- Suporte a códigos IATA e ICAO nos aeroportos

### Etapa 4 - Camada Analítica (lib_dados.py)
Módulo compartilhado pelos dois dashboards, onde mora a engenharia de dados pesada:
- **Cache Parquet (zstd)**: o CSV de ~1 GB é lido uma única vez e materializado em
  `dataset_analitico.parquet` (~50 MB). A carga cai de **~33 s → ~0,3 s** e a memória
  de **~2,6 GB → ~0,7 GB** (downcast de tipos + categorias). Invalidação automática por
  versão de schema e data de modificação.
- **Enriquecimento** (novas variáveis derivadas):
  - `EMPRESA_NOME` / `GRUPO` (Azul, LATAM, Gol, Regionais, Internacionais, Cargueiras)
  - `FABRICANTE` / `FAMILIA_AERONAVE` a partir do modelo ICAO da aeronave
  - `DIST_KM` (haversine entre coordenadas) e `ASK` (assentos-km ofertados)
  - `ATRASO_CHEGADA_MIN` e `RECUPERACAO_MIN` (atraso recuperado em voo)
  - `HORA_PARTIDA`, `FAIXA_HORARIA`, `DIA_SEM_PT`, `PERIODO`, `SEGMENTO`, `FLUXO_REGIAO`
  - `ORIGEM_IATA`/`DESTINO_IATA` (conversão ICAO→IATA para rótulos legíveis)
- **Integração das tarifas**: resolve o descasamento ICAO×IATA entre VRA e tarifas e
  calcula `DIST_KM` e `TARIFA_POR_KM` por rota.
- **Tema visual** e formatação pt-BR (`1.234.567`, `R$`, `1,2 mi`) reutilizados pelos dois apps.

### Etapa 5 - Análise Exploratória (dashboards)
- Estatísticas descritivas por companhia, grupo, rota, região e período
- Identificação de sazonalidade, picos e tendências (com comparação ano a ano)
- Análise de pontualidade (partida × chegada), cancelamentos e frota
- Comparação de tarifas entre companhias, rotas e distância
- **Insights calculados dinamicamente** a partir do recorte filtrado

---

## 💡 Principais Insights

| # | Insight | Relevância |
|---|---------|-----------|
| 1 | **São Paulo como super-hub**: GRU lidera com folga em movimentos; somado a CGH e VCP, concentra a maior fatia da malha | Infraestrutura e concentração geográfica |
| 2 | **Ponte aérea Rio–SP**: CGH↔SDU é de longe a rota mais movimentada (~59 mil voos/sentido) | Corredor crítico de alta frequência |
| 3 | **Oligopólio (~86%)**: Azul + LATAM + Gol dominam o mercado, com HHI > 2.600 (concentração alta) | Competição e impacto sobre tarifas |
| 4 | **Frota majoritariamente Airbus**: ~42% Airbus, ~32% Boeing, seguidos de Embraer e ATR (regional) | Estratégia de frota e capacidade |
| 5 | **Recuperação em voo**: voos que partem atrasados chegam ~5 min menos atrasados — recuperam tempo no ar | Eficiência operacional e malha de horários |
| 6 | **Internacionais atrasam mais**: Copa (~42%) e TAP (~38%) têm taxa de atraso muito acima das nacionais (~13–16%) | Padrão operacional por tipo de operação |
| 7 | **Sazonalidade e dias críticos**: picos em jan/jul/dez; quinta e sexta são os dias com mais atrasos | Planejamento de demanda e escala |
| 8 | **Eixo Sudeste**: o maior bloco de voos domésticos é Sudeste↔Sudeste, reforçando a centralidade da região | Distribuição regional da demanda |

---

## 🎨 Design dos Dashboards

### Dashboard 1 - Painel Executivo (porta 8050)
- **8 KPIs com variação ano a ano** (voos, voos/dia, companhias, aeroportos, pontualidade,
  cancelamentos, assentos ofertados, atraso médio) — deltas em verde/vermelho e p.p.
- **Mapa da malha aérea**: aeroportos como bolhas (movimento) e principais ligações como linhas
- **Concentração de mercado**: donut por grupo econômico com Top-3 e índice HHI
- **Evolução mensal** sobreposta por ano (2025 sinalizado como parcial)
- **Sazonalidade** com destaque dos meses de pico
- **Ranking de hubs**, **mix de frota** (família × fabricante)
- **Pontualidade por companhia** e **matriz de fluxo entre regiões**
- **Insights dinâmicos** recalculados conforme os filtros (ano + segmento)

### Dashboard 2 - Exploração Interativa (porta 8051)
**8 abas temáticas:**
- **🗺 Visão**: volume no tempo por grupo, participação, top rotas, heatmap mês×dia
- **⏱ Pontualidade**: distribuição de atrasos, **partida × chegada por hora** (recuperação),
  atraso por dia da semana, cancelamento por mês
- **🛩 Frota & Capacidade**: fabricante, famílias, porte médio por grupo, ASK no tempo
- **🌐 Malha & Geografia**: mapa nacional, fluxo regional, distância × recuperação
- **💲 Tarifas**: tarifa por companhia, evolução, tarifa × distância, rotas + caras/baratas
- **🔭 Curiosidades & Correlações**: cartões "você sabia?" dinâmicos, painel "o que tem a ver
  com o quê?" (relações em linguagem clara), pontualidade por fabricante, R$/km × distância
  e crescimento de rotas
- **📊 Comparativo**: dimensão, métrica e cor configuráveis (6 métricas, 10 dimensões)
- **📋 Tabela**: filtros nativos, colunas selecionáveis e **download CSV** do recorte

#### 🔭 Exemplos de correlações/curiosidades (calculadas, não fixas)
| Curiosidade | Dado |
|---|---|
| **Efeito cascata**: voos da noite atrasam mais que os da manhã | 06h ≈ 9% → 18h ≈ 21% (~2,5×) |
| **Preço por km despenca com a distância** (tarifa quase não muda) | R$ 3,45/km (<500 km) → R$ 0,19/km (2500+ km) |
| **Êxodo Santos Dumont → Galeão (2024)** | GIG↔SSA **+419%**; rotas SDU **−100%** |
| **Aeroportos pequenos atrasam mais que os grandes hubs** | ~18,5% vs ~15,3% |
| **Boeing atrasa mais que Embraer**; widebodies são os menos pontuais | 19% vs 13%; A330neo/787 ~35% |
| **Recuperação em voo** cresce com o atraso | atrasos de 2h+ recuperam ~8 min; 22% "salvam" o atraso |
| **Internacionais**: quando atrasam, atrasam muito; e cancelam mais | ~108 min médios; ~16% de cancelamento |

**Filtros interativos (sidebar):** período (anos), grupo econômico, região de origem,
segmento (doméstico/internacional) e pontualidade — com contador do recorte em tempo real.

---

## 🛠 Tecnologias Utilizadas

| Biblioteca | Uso |
|-----------|-----|
| `pandas` | Manipulação e análise de dados |
| `numpy` | Cálculos numéricos (haversine, agregações) |
| `pyarrow` | Cache colunar Parquet (carga rápida) |
| `requests` | Crawler HTTP |
| `dash` | Framework dos dashboards |
| `dash-bootstrap-components` | Layout e componentes visuais |
| `plotly` | Gráficos interativos (mapas, heatmaps, etc.) |

---

## 👥 Equipe
Projeto Final - Banco de Dados Avançado
- Caio Adamo Scomparin - 23028248
- Rafael Tamura - 23024380
- Fabio Su Li - 23027760
- Henrique Zaccarias Martelini - 23024214
