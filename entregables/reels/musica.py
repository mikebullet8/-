# Música lo-fi suave generada (sin derechos de terceros): acordes de piano eléctrico + bombo suave + shaker.
import numpy as np, wave, sys
sr=44100; bpm=84; beat=60/bpm; dur=float(sys.argv[2]) if len(sys.argv)>2 else 60
t_total=int(sr*dur); out=np.zeros(t_total)
def note(f,start,length,vol):
    n=int(length*sr); t=np.arange(n)/sr
    env=np.minimum(1,t/0.02)*np.exp(-t*2.2)
    w=(np.sin(2*np.pi*f*t)+0.35*np.sin(2*np.pi*2*f*t)*np.exp(-t*4)+0.12*np.sin(2*np.pi*3*f*t)*np.exp(-t*6))
    s=int(start*sr); e=min(t_total,s+n)
    if s<t_total: out[s:e]+=vol*(w*env)[:e-s]
# Fmaj7, Em7, Dm7, Cmaj7 (voicings medios)
chords=[[174.61,220.0,261.63,329.63],[164.81,196.0,246.94,293.66],[146.83,174.61,220.0,261.63],[130.81,164.81,196.0,246.94]]
bar=4*beat; i=0; t=0
while t<dur:
    ch=chords[i%4]
    for k,f in enumerate(ch): note(f,t+k*0.012,bar*1.1,0.05)
    note(ch[-1]*2,t+2*beat,beat*1.5,0.025)
    t+=bar; i+=1
# bombo suave y shaker
n=int(0.25*sr); tt=np.arange(n)/sr
kick=np.sin(2*np.pi*(45+60*np.exp(-tt*30))*tt)*np.exp(-tt*14)*0.18
rng=np.random.default_rng(1); sh=rng.standard_normal(int(0.05*sr))*np.exp(-np.arange(int(0.05*sr))/sr*80)*0.012
b=0
while b*beat<dur:
    s=int(b*beat*sr)
    if b%2==0 and s+n<t_total: out[s:s+n]+=kick
    s2=int((b+0.5)*beat*sr)
    if s2+len(sh)<t_total: out[s2:s2+len(sh)]+=sh
    b+=1
# reverb sencilla y paso bajo
ir=rng.standard_normal(int(1.2*sr))*np.exp(-np.arange(int(1.2*sr))/sr*3.5)*0.03
wet=np.convolve(out,ir)[:t_total]; mix=out*0.8+wet*0.5
k=np.ones(8)/8; mix=np.convolve(mix,k,mode='same')
mix=mix/np.max(np.abs(mix))*0.5
fade=int(1.0*sr); mix[-fade:]*=np.linspace(1,0,fade)
st=np.stack([mix,mix],1); pcm=(st*32767).astype(np.int16)
w=wave.open(sys.argv[1],'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(sr); w.writeframes(pcm.tobytes()); w.close()
