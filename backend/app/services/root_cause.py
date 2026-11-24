def hypotheses():
 return [
  {"rank":1,"title":"Database connection-pool exhaustion","confidence":0.82,"status":"Leading hypothesis — unconfirmed",
   "why":"The pool maximum was reduced shortly before connection usage climbed; payment logs show acquisition timeouts.",
   "evidence":["EV-01","EV-03","EV-04"],"alternatives":["Database host saturation","Unexpected traffic spike"],"uncertainty":"No live DB telemetry or trace spans are connected."},
  {"rank":2,"title":"Database host resource saturation","confidence":0.43,"status":"Alternative hypothesis",
   "why":"Connection contention can coincide with host CPU or I/O pressure, but this fixture contains no host saturation evidence.",
   "evidence":["EV-01"],"alternatives":["Pool configuration regression"],"uncertainty":"Host CPU and I/O metrics are not available in this demo."},
  {"rank":3,"title":"Unexpected checkout traffic increase","confidence":0.26,"status":"Alternative hypothesis",
   "why":"Traffic growth could raise concurrency and pool demand; request-volume evidence is not present in the fixture.",
   "evidence":["EV-02"],"alternatives":["Pool configuration regression"],"uncertainty":"No request-volume baseline is connected."}
 ]
