# ✈ Dashboard Interativo de Voos no Brasil
### Projeto Final — Banco de Dados Avançado

---

## 📋 Visão Geral

Este projeto analisa dados públicos de aviação civil brasileira disponibilizados pela **ANAC (Agência Nacional de Aviação Civil)**, construindo dois dashboards interativos com Dash/Plotly que permitem explorar padrões, tendências e insights sobre os voos no Brasil entre 2022 e 2024.

### Fontes de Dados
| Arquivo | Fonte | Descrição |
|---------|-------|-----------|
| VRA — Voo Regular Ativo | ANAC (gov.br) | Histórico mensal de todos os voos comerciais (origem, destino, companhia, horários, situação) |
| Tarifas Aéreas Domésticas | ANAC (gov.br) | Tarifas médias praticadas por trecho, companhia e período |

---

## 🗂 Estrutura do Projeto

```
voos_brasil/
│
├── coleta_dados.py        ← CRAWLER: baixa dados da ANAC automaticamente (+1 ponto bônus)
├── prepara_dados.py       ← Limpeza, integração e transformação
├── dashboard_visao_geral.py← Dashboard 1: Painel Executivo (porta 8050)
├── dashboard_exploratorio.py← Dashboard 2: Exploração Interativa (porta 8051)
├── requirements.txt
├── README.md
│
├── dados_brutos/              
│   ├── vra/                   ← CSVs mensais do VRA
│   ├── tarifas/               ← CSVs trimestrais de tarifas
│   ├── vra_consolidado.csv
│   └── tarifas_consolidado.csv
│
└── dados_processados/         
    ├── voos_limpo.csv
    ├── tarifas_limpo.csv
    └── dataset_final.csv      ← Usado pelos dashboards
```

---

## 🚀 Como Executar

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Coletar os dados (BÔNUS — crawler automático)
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

### 4. Executar os Dashboards

Em dois terminais separados:
```bash
# Terminal 1 — Dashboard Executivo
python dashboard_visao_geral.py
# Acesse: http://localhost:8050

# Terminal 2 — Dashboard Exploratório
python dashboard_exploratorio.py
# Acesse: http://localhost:8051
```

---

## 📊 Pipeline de Ciência de Dados

### Etapa 1 — Aquisição (01_coletar_dados.py)
- Crawler automático com `requests`
- Download de arquivos ZIP/CSV mensais do VRA (2022–2024)
- Download de tarifas trimestrais
- Retry automático, cache local, tratamento de erros HTTP

### Etapa 2 — Integração e Limpeza (02_preparar_dados.py)
- `pd.concat()` para unir arquivos mensais/trimestrais
- `pd.merge()` para cruzar VRA com Tarifas por empresa/rota/mês
- Tratamento de valores ausentes (dropna seletivo, coerção de tipos)
- Padronização de colunas (renomeação, strip, upper)
- Remoção de duplicatas por chave composta
- Remoção de inconsistências (tarifas fora de faixa, datas inválidas)

### Etapa 3 — Transformação (02_preparar_dados.py)
- Novas variáveis: `ATRASO_MIN`, `ATRASADO`, `CANCELADO`, `ROTA`
- Extração de `ANO`, `MES`, `TRIMESTRE`, `DIA_SEM` da data de partida
- Mapeamento `ORIG_REGIAO` / `DEST_REGIAO` (Norte, Nordeste, etc.)
- Coordenadas geográficas dos aeroportos (lat/lon para mapa)
- Conversão de ICAO → IATA (remoção do prefixo "SB")

### Etapa 4 — Análise Exploratória (dashboards)
- Estatísticas descritivas por companhia, rota, região e período
- Identificação de sazonalidade, picos e tendências
- Análise de pontualidade e cancelamentos
- Comparação de tarifas entre companhias e rotas

---

## 💡 Principais Insights

| # | Insight | Relevância |
|---|---------|-----------|
| 1 | **São Paulo como hub dominante**: GRU e CGH concentram > 30% de todos os voos domésticos | Infraestrutura e concentração de mercado |
| 2 | **Sazonalidade forte**: picos em jan, jul e dez coincidem com férias e festas | Planejamento de demanda e precificação |
| 3 | **Recuperação pós-pandemia**: crescimento consistente de 2022 a 2024 | Recuperação do setor aéreo após COVID-19 |
| 4 | **Oligopólio**: Gol + LATAM + Azul somam >90% do mercado | Concentração competitiva e impacto no preço |
| 5 | **Atrasos aumentam à tarde**: voos noturnos acumulam mais atrasos por efeito cascata | Padrão operacional e planejamento de escala |
| 6 | **Tarifa inversamente proporcional ao volume**: rotas concorridas têm tarifas menores | Dinâmica de oferta/demanda e concorrência |
| 7 | **Nordeste subutilizado**: menor frequência de rotas regionais vs potencial turístico | Oportunidade de expansão da malha aérea |

---

## 🎨 Design dos Dashboards

### Dashboard 1 — Visão Geral (Painel Executivo)
- 6 KPIs principais (total de voos, companhias, rotas, atraso, cancelamentos, atraso médio)
- Mapa interativo com bolhas proporcionais ao volume por aeroporto
- Gráfico de market share por companhia
- Evolução temporal do volume de voos
- Sazonalidade por mês
- Top 15 rotas mais movimentadas
- Taxa de atraso por companhia
- Filtro por ano

### Dashboard 2 — Exploração Interativa
**5 abas temáticas:**
- **Rotas & Volume**: volume temporal, participação de mercado, top rotas, heatmap mês×dia
- **Pontualidade**: histograma de atrasos, atraso por empresa, atraso por hora, cancelamentos
- **Tarifas**: boxplot por empresa, série mensal, scatter tarifa×volume por rota
- **Comparativo**: eixo X, métrica e cor configuráveis dinamicamente
- **Tabela**: visualização tabular com filtros nativos, colunas selecionáveis

**Filtros interativos (sidebar):**
- Período (anos)
- Companhias aéreas
- Região de origem
- Tipo de voo (doméstico/internacional)
- Apenas voos atrasados

---

## 🛠 Tecnologias Utilizadas

| Biblioteca | Uso |
|-----------|-----|
| `pandas` | Manipulação e análise de dados |
| `numpy` | Cálculos numéricos |
| `requests` | Crawler HTTP |
| `dash` | Framework dos dashboards |
| `dash-bootstrap-components` | Layout e componentes visuais |
| `plotly` | Gráficos interativos |

---

## 👥 Equipe
Projeto Final — Banco de Dados Avançado
- Caio Adamo Scomparin - 23028248
- Rafael Tamura - 23024380
- Fabio Su Li - 23027760
- Henrique Zaccarias Martelini - 23024214
