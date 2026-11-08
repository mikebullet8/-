import sys, html; sys.path.insert(0,'.'); from contenido import CATS
n=0; secs=""
for cat, ps in CATS.items():
    items=""
    for p in ps:
        n+=1; items+=f'<div class="p"><span class="n">{n}</span><div>{html.escape(p)}</div></div>'
    secs+=f'<section><h2>{cat}</h2>{items}</section>'
assert n==100
open('pack.html','w').write(f'''<html><head><meta charset="utf-8"><style>
@page{{size:A4;margin:16mm}} @page:first{{margin:0}} body{{font-family:'DejaVu Sans',sans-serif;color:#111;font-size:10.5pt;line-height:1.45}}
.cover{{height:297mm;box-sizing:border-box;background:#0d0d0d;color:#fff;display:flex;flex-direction:column;justify-content:center;padding:0 18mm;page-break-after:always}}
.cover h1{{font-size:44pt;line-height:1.05;margin:0}} .y{{color:#FFD400}} .cover p{{font-size:14pt;color:#ccc}}
h2{{background:#FFD400;padding:6px 10px;font-size:14pt;margin:18px 0 8px;page-break-after:avoid}}
.p{{display:flex;gap:10px;border-left:3px solid #FFD400;background:#f6f6f6;padding:7px 10px;margin:6px 0;page-break-inside:avoid}}
.n{{font-weight:900;min-width:26px;color:#b08f00}} .tip{{border:2px solid #111;padding:12px;margin:12px 0}}
</style></head><body>
<div class="cover"><div style="font-size:40pt">⚡</div><h1>100 PROMPTS<br>DE IA PARA <span class="y">GANAR<br>DINERO</span> Y TIEMPO</h1>
<p>Copia, pega y adapta. Funcionan con Claude, ChatGPT y Gemini.</p><p style="color:#FFD400">Atajo IA</p></div>
<h2>Cómo usar este pack</h2>
<div class="tip"><b>1.</b> Copia el prompt. <b>2.</b> Cambia lo que está entre [corchetes] por tu situación real. <b>3.</b> Si la respuesta no te convence, usa el prompt 93: "Critica tu respuesta anterior… y dame una versión mejorada".</div>
<div class="tip"><b>La fórmula de un buen prompt:</b> ROL + TAREA + CONTEXTO + FORMATO. Cuanto más concreto seas con tu situación, mejor será la respuesta.</div>
{secs}
<h2>Aviso</h2><p>Estos prompts son herramientas: los resultados dependen de cómo los apliques. No garantizamos ingresos concretos. Revisa siempre lo que genera la IA antes de usarlo.</p>
</body></html>''')
