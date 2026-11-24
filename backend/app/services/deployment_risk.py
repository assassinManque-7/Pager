def score():
    factors=[{"factor":"Connection pool maximum reduced 80 → 24","points":35},
             {"factor":"Change touches payment critical path","points":25},
             {"factor":"Deployment occurred shortly before anomaly","points":20},
             {"factor":"No staged soak evidence in fixture","points":10}]
    return {"score":90,"band":"high","factors":factors,"deployment":"v2.4.1","commit":"a81f2c9",
            "diff":[{"file":"config/database.yaml","change":"pool.max: 80 → 24","risk":"high"},
                    {"file":"services/payment/connection.py","change":"acquire_timeout: 2s → 5s","risk":"medium"}],
            "disclaimer":"Rule-based deployment-risk heuristic for seeded demo data; not a production risk model."}
