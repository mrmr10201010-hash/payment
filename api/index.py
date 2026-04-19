from flask import Flask, request, jsonify
import os, requests, hmac, hashlib

app = Flask(__name__)

EASY_ORDERS_API_KEY = "0c7b4bf3-99f2-4c50-860d-27d66e914a4a"
LEMONSQUEEZY_API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiI5NGQ1OWNlZi1kYmI4LTRlYTUtYjE3OC1kMjU0MGZjZDY5MTkiLCJqdGkiOiJmYTMzNDI2OTRjNmNlMzU4OGUyYTUyNmFkM2FhMzBhYTM5MTAyYjNhOTY2Yzk3NDZjMmJiNjBjNzk3MTQ0YTJmYTEwNTNiNmYwMzU3NjY3ZSIsImlhdCI6MTc3MjQ4NTE4Ny45MzQxMywibmJmIjoxNzcyNDg1MTg3LjkzNDEzMiwiZXhwIjo0OTQ0MTUzNjAwLjAzNTgzOSwic3ViIjoiNjU5Mzc5MSIsInNjb3BlcyI6W119.Q_1utkF8GE9zWiKVmtA88sz-Fnw_nXknSAm1rdEXdQmZ27wuuRNgzY35z-pO-z1XfH6sevGapo_QXmRKKc9RxXGwxHk7j-qd5k67O2ZBSoX6VWRIIkCC5fmHsMAMT-Ns9yqRoXAK9OKZrZSPoqw9fvtlK8cxiq3HNPu8XascM5RkNH9XL4OoxBlhcgLH-ulJkRwFlbKJi8DdamfvznHGmpE9ojzP7imimNXXl_TD2tf98nLJXpxDfsXrS7rYKCRAElfY7DwuEj5Zm2km6FiAFAxF2DiL3wCO_sdOO2m45wi4S0plLunNGUIEdtDkQFuXso4DW9XAljYRn6qhkQ8eFsmYUD4m6h3XjhLEzgLmpZA_LBoTCBAuy4TopbO64S8rjeuW_ycx7K7y-UA8ZoqK84Vj-21PQVVhhTUNIQfwLHhlfrQZnlUpOzRIs2HKSxuiZ2k6AGE7NAcP3CoAUdEt7aQSh7Myn0eu6jgp5HciM389T6Uwp4v7ywWxqBHucRSiPxUIdDZs5Y61ZmJDsSZlWvjN3SXUQLqQV7_OVSuBJ2eyfmjN2tCVHgMPoH_aeMbX8rj9fIRRWKRXr9G0ZuEyJs8GrjCnx_ggGitglh1uDdn1RU7ubkP5ri-uEtbgpWsrmD3aq4GNZKG4Ajk4fNz9bkyDoJhBt1A9vCKQb19Qa8w"
LEMONSQUEEZY_WEBHOOK_SECRET = "my_secret_key_123"

# وظيفة 1: إنشاء رابط الدفع (يتم استدعاؤها من الفوتر)
@app.route("/api/create-checkout", methods=["GET"])
def create_checkout():
    order_id = request.args.get("order_id")
    if not order_id: return jsonify({"error": "No order_id"}), 400
    
    res = requests.post("https://api.lemonsqueezy.com/v1/checkouts", 
        headers={"Authorization": f"Bearer {LEMONSQUEEZY_API_KEY}", "Content-Type": "application/vnd.api+json"},
        json={"data": {"type": "checkouts", "attributes": {"checkout_data": {"custom": {"easy_orders_order_id": order_id}}},
            "relationships": {"store": {"data": {"type": "stores", "id": "302968"}}, "variant": {"data": {"type": "variants", "id": "1360733"}}}}}
     )
    return jsonify(res.json())

# وظيفة 2: استقبال تأكيد الدفع (يتم استدعاؤها من ليمون سكويز)
@app.route("/webhook/lemonsqueezy", methods=["POST"])
def webhook():
    signature = request.headers.get("X-Signature")
    payload = request.get_data()
    digest = hmac.new(LEMONSQUEEZY_WEBHOOK_SECRET.encode(), payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(digest, signature): return "Invalid", 401
    
    data = request.json
    if data.get("meta", {}).get("event_name") == "order_created":
        eo_id = data.get("data", {}).get("attributes", {}).get("custom", {}).get("easy_orders_order_id")
        if eo_id:
            requests.patch(f"https://api.easy-orders.net/api/v1/external-apps/orders/{eo_id}/status", 
                headers={"Api-Key": EASY_ORDERS_API_KEY}, json={"status": "paid"} )
    return "OK", 200

app = app
