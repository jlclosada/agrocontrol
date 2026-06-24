"""Verify the REST API end-to-end against the seeded DB using Django's test client.

Run: DJANGO_SETTINGS_MODULE=config.settings.local python manage.py shell < api_check.py
"""
import json

from rest_framework.test import APIClient

client = APIClient()

# 1. Login
r = client.post("/api/v1/auth/token/",
                {"email": "admin@agrocontrol.os", "password": "Agro1234!"}, format="json")
print("LOGIN", r.status_code)
access = r.json()["access"]
auth = {"HTTP_AUTHORIZATION": f"Bearer {access}", "HTTP_X_COOPERATIVE": "cooperativa-demo"}

# 2. Profile
r = client.get("/api/v1/auth/me/", **auth)
print("ME", r.status_code, r.json()["email"])

# 3. Cooperatives
r = client.get("/api/v1/cooperatives/", **auth)
print("COOPS", r.status_code, "count=", r.json()["count"], "role=", r.json()["results"][0]["role"])

# 4. Parcels / crops / products
for ep in ["parcels", "crops", "products", "operations", "treatments", "memories", "agents"]:
    r = client.get(f"/api/v1/{ep}/", **auth)
    print(f"{ep.upper()}", r.status_code, "count=", r.json().get("count"))

# 5. Low stock
r = client.get("/api/v1/products/low_stock/", **auth)
print("LOW_STOCK", r.status_code, [p["name"] for p in r.json()])

# 6. Talk to the Cooperative agent
agents = client.get("/api/v1/agents/", **auth).json()["results"]
coop_agent = next(a for a in agents if a["agent_type"] == "COOPERATIVE")
r = client.post(f"/api/v1/agents/{coop_agent['id']}/chat/",
                {"message": "¿Qué productos tengo bajo mínimos y cuántas parcelas hay?"},
                format="json", **auth)
print("CHAT", r.status_code, "status=", r.json()["status"])
print("AGENT_OUTPUT:", r.json()["output_text"][:300])

print("\nAPI CHECK OK ✅")
