import React,{useEffect,useRef,useState}from'react';
import{Activity,AlertTriangle,ShieldCheck,Network,ClipboardList,FileText,Mic,Radio,Play,RotateCcw,Search,ChevronRight,CheckCircle2,Lock,Zap,Volume2,ArrowUpRight,Server,Database,Ban,ShieldAlert,Eye,Lightbulb,UserCheck,Rocket,BadgeCheck}from'lucide-react';
import{AreaChart,Area,XAxis,YAxis,Tooltip,ResponsiveContainer,CartesianGrid,ReferenceLine}from'recharts';
import{api,post}from'./api';

const nav=[['Overview','overview',Activity],['Investigation','investigation',Search],['Service map','map',Network],['Approvals','approvals',ShieldCheck],['Audit trail','audit',ClipboardList],['Postmortem','postmortem',FileText],['Policy & security','policy',Lock]];
const TIER_LABEL={read_only:'READ-ONLY',nonprod_write:'NON-PROD WRITE',production_write:'PROD WRITE',destructive:'DESTRUCTIVE',unknown:'UNKNOWN'};
const DECISION_LABEL={ALLOW:'ALLOW',REQUIRES_APPROVAL:'NEEDS APPROVAL',REQUIRES_CONFIRMATION:'NEEDS CONFIRM',DENY:'DENY'};
// The agent loop, left to right. `tier` shows which gateway tier each step is governed by.
const FLOW=[
 {id:'detect',label:'Detect',sub:'Anomaly heuristic',icon:Radio},
 {id:'investigate',label:'Investigate',sub:'Read-only MCP calls',icon:Eye,tier:'read_only'},
 {id:'propose',label:'Propose',sub:'Dry runs, no changes',icon:Lightbulb,tier:'read_only'},
 {id:'approve',label:'Approve',sub:'Second teammate',icon:UserCheck,tier:'production_write'},
 {id:'execute',label:'Execute',sub:'Sandbox only',icon:Rocket,tier:'production_write'},
 {id:'verify',label:'Verify',sub:'Re-check metrics',icon:BadgeCheck,tier:'read_only'}];
// Index of the step currently in progress for each backend stage (FLOW.length = all done).
const STAGE_INDEX={idle:-1,propose:2,approve:3,execute:4,resolved:6};

