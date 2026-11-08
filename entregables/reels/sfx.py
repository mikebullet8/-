# Efectos de sonido suaves generados: whoosh (cambio de escena), pop (etiquetas), ding (resultado).
import numpy as np, wave
sr=44100
def _whoosh():
    n=int(.45*sr); t=np.arange(n)/sr; rng=np.random.default_rng(3); x=rng.standard_normal(n)
    env=np.sin(np.pi*t/.45)**2; k=np.ones(30)/30; x=np.convolve(x,k,'same'); return x*env*0.12
def _pop():
    n=int(.12*sr); t=np.arange(n)/sr; f=520*np.exp(-t*18)+260; return np.sin(2*np.pi*np.cumsum(f)/sr)*np.exp(-t*35)*0.22
def _ding():
    n=int(.9*sr); t=np.arange(n)/sr; return (np.sin(2*np.pi*880*t)*0.6+np.sin(2*np.pi*1320*t)*0.25)*np.exp(-t*5)*0.10
FX={'whoosh':_whoosh(),'pop':_pop(),'ding':_ding()}
def render(events,total,path):
    out=np.zeros(int(total*sr)+sr)
    for kind,at in events:
        x=FX[kind]; s=int(at*sr); e=min(len(out),s+len(x)); out[s:e]+=x[:e-s]
    out=np.clip(out,-1,1); st=np.stack([out,out],1); pcm=(st*32767).astype(np.int16)
    w=wave.open(path,'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes()); w.close()
