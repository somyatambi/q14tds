from http.server import BaseHTTPRequestHandler
import json
import os
import numpy as np

# CORS configuration
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
    "Access-Control-Expose-Headers": "Access-Control-Allow-Origin",
}

# Load telemetry data
def load_data():
    data_path = os.path.join(os.path.dirname(__file__), "q-vercel-latency.json")
    with open(data_path, "r") as f:
        return json.load(f)

class handler(BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        """Set CORS headers for all responses"""
        for header, value in CORS_HEADERS.items():
            self.send_header(header, value)
    
    def do_OPTIONS(self):
        """Handle preflight CORS requests"""
        self.send_response(200)
        self.send_header('Content-Type', 'text/plain')
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(b'')
    
    def do_POST(self):
        """Handle POST requests"""
        try:
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            body = json.loads(post_data)
            
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
            
            # Send successful response with CORS headers
            response = {"regions": results}
            self.send_response(200)
            self._set_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            # Send error response with CORS headers
            self.send_response(500)
            self._set_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