export default function App(){
 const [page,setPage]=useState('overview');
 const [status,setStatus]=useState({active:false,stage:'idle',phase:'healthy',kill_switch:false});
 const [metrics,setMetrics]=useState(null),[evidence,setEvidence]=useState([]),[pred,setPred]=useState(null),[graph,setGraph]=useState(null),[recs,setRecs]=useState([]);
 const [mcpServers,setMcpServers]=useState(null);
 const [gateway,setGateway]=useState([]),[approval,setApproval]=useState(null),[preview,setPreview]=useState(null);
 const [audit,setAudit]=useState([]),[postmortem,setPostmortem]=useState(null),[policy,setPolicy]=useState(null),[brief,setBrief]=useState(''),[memory,setMemory]=useState('');
 const [notice,setNotice]=useState(''),[busy,setBusy]=useState(false);
 const active=status.active, phase=status.phase;

 async function refresh(){try{
  const s=await api('/status');setStatus(s);
  const [m,g,gl,pol,au,pm,ms]=await Promise.all([api('/metrics'),api('/blast-radius'),api('/gateway/log'),api('/policy'),api('/audit'),api('/postmortem'),api('/mcp/servers')]);
  setMetrics(m);setGraph(g);setGateway(gl.items);setPolicy(pol);setAudit(au.items);setPostmortem(pm);setMcpServers(ms.servers);
  if(s.active){const id=s.incident_id;const [ev,pr,rc]=await Promise.all([api(`/incidents/${id}/evidence`),api(`/incidents/${id}/predictions`),post(`/incidents/${id}/recommendations`)]);setEvidence(ev.items);setPred(pr);setRecs(rc.items)}
  else{setEvidence([]);setPred(null);setRecs([])}
 }catch(e){setNotice('Backend not connected — start FastAPI on port 8000. '+e.message)}}
 useEffect(()=>{refresh();const t=setInterval(refresh,6000);return()=>clearInterval(t)},[]);
 async function act(fn,msg){setBusy(true);setNotice('');try{await fn();await refresh();if(msg)setNotice(msg)}catch(e){setNotice(e.message);await refresh()}finally{setBusy(false)}}

 const trigger=()=>act(()=>post('/incidents/trigger',{}),'Incident triggered. The agent ran its read-only investigation through the policy gateway.');
 const reset=()=>act(async()=>{await post('/demo/reset',{});setApproval(null);setPreview(null);setBrief('')},'Demo reset to healthy baseline.');
 async function speak(){const b=await api('/voice/briefing');setBrief(b.text);if('speechSynthesis'in window){speechSynthesis.cancel();speechSynthesis.speak(new SpeechSynthesisUtterance(b.text))}}
 const dryRun=id=>act(async()=>setPreview(await post(`/actions/${id}/preview`,{environment:'SANDBOX'})),'Dry run checked by the gateway. Nothing was changed.');
 const requestApproval=()=>act(async()=>setApproval(await post('/actions/request-approval',{action_id:'ACT-ROLLBACK',requester:'oncall.primary'})),'Approval requested from a second teammate.');
 const decide=d=>act(async()=>{setApproval(await post(`/approvals/${approval.id}/decision`,{decision:d,approver:'teammate.approver',requester:'oncall.primary'}));setPreview(null)},`Approval ${d}d by teammate.approver.`);
 const execute=(id,confirmed=false)=>act(async()=>{const r=await post(`/actions/${id}/execute`,{confirmed});setPreview(null);setNotice(r.message)});
 const probe=(tool,server)=>act(()=>post('/gateway/probe',{tool,server}),`Gateway blocked "${tool}". See the gateway feed.`);
 const toggleKill=()=>act(()=>post('/policy/kill-switch',{enabled:!status.kill_switch}),status.kill_switch?'Kill switch off: writes allowed again (with policy checks).':'Kill switch on: every write is now blocked.');

 const a=metrics?.analysis, cur=a?.current||{latency:118,db:42,errors:.4};
 const tone=phase==='incident'?'orange':'green';
 const title=page==='overview'?'Incident overview':nav.find(x=>x[1]===page)?.[0];
 return <div className="shell">
  <aside className="sidebar"><div className="brand"><div className="brandmark">P<span>·</span></div><div><b>PAGER</b><small>INCIDENT COMMANDER</small></div></div>
   <div className="workspace"><span className="pulse"></span><div><b>Platform engineering</b><small>Demo environment</small></div><ChevronRight size={15}/></div>
   <div className="navlabel">WORKSPACE</div>
   {nav.map(([label,id,Icon])=><button key={id} className={'navitem '+(page===id?'selected':'')} onClick={()=>setPage(id)}><Icon size={17}/>{label}{id==='approvals'&&approval?.status==='pending'&&<i/>}</button>)}
   <div className="sidebottom"><div className={'secure'+(status.kill_switch?' off':'')}>{status.kill_switch?<ShieldAlert size={17}/>:<ShieldCheck size={17}/>}<div><b>{status.kill_switch?'Kill switch ON':'Policy gateway active'}</b><small>{status.kill_switch?'All agent writes blocked':`${gateway.filter(x=>x.kind==='call').length} tool calls checked`}</small></div></div>
    <div className="profile"><div className="avatar">OP</div><div><b>On-call operator</b><small>operator@pager.demo</small></div><span className="online"></span></div></div>
  </aside>
  <main className="main"><header className="topbar"><div className="crumb">Workspace <span>/</span> {nav.find(x=>x[1]===page)?.[0]}</div><div className="topright"><span className="env"><span/> LOCAL SIMULATION</span><span className="divider"/><span className="topdate">RIT HACKATHON · DEMO</span></div></header>
  <div className="content">
   <div className="pagehead"><div><div className="eyebrow">DETECT EARLY · INVESTIGATE INTELLIGENTLY · RESOLVE SAFELY</div><h1>{title}</h1><p>{page==='overview'?'Every agent action is checked by a deterministic MCP policy gateway before it runs.':'Evidence-led incident response with deterministic action governance.'}</p></div>
    <div className="headactions"><button className="btn secondary" onClick={reset} disabled={busy}><RotateCcw size={15}/> Reset demo</button><button className="btn primary" onClick={trigger} disabled={busy||active}><Play size={15} fill="currentColor"/> {phase==='recovered'?'Resolved':active?'Incident active':'Trigger incident'}</button></div></div>
   {notice&&<div className="notice"><span>{notice}</span><button onClick={()=>setNotice('')}>×</button></div>}

   {page==='overview'&&<>
    <Banner phase={phase}/>
    <AgentFlow stage={status.stage} calls={gateway.filter(x=>x.kind==='call'&&x.transport==='mcp'&&x.actor==='pager-agent'&&!x.purpose.startsWith('Verify')).length}/>
    <div className="grid2">
     <section className="panel"><PanelTitle title="Gateway feed" sub="Every MCP tool call the agent makes, the gateway's decision, and where it was sent" right={`${gateway.filter(x=>x.kind==='call').length} CALLS`}/><GatewayFeed items={gateway}/></section>
     <section className="panel"><PanelTitle title="Policy tiers" sub="How the gateway decides · enforced in code, outside the AI model"/><TierLegend tiers={policy?.tiers}/>
      <div className="probebox"><div><b>Prove it</b><small>Ask the agent to do something unsafe. The gateway blocks it and logs the attempt.</small></div><div className="actionrow"><button className="btn danger" onClick={()=>probe('drop_database')} disabled={busy}><Ban size={14}/> Try drop_database</button><button className="btn secondary" onClick={()=>probe('purge_logs','pager-monitoring')} disabled={busy}><Ban size={14}/> Try purge_logs (not in registry)</button></div><small className="probenote">purge_logs is a real tool on the pager-monitoring MCP server, and the server labels it read-only. The gateway denies it anyway: MCP annotations are metadata, not authorization.</small></div></section>
    </div>
    <div className="metricgrid">
     <Metric label="Predictive risk" value={a?.risk_score??0} unit="/100" foot={`Heuristic · ${a?.severity||'healthy'}`} icon={Activity} tone={tone}/>
     <Metric label="Payment P95 latency" value={cur.latency} unit="ms" foot={phase==='incident'?`${a?.signals?.[1]?.change??''} vs baseline`:phase==='recovered'?'Recovered · near baseline':'Within baseline'} icon={Zap} tone={phase==='incident'?'red':'green'}/>
     <Metric label="DB connections" value={cur.db} unit="%" foot={phase==='incident'?'Pool saturation trend':phase==='recovered'?'Recovered after rollback':'Healthy utilization'} icon={Database} tone={tone}/>
     <Metric label="Services at risk" value={graph?.at_risk??0} unit="/ 5" foot="Potential inferred impact" icon={Server} tone={graph?.at_risk?'orange':'green'}/>
    </div>
    <div className="grid2"><section className="panel"><PanelTitle title="Predictive signal trend" sub={phase==='recovered'?'Seeded telemetry · incident and recovery':'Seeded telemetry · 10-minute window'} right="SIMULATED"/><TrendChart series={a?.series}/></section>
     <section className="panel"><PanelTitle title="Leading root-cause hypothesis" sub="Evidence-backed · not confirmed"/>{active?<><div className="hypothesis"><div className="hypoicon"><Database size={20}/></div><div><b>Database connection-pool exhaustion</b><small>Deployment v2.4.1 · payment path</small></div><strong>82%</strong></div><p className="muted">{phase==='recovered'?'Rolling back the pool change restored latency and connection usage, which supports this hypothesis.':'Pool maximum was reduced shortly before connection usage climbed. Payment logs show acquisition timeouts.'}</p><div className="evidencechips"><span>EV-01 · get_metrics</span><span>EV-03 · get_logs</span><span>EV-04 · get_deployments</span></div><button className="textbutton" onClick={()=>setPage('investigation')}>Review investigation <ArrowUpRight size={14}/></button></>:<div className="empty"><Search size={24}/><b>No active investigation</b><span>Trigger the demo incident to surface hypotheses and evidence.</span></div>}</section></div>
    <div className="grid2"><section className="panel"><PanelTitle title="Service health" sub="Dependency-aware service status" right="5 SERVICES"/><div className="service-mini">{(graph?.nodes||[]).map(n=><div key={n.id}><i className={n.health}/>{n.name}</div>)}</div><button className="textbutton" onClick={()=>setPage('map')}>Open service map <ArrowUpRight size={14}/></button></section>
     <section className="panel"><PanelTitle title="Pager voice briefing" sub="Voice-first · text fallback available"/><div className="voicebox"><div className="voiceorb"><Mic size={21}/></div><div><b>{active?'Your incident briefing is ready':'Pager is standing by'}</b><small>{active?'Plays in your browser. No phone call is placed.':'Trigger an incident, then play the proactive briefing.'}</small></div><button className="roundbtn" onClick={speak}><Volume2 size={17}/></button></div>{brief&&<p className="brieftext">{brief}</p>}</section></div>
   </>}

   {page==='investigation'&&<>
    <div className="grid2"><section className="panel"><PanelTitle title="Predictive analysis" sub="Transparent prototype heuristic"/><div className="scoreline"><strong>{a?.risk_score??0}</strong><span>/ 100 risk score</span><b className={phase==='incident'?'textred':'textgreen'}>{(a?.severity||'healthy').toUpperCase()}</b></div><p className="muted">{a?.explanation}</p>{(a?.signals||[]).map(x=><div className="signalrow" key={x.name}><span>{x.name}</span><b>{x.value}</b><small>{x.change}</small></div>)}</section>
     <section className="panel"><PanelTitle title="Deployment risk predictor" sub="Recent deployment · v2.4.1"/>{pred?<><div className="scoreline"><strong>{pred.deployment.score}</strong><span>/ 100 deployment risk</span><b className="textred">{pred.deployment.band.toUpperCase()}</b></div>{pred.deployment.factors.map(f=><div className="factor" key={f.factor}><span>{f.factor}</span><b>+{f.points}</b></div>)}<small className="muted">{pred.deployment.disclaimer}</small></>:<Empty icon={Search} text="Trigger the incident to score the latest deployment."/>}</section></div>
    <section className="panel"><PanelTitle title="Root-cause hypotheses" sub="Ranked evidence, alternatives and uncertainty"/>{pred?pred.hypotheses.map(h=><div className="rootrow" key={h.rank}><div className="rank">{h.rank}</div><div className="rootbody"><div className="roottitle"><b>{h.title}</b><span>{h.status}</span></div><p>{h.why}</p><div className="evidencechips">{h.evidence.map(e=><span key={e}>{e}</span>)}</div><small>Alternatives: {h.alternatives.join(' · ')} · Uncertainty: {h.uncertainty}</small></div><strong>{Math.round(h.confidence*100)}%</strong></div>):<Empty icon={Search} text="No hypotheses yet."/>}</section>
    <section className="panel"><PanelTitle title="Correlated evidence" sub="Collected only through MCP tool calls the gateway allowed" right={`${evidence.length} ITEMS`}/>{evidence.length?evidence.map(e=><div className="evidencerow" key={e.id}><div className="evtag">{e.kind.toUpperCase()}</div><div><b>{e.id} · {e.signal}</b><small>via <code>{e.tool}</code> over MCP on {policy?.tools?.[e.tool]?.server} · {e.source} · {e.time}</small><p>{e.detail}</p></div><strong>{e.value}</strong></div>):<Empty icon={Search} text="No evidence collected yet."/>}</section>
   </>}

   {page==='map'&&<section className="panel"><PanelTitle title="Service dependency graph" sub="Arrows point from a service to what it depends on" right={phase==='incident'?'FAULT ACTIVE':'ALL HEALTHY'}/>
    <p className="muted maplead">{phase==='incident'?<>The fault starts at <b>Orders DB</b>. Every service that depends on it, directly or through another service, may be affected. Red dashed lines show that path.{preview&&<> The blue outline shows what the <b>{preview.action.title}</b> dry run would touch.</>}</>:phase==='recovered'?'After the sandbox rollback, the fault is gone and all services are back to healthy.':'No active fault. Trigger the incident to see how a database problem spreads to the services above it.'}</p>
    <ServiceMap graph={graph} highlight={preview?.blast_radius||[]}/>
    <div className="maplegend"><span><i className="healthy"/>Healthy</span><span><i className="degraded"/>Degraded</span><span><i className="at-risk"/>At risk</span><span><i className="critical"/>Fault source</span><span><i className="outline"/>Dry-run blast radius</span></div>
    <div className="mapnote"><AlertTriangle size={16}/> {graph?.explanation}</div></section>}

   {page==='approvals'&&<>
    <section className="panel"><PanelTitle title="Recommended remediation" sub="Each action is a tool call, so each has a gateway tier"/>{recs.length?recs.map(r=><div className="recrow" key={r.id}><div><div className="rechead"><b>{r.title}</b><TierBadge tier={r.tier}/></div><p>{r.benefit}</p><small>Tool <code>{r.tool}</code> · Risk: {r.risk} · Needs: {r.approval}</small></div><button className="btn secondary" onClick={()=>dryRun(r.id)} disabled={busy||phase==='recovered'}>Dry run</button></div>):<Empty icon={ShieldCheck} text="Trigger the incident to get recommended actions."/>}</section>
    {preview&&<DryRun p={preview} busy={busy} approval={approval} onRequest={requestApproval} onExecute={execute} onMap={()=>setPage('map')}/>}
    <section className="panel"><PanelTitle title="Approval queue" sub="Production-write policy · separate teammate required"/>{approval?<div className="approvalcard"><div className="approvaltop"><span className={'pill '+(approval.status==='pending'?'orange':approval.status==='approved'?'green':'red')}>{approval.status.toUpperCase()}</span><b>{approval.id}</b></div><h3>Rollback database configuration v2.4.1</h3><p>Requester: <b>{approval.requester}</b> · Environment: <b>SANDBOX</b></p><div className="diff">config/database.yaml<br/><span>− pool.max: 24</span><br/><span>+ pool.max: 80</span></div><p className="muted">Affected: Orders DB · Payment API · Order Service · Checkout. The requester cannot approve their own action.</p>{approval.status==='pending'?<div className="actionrow"><button className="btn danger" onClick={()=>decide('reject')} disabled={busy}>Reject request</button><button className="btn primary" onClick={()=>decide('approve')} disabled={busy}>Approve as teammate.approver</button></div>:<div className="successline"><CheckCircle2 size={16}/> {approval.status} by {approval.approver}</div>}</div>:<Empty icon={ShieldCheck} text="No pending approvals. Dry-run the rollback, then request approval."/>}</section>
    {approval?.status==='approved'&&phase!=='recovered'&&<section className="panel"><PanelTitle title="Approved action" sub="The gateway re-checks the approval when you execute · sandbox only"/><button className="btn primary" onClick={()=>execute('ACT-ROLLBACK')} disabled={busy}>Execute sandbox rollback</button></section>}
    {phase==='recovered'&&<section className="panel"><div className="successline big"><CheckCircle2 size={18}/> Rollback executed in the sandbox. The agent re-checked metrics through get_metrics: latency {cur.latency} ms, DB connections {cur.db}%.</div></section>}
   </>}

   {page==='audit'&&<section className="panel"><PanelTitle title="Audit trail" sub="Chronological tool, policy and action records"/>{audit.map(x=><div className="auditrow" key={x.id}><div className="auditdot"/><div><b>{x.event}</b><small>{x.ts} · {x.actor}</small><p>{x.detail}</p></div></div>)}</section>}

   {page==='postmortem'&&<section className="panel"><PanelTitle title="Incident postmortem draft" sub="Generated from seeded evidence and event timeline"/><div className="pmhead"><span className="pill blue">DRAFT</span><h2>{postmortem?.incident_id||'Awaiting incident'} · Payment API latency regression</h2><p>{postmortem?.incident_id?postmortem.summary:'Trigger the incident to generate a postmortem draft.'}</p></div>{[['Impact',postmortem?.impact],['Root-cause hypothesis',postmortem?.root_cause],['Gateway activity',postmortem?.incident_id&&`${postmortem.gateway_calls} tool calls checked by the policy gateway`],['Action taken',postmortem?.action],['Recovery verification',postmortem?.verification]].map(([h,v])=><div className="pmsection" key={h}><h4>{h}</h4><p>{(postmortem?.incident_id&&v)||'Pending'}</p></div>)}<div className="pmsection"><h4>Follow-up actions</h4>{(postmortem?.follow_ups||[]).map(x=><p key={x}>□ {x}</p>)}</div><button className="btn secondary" onClick={()=>navigator.clipboard?.writeText(JSON.stringify(postmortem,null,2))}>Copy postmortem JSON</button></section>}

   {page==='policy'&&<>
    <section className="panel"><PanelTitle title="Deterministic MCP policy gateway" sub="Policy is enforced in code, outside the AI model"/><TierLegend tiers={policy?.tiers} grid/>
     <div className="killrow"><div><b>Global agent-action kill switch {status.kill_switch&&<span className="pill red">ON</span>}</b><small>Blocks every agent write. Read-only investigation keeps working.</small></div><button className="btn danger" onClick={toggleKill} disabled={busy}>{status.kill_switch?'Disable kill switch':'Enable kill switch'}</button></div></section>
    <section className="panel"><PanelTitle title="Connected MCP servers" sub="What each server advertises (tools/list), compared with PAGER's trusted registry" right="OFFICIAL MCP PYTHON SDK"/><McpServers servers={mcpServers}/>
     <p className="muted">Read-only servers are real MCP servers, reached over an MCP client session. Each can also run on its own over stdio: <code>python -m app.mcp.servers pager-monitoring</code>. Write tools are mocked in a sandbox.</p></section>
    <section className="panel"><PanelTitle title="Trusted MCP tool registry" sub="Only these tools on these servers are known. Anything else is denied."/>{Object.entries(policy?.tools||{}).map(([k,v])=><div className="toolrow" key={k}><code>{k}</code><span>{v.server}</span><TierBadge tier={v.tier}/></div>)}<div className="toolrow"><code>anything else</code><span>any unregistered server</span><DecisionBadge decision="DENY"/></div></section>
    <section className="panel"><PanelTitle title="Incident memory" sub="Similar historical incidents (seeded)"/><button className="btn secondary" onClick={async()=>setMemory(JSON.stringify(await api('/memory'),null,2))}>Retrieve similar incidents</button>{memory&&<pre className="pre">{memory}</pre>}</section>
   </>}
   <footer> PAGER · RIT HACKATHON PROTOTYPE <span>All telemetry and write actions are simulated · No production systems are connected.</span></footer>
  </div></main></div>
}

