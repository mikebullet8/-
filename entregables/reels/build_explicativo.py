# Genera un reel explicativo narrado: voz (Piper) + animación (explicativo.html) + subtítulos + música suave.
import json, subprocess, sys, os, wave, urllib.parse
S='/tmp/claude-0/-home-user--/e39b312e-db2c-59e3-989e-b8657ee61b78/scratchpad'
VOICE=f'{S}/voices/es_MX-claude-high.onnx'
spec=json.load(open(sys.argv[1])); name=os.path.splitext(os.path.basename(sys.argv[1]))[0]
work=f'{S}/exp_{name}'; os.makedirs(work,exist_ok=True)
parts=[]
for i,sc in enumerate(spec['scenes']):
    w=f'{work}/s{i}.wav'
    subprocess.run(['python3','-m','piper','-m',VOICE,'--length-scale','0.9','-f',w],input=sc['say'].encode(),check=True,stderr=subprocess.DEVNULL)
    with wave.open(w) as f: dur=f.getnframes()/f.getframerate(); sr=f.getframerate()
    sc['d']=round(dur+0.35,3); parts.append((w,sc['d']))
# narración con silencios
lst=f'{work}/list.txt'
with open(lst,'w') as L:
    for i,(w,d) in enumerate(parts):
        pad=f'{work}/p{i}.wav'
        subprocess.run(['ffmpeg','-y','-v','error','-i',w,'-af',f'apad=whole_dur={d}','-ar','44100','-ac','2',pad],check=True)
        L.write(f"file '{pad}'\n")
subprocess.run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',lst,'-c','copy',f'{work}/voz.wav'],check=True)
total=sum(d for _,d in parts)
import sfx
ev=[];t=0
for i,sc in enumerate(spec['scenes']):
    if i>0: ev.append(('whoosh',max(0,t-0.15)))
    for j,l in enumerate(sc.get('labels',[])): ev.append(('pop',t+l.get('at',0.4+j*0.5)))
    for j,l in enumerate(sc.get('props',[])): ev.append(('pop',t+l.get('at',0.5+j*0.5)))
    for j,l in enumerate(sc.get('clones',[])): ev.append(('pop',t+l.get('at',0.6+j*0.3)))
    if sc.get('flash') or sc.get('cta'): ev.append(('ding',t+0.2))
    t+=sc['d']
sfx.render(ev,total,f'{work}/sfx.wav')
json.dump({'scenes':spec['scenes']},open(f'{work}/data.json','w'),ensure_ascii=False)
subprocess.run(['node',f'{S}/rec2.js',os.path.abspath('explicativo.html'),f'{work}/data.json',f'{work}/v.webm',str(total)],check=True)
out=f'explicativos/{name}.mp4'
subprocess.run(['ffmpeg','-y','-v','error','-ss','0.3','-i',f'{work}/v.webm','-i',f'{work}/voz.wav','-i',f'{S}/lofi.wav','-i',f'{work}/sfx.wav',
 '-filter_complex','[1:a]volume=1.6[v];[2:a]volume=0.2[m];[3:a]volume=1.0[x];[v][m][x]amix=inputs=3:duration=first:dropout_transition=0:normalize=0[a]',
 '-map','0:v','-map','[a]','-t',str(total),'-vf','fps=30,format=yuv420p','-c:v','libx264','-preset','fast','-crf','20','-c:a','aac','-b:a','160k','-movflags','+faststart',out],check=True)
print(out,round(total,1),'s')
