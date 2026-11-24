const BASE=import.meta.env.VITE_API_URL||'http://localhost:8000/api';
export async function api(path,options={}){const r=await fetch(BASE+path,{headers:{'Content-Type':'application/json'},...options});const d=await r.json();if(!r.ok)throw new Error(d.detail||'Request failed');return d}
export const post=(path,body={})=>api(path,{method:'POST',body:JSON.stringify(body)});