function Banner({phase}){
 const V={healthy:['All systems operational','Baseline telemetry is stable. Trigger the seeded payment connection-pool regression to watch the agent investigate.','HEALTHY','green'],
  incident:['Predictive warning · Payment platform','Anomaly detected in the payment path. The agent investigated using read-only tools, each checked by the policy gateway.','INVESTIGATING','red'],
  recovered:['Resolved · Sandbox rollback verified','The approved rollback ran in the sandbox and the agent confirmed metrics are back near baseline.','RESOLVED','green']};
 const v=V[phase]||V.healthy;
 return <div className={'banner '+phase}><div className="bannericon">{phase==='recovered'?<CheckCircle2 size={19}/>:<Radio size={19}/>}</div><div><b>{v[0]}</b><p>{v[1]}</p></div><span className={'pill '+v[3]}>{v[2]}</span></div>}

function AgentFlow({stage,calls}){
 const at=STAGE_INDEX[stage]??-1;
 return <section className="panel flowpanel"><PanelTitle title="Agent loop" sub="What the agent is doing now. Every step from Investigate onward goes through the gateway." right={stage==='idle'?'WAITING FOR TRIGGER':stage==='resolved'?'COMPLETE':'IN PROGRESS'}/>
  <div className="flow">{FLOW.map((s,i)=>{const st=i<at?'done':i===at?'current':'pending';const Icon=s.icon;
   return <div className={'flowstep '+st} key={s.id}><div className="flowicon">{st==='done'?<CheckCircle2 size={16}/>:<Icon size={16}/>}</div><b>{s.label}</b><small>{s.id==='investigate'&&calls?`${calls} read-only MCP calls`:s.sub}</small>{s.tier&&<TierBadge tier={s.tier} small/>}</div>})}</div>
  <div className="gatewaybar"><ShieldCheck size={15}/><span><b>MCP policy gateway</b> checks the tool, its server and its tier against a trusted registry <b>before</b> the request reaches any MCP server. Unknown tools are denied and never sent.</span></div>
 </section>}

