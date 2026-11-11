const {chromium}=require('playwright');(async()=>{
const b=await chromium.launch();const p=await b.newPage({viewport:{width:540,height:960},deviceScaleFactor:2});
await p.goto('file://'+process.argv[2]);await p.waitForTimeout(500);
const T=await p.evaluate(()=>window.TOTAL);const fps=30;const n=Math.ceil(T*fps);
for(let i=0;i<n;i++){await p.evaluate(t=>render(t),i/fps);await p.screenshot({path:`${process.argv[3]}/f${String(i).padStart(4,'0')}.jpg`,type:'jpeg',quality:90});}
console.log(T,n);await b.close();})();
