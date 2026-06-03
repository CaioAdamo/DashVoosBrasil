# -*- coding: utf-8 -*-
"""Exporta os gráficos reais dos dashboards como PNG (para a apresentação)."""
import warnings, os
warnings.filterwarnings("ignore")
os.makedirs("assets", exist_ok=True)

import lib_dados as L
import dashboard_visao_geral as D
import dashboard_exploratorio as E

df = D.df
tf = E.tarifas


def salvar(fig, nome, w, h):
    fig.update_layout(title_text="", margin=dict(t=30, l=20, r=20, b=40),
                      paper_bgcolor="white", plot_bgcolor="white")
    fig.write_image(f"assets/{nome}.png", width=w, height=h, scale=2)
    print("ok:", nome)


# Mapa (mantém só margem mínima; já vem sem título)
m = L.mapa_malha(df, top_rotas=55, titulo="")
m.update_layout(margin=dict(t=10, l=0, r=0, b=0), paper_bgcolor="white")
m.write_image("assets/mapa.png", width=760, height=720, scale=2)
print("ok: mapa")

salvar(D.fig_share_grupo(df),        "share",     640, 470)
salvar(D.fig_evolucao(df),           "evolucao",  900, 430)
salvar(D.fig_hubs(df),               "hubs",      760, 440)
salvar(E._fig_fab(df),               "fabricante",740, 430)
salvar(E._fig_relacoes(df),          "relacoes",  880, 430)
salvar(E._fig_rkm(tf),               "rkm",       720, 430)
salvar(E._fig_cresc(df),             "cresc",     840, 470)

print("\nimagens em assets/:")
for f in sorted(os.listdir("assets")):
    print("  ", f)