const TRANSPORT={mcp:['SENT VIA MCP','mcp'],'sandbox-mock':['SANDBOX MOCK','mock'],'not-sent':['NOT SENT','none']};
const fmtArgs=a=>Object.entries(a||{}).map(([k,v])=>`${k}=${JSON.stringify(v)}`).join(', ');
function GatewayFeed({items}){
 const box=useRef(null),delays=useRef({});
 if(!items.length)delays.current={};
 let k=0;items.forEach(x=>{const key=x.time+x.id;if(!(key in delays.current))delays.current[key]=(k++)*0.35});
 useEffect(()=>{if(box.current)box.current.scrollTop=box.current.scrollHeight},[items.length]);
 if(!items.length)return <Empty icon={ShieldCheck} text="No tool calls yet. Trigger the incident and watch the agent discover MCP tools and call them, each checked by the gateway first."/>;
 return <div className="feed" ref={box}>{items.map(x=>{const key=x.time+x.id,style={animationDelay:delays.current[key]+'s'};
  if(x.kind==='discovery')return <div className="feedrow discovery" key={key} style={style}><span className="feedno">{x.id}</span>
   <div className="feedbody"><div className="feedtop"><code>tools/list</code><span className="feedserver">{x.servers} MCP servers</span></div><small>{x.purpose}</small>{x.untrusted?.length>0&&<small className="feedreason">Not in registry, will be denied: {x.untrusted.join(', ')}</small>}</div>
   <div className="feedbadges"><span className="transport mcp">MCP DISCOVERY</span></div></div>;
  const t=TRANSPORT[x.transport]||TRANSPORT['not-sent'];
  return <div className={'feedrow '+x.decision.toLowerCase()} key={key} style={style}>
  <span className="feedno">{x.id}</span>
  <div className="feedbody"><div className="feedtop"><code>{x.tool}<span className="args">({fmtArgs(x.args)})</span></code><span className="feedserver">{x.server}</span>{x.dry_run&&<span className="dryflag">DRY RUN</span>}</div><small>{x.purpose}</small>{x.decision!=='ALLOW'&&<small className="feedreason">{x.reason}</small>}{x.error&&<small className="feedreason">MCP error: {x.error}</small>}</div>
  <div className="feedbadges"><div className="badgepair"><TierBadge tier={x.tier}/><DecisionBadge decision={x.decision}/></div><span className={'transport '+t[1]}>{t[0]}</span></div></div>})}</div>}

