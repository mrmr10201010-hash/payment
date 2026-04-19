from flask import Flask, request, jsonify
import os
import requests
import hmac
import hashlib

app = Flask(__name__)

# --- الإعدادات ---
# مفتاح API الخاص بـ Easy Orders
EASY_ORDERS_API_KEY = "0c7b4bf3-99f2-4c50-860d-27d66e914a4a"

# كلمة سر الـ Webhook (يجب أن تضع نفس الكلمة في إعدادات Lemon Squeezy)
LEMONSQUEEZY_WEBHOOK_SECRET = os.environ.get("LEMONSQUEEZY_WEBHOOK_SECRET", "my_secret_key_123")

@app.route("/webhook/lemonsqueezy", methods=["POST"])
def lemonsqueezy_webhook():
    # 1. التحقق من التوقيع (Signature) لضمان الأمان
    signature = request.headers.get("X-Signature")
    if not signature:
        return jsonify({"message": "Missing signature"}), 401

    payload = request.get_data()
    digest = hmac.new(
        LEMONSQUEEZY_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(digest, signature):
        return jsonify({"message": "Invalid signature"}), 401

    # 2. قراءة البيانات القادمة من Lemon Squeezy
    data = request.json
    event_name = data.get("meta", {}).get("event_name")

    # نحن نهتم فقط بحدث إنشاء طلب جديد (الدفع الناجح)
    if event_name == "order_created":
        # استخراج رقم طلب Easy Orders الذي أرسلناه في كود الفوتر
        easy_orders_id = data.get("data", {}).get("attributes", {}).get("custom", {}).get("easy_orders_order_id")

        if easy_orders_id:
            print(f"Updating Easy Orders ID: {easy_orders_id}")
            
            # 3. تحديث حالة الطلب في Easy Orders إلى "مدفوع"
            url = f"https://api.easy-orders.net/api/v1/external-apps/orders/{easy_orders_id}/status"
            headers = {
                "Api-Key": EASY_ORDERS_API_KEY,
                "Content-Type": "application/json"
            }
            payload_update = {"status": "paid"}

            try:
                response = requests.patch(url, headers=headers, json=payload_update )
                response.raise_for_status()
                return jsonify({"message": "Success", "easy_orders_response": response.json()}), 200
            except requests.exceptions.RequestException as e:
                print(f"Error updating Easy Orders: {e}")
                return jsonify({"message": "Failed to update Easy Orders", "error": str(e)}), 500
        else:
            return jsonify({"message": "Easy Orders ID not found in custom data"}), 400

    return jsonify({"message": f"Event {event_name} ignored"}), 200

# هذا السطر مهم جداً ليعمل الكود على Vercel
app = app

if __name__ == "__main__":
    app.run(port=5000)
