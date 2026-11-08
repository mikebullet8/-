import subprocess, os, textwrap, sys
from PIL import Image, ImageDraw, ImageFont
W,H=1080,1920; BG=(15,14,11); FG=(243,241,234); Y=(255,212,0); MUTED=(169,165,150); PANEL=(30,29,23)
B='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'; R='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'; M='/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'
f=lambda p,s: ImageFont.truetype(p,s)
def wrap(d,text,font,maxw):
    words=text.split(); lines=[]; cur=''
    for w in words:
        t=(cur+' '+w).strip()
        if d.textlength(t,font=font)<=maxw: cur=t
        else: lines.append(cur); cur=w
    lines.append(cur); return lines
def card(kind, title, body=None, step=None):
    im=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(im)
    d.text((90,230),'⚡ ATAJO IA',font=f(B,40),fill=Y)
    x0, maxw = 90, W-90-170
    y=700 if kind!='hook' else 760
    if step: d.text((x0,y-110),step,font=f(B,44),fill=MUTED)
    size=96 if kind=='hook' else 72
    ft=f(B,size); hl=False; toks=[]
    for w in title.split():
        st=hl or w.startswith('*'); toks.append((w.replace('*',''),st))
        if w.startswith('*'): hl=True
        if w.endswith('*'): hl=False
    lines=[[]]; 
    for w,c in toks:
        t=' '.join(x for x,_ in lines[-1]+[(w,c)])
        if d.textlength(t,font=ft)>maxw and lines[-1]: lines.append([])
        lines[-1].append((w,c))
    for ln in lines:
        x=x0
        for w,c in ln:
            d.text((x,y),w,font=ft,fill=Y if c else FG); x+=d.textlength(w+' ',font=ft)
        y+=int(size*1.2)
    if body:
        y+=50; fb=f(M,44); lines=wrap(d,body,fb,maxw-60); h=len(lines)*60+70
        d.rounded_rectangle((x0-10,y,W-150,y+h),radius=24,fill=PANEL,outline=Y,width=4)
        yy=y+35
        for ln in lines: d.text((x0+25,yy),ln,font=fb,fill=FG); yy+=60
    return im
VIDEOS={
"01-prompt-dinero":[
 ('hook','Este prompt me dio 10 formas de *ganar dinero*',None,None),
 ('p','Cópialo tal cual:','Actúa como experto en negocios digitales. Tengo estas habilidades: [las tuyas]. Dame 10 formas de ganar dinero online con ellas usando IA, de más rápida a más lenta, con el primer paso de cada una.',None),
 ('p','Cambia [las tuyas] por lo que sabes hacer',None,'TRUCO'),
 ('cta','Tengo 99 prompts más así. *Enlace en mi perfil*',None,None)],
"02-deja-de-usar-ia-asi":[
 ('hook','Si usas la IA así, *pierdes el 90%*',None,None),
 ('p','Lo que hace casi todo el mundo:','"Dame ideas de negocio"','MAL'),
 ('p','*Hazlo* *así:*','Actúa como [experto]. Tu tarea es [tarea]. Contexto: [tu situación]. Formato: [tabla, lista...].','BIEN'),
 ('p','ROL + TAREA + CONTEXTO + FORMATO',None,'LA FÓRMULA'),
 ('cta','Guárdalo. 100 prompts listos *en mi perfil*',None,None)],
"03-truco-respuesta-mejor":[
 ('hook','Escribe esto después de *cualquier* respuesta de la IA',None,None),
 ('p','Copia esto:','Critica tu respuesta anterior como lo haría un experto exigente y luego dame una versión mejorada.',None),
 ('p','La IA revisa su propio trabajo y lo *mejora*',None,'POR QUÉ FUNCIONA'),
 ('cta','Sígueme para más *trucos de IA*',None,None)],
"04-entrevista-trabajo":[
 ('hook','Usa este prompt antes de tu próxima *entrevista*',None,None),
 ('p','Copia esto:','Simula una entrevista de trabajo para [puesto]. Hazme una pregunta cada vez y evalúa mis respuestas.',None),
 ('p','Practica hasta que te salga *natural*',None,'RESULTADO'),
 ('cta','Pack de 100 prompts *en mi perfil*',None,None)],
"05-ahorrar-10-horas":[
 ('hook','3 prompts que me ahorran *10 horas* a la semana',None,None),
 ('p','Organizar la semana','Organiza mi semana. Tareas: [lista]. Dame un horario realista priorizando lo que genera dinero.','1/3'),
 ('p','Resumir cualquier texto','Resume este texto en 5 puntos clave y 1 acción concreta: [texto].','2/3'),
 ('p','Vencer la pereza','Divide este proyecto [proyecto] en pasos tan pequeños que pueda empezar en 5 minutos.','3/3'),
 ('cta','Los 100 prompts están *en mi perfil*',None,None)],
}
tmp='/tmp/claude-0/-home-user--/e39b312e-db2c-59e3-989e-b8657ee61b78/scratchpad/tt'; os.makedirs(tmp,exist_ok=True)
for name,cards in VIDEOS.items():
    segs=[]
    for i,(k,t,b,s) in enumerate(cards):
        p=f'{tmp}/{name}-{i}.png'; card(k,t,b,s).save(p)
        dur=2.5 if k=='hook' else (5.5 if b and len(b)>120 else 4.0 if b else 3.0)
        seg=f'{tmp}/{name}-{i}.mp4'
        subprocess.run(['ffmpeg','-y','-v','error','-loop','1','-t',str(dur),'-i',p,'-vf',f'fade=in:0:8,format=yuv420p','-r','30','-c:v','libx264','-preset','veryfast',seg],check=True)
        segs.append(seg)
    lst=f'{tmp}/{name}.txt'; open(lst,'w').write(''.join(f"file '{s}'\n" for s in segs))
    subprocess.run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',lst,'-f','lavfi','-i','anullsrc=r=44100:cl=stereo','-shortest','-c:v','copy','-c:a','aac',f'{name}.mp4'],check=True)
    print(name)