function McpServers({servers}){
 if(!servers)return null;
 return <div className="mcpservers">{servers.map(s=>{const mcp=s.name!=='pager-sandbox';return <div className={'mcpserver'+(mcp?'':' mocked')} key={s.name}>
  <div className="mcphead"><Server size={15}/><b>{s.name}</b><span className={'transport '+(mcp?'mcp':'mock')}>{mcp?'REAL MCP SERVER':'MOCKED'}</span></div>
  <small>{s.transport}</small>
  {s.tools.map(t=><div className="mcptool" key={t.name}><code>{t.name}<span className="args">({t.params.join(', ')})</span></code>{t.readOnlyHint&&<span className="hint">claims readOnlyHint</span>}{t.trusted?<TierBadge tier={t.tier}/>:<DecisionBadge decision="DENY"/>}</div>)}
 </div>})}</div>}

function TierLegend({tiers,grid}){return <div className={grid?'policytiers':'tierlist'}>{(tiers||[]).map((t,i)=><div className={'tier '+t.id} key={t.id}><span>TIER 0{i+1}</span><TierBadge tier={t.id}/><b>{t.rule}</b><p>e.g. {t.examples}</p></div>)}</div>}

function DryRun({p,busy,approval,onRequest,onExecute,onMap}){
 const g=p.gateway,id=p.action.id;
 let action=null;
 if(g.decision==='REQUIRES_APPROVAL'&&id==='ACT-ROLLBACK')action=approval?.status==='pending'?<span className="muted">Approval already requested. Waiting for a teammate below.</span>:<button className="btn primary" onClick={onRequest} disabled={busy}>Request second-person approval</button>;
 else if(g.decision==='REQUIRES_CONFIRMATION')action=<button className="btn primary" onClick={()=>onExecute(id,true)} disabled={busy}>Confirm and run in sandbox</button>;
 else if(g.decision==='ALLOW')action=<button className="btn primary" onClick={()=>onExecute(id)} disabled={busy}>{p.action.tier==='read_only'?'Run read-only call':'Execute in sandbox'}</button>;
 return <section className="panel"><PanelTitle title={`Dry run · ${p.action.title}`} sub="No changes have been made"/>
  <div className={'verdict '+g.decision.toLowerCase()}><DecisionBadge decision={g.decision}/><div><b>{g.next_step}</b><small>{g.reason}</small></div><TierBadge tier={g.tier}/></div>
  <div className="diff">{p.exact_change}{p.diff.map(d=><React.Fragment key={d}><br/><span className={d.startsWith('-')?'minus':'plus'}>{d}</span></React.Fragment>)}</div>
  <p className="muted">Target: {p.action.target} · Environment: {p.environment}</p>
  <div className="evidencechips">{p.blast_radius.map(b=><span key={b}>{b}</span>)}<button className="textbutton" onClick={onMap}>See blast radius on map <ArrowUpRight size={13}/></button></div>
  {action}</section>}

