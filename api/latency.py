from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import os
import numpy as np

app = FastAPI()

# Enable CORS - following the recommended configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load telemetry data
def load_data():
    data_path = os.path.join(os.path.dirname(__file__), "q-vercel-latency.json")
    with open(data_path, "r") as f:
        return json.load(f)

@app.post("/api/latency")
async def analyze_latency(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold_ms = body.get("threshold_ms", 180)
    
    # Load and filter data
    data = load_data()
    
    results = {}
    
    for region in regions:
        # Filter records for this region
        region_data = [r for r in data if r["region"] == region]
        
        if not region_data:
            results[region] = {
                "avg_latency": 0,
                "p95_latency": 0,
                "avg_uptime": 0,
                "breaches": 0
            }
            continue
        
        # Extract metrics
        latencies = [r["latency_ms"] for r in region_data]
        uptimes = [r["uptime_pct"] for r in region_data]
        
        # Calculate statistics
        avg_latency = np.mean(latencies)
        p95_latency = np.percentile(latencies, 95)
        avg_uptime = np.mean(uptimes)
        breaches = sum(1 for lat in latencies if lat > threshold_ms)
        
        results[region] = {
            "avg_latency": round(float(avg_latency), 2),
            "p95_latency": round(float(p95_latency), 2),
            "avg_uptime": round(float(avg_uptime), 2),
            "breaches": breaches
        }
    
    return JSONResponse(content=results)

# Handler for Vercel
handler = app