function TrendChart({series}){return <><div className="chartlegend"><span><i className="dot blue"/>Latency (ms)</span><span><i className="dot violet"/>DB pool (%)</span></div><div className="chart"><ResponsiveContainer width="100%" height="100%"><AreaChart data={series||[]}><defs><linearGradient id="lat" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#4c8dff" stopOpacity={.22}/><stop offset="100%" stopColor="#4c8dff" stopOpacity={0}/></linearGradient></defs><CartesianGrid stroke="#202d40" vertical={false}/><XAxis dataKey="t" stroke="#77869a" tickLine={false} axisLine={false}/><YAxis stroke="#77869a" tickLine={false} axisLine={false} domain={[0,320]}/><Tooltip contentStyle={{background:'#111c2d',border:'1px solid #2a3b52',borderRadius:8}}/><ReferenceLine y={250} stroke="#f47e83" strokeDasharray="4 4"/><Area type="monotone" dataKey="latency" stroke="#5b9bff" fill="url(#lat)" strokeWidth={2.5}/><Area type="monotone" dataKey="db" stroke="#a78bfa" fill="none" strokeWidth={2}/></AreaChart></ResponsiveContainer></div><div className="chartfoot"><span>Baseline <b>118 ms</b></span><span>Warning threshold (red dashed) <b>250 ms</b></span></div></>}

const NODE_W=150,NODE_H=58;
const HEALTH_COLOR={healthy:'#46c999',degraded:'#efb85e','at-risk':'#efb85e',critical:'#f1747d'};
function ServiceMap({graph,highlight}){
 if(!graph)return null;
 const byId=Object.fromEntries(graph.nodes.map(n=>[n.id,n]));
 return <div className="mapwrap"><svg viewBox="0 0 800 320" className="mapsvg" role="img" aria-label="Service dependency graph">
  <defs>{['plain','fault'].map(k=><marker key={k} id={'arrow-'+k} viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill={k==='fault'?'#f1747d':'#4d6584'}/></marker>)}</defs>
  {graph.edges.map(e=>{const a=byId[e.from],b=byId[e.to];return <line key={e.from+e.to} x1={a.x+NODE_W/2} y1={a.y} x2={b.x-NODE_W/2-4} y2={b.y} className={e.fault_path?'edge fault':'edge'} markerEnd={`url(#arrow-${e.fault_path?'fault':'plain'})`}/>})}
  {graph.nodes.map(n=>{const hl=highlight.includes(n.name);return <g key={n.id} className={'mapnode '+n.health}>
   {hl&&<rect x={n.x-NODE_W/2-6} y={n.y-NODE_H/2-6} width={NODE_W+12} height={NODE_H+12} rx="11" className="hlrect"/>}
   <rect x={n.x-NODE_W/2} y={n.y-NODE_H/2} width={NODE_W} height={NODE_H} rx="8" className="noderect"/>
   <circle cx={n.x-NODE_W/2+14} cy={n.y-8} r="4" fill={HEALTH_COLOR[n.health]}/>
   <text x={n.x-NODE_W/2+25} y={n.y-4} className="nodename">{n.name}</text>
   <text x={n.x-NODE_W/2+14} y={n.y+15} className="nodesub">{n.role} · {n.health}</text></g>})}
 </svg></div>}

function Metric({label,value,unit,foot,icon:Icon,tone}){return <div className="metric"><div className="metrichead"><span>{label}</span><Icon size={17}/></div><div className="metricvalue">{value}<small>{unit}</small></div><div className={'metricfoot '+tone}><i/>{foot}</div></div>}
function PanelTitle({title,sub,right}){return <div className="paneltitle"><div><h3>{title}</h3><p>{sub}</p></div>{right&&<span>{right}</span>}</div>}
function TierBadge({tier,small}){return <span className={'tierbadge '+tier+(small?' small':'')}>{TIER_LABEL[tier]||tier}</span>}
function DecisionBadge({decision}){return <span className={'decision '+decision.toLowerCase()}>{DECISION_LABEL[decision]||decision}</span>}
function Empty({icon:Icon,text}){return <div className="empty"><Icon size={24}/><span>{text}</span></div>}
