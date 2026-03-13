# instance_id = 'https://api.ultramsg.com/instance118845/'
# token = 'x6ql6wjxhef1gqm6'
import requests
import frappe
@frappe.whitelist()
def send_whatsapp(mobile, message):
    instance_id = frappe.db.get_single_value("WhatsApp Settings", "instance_id")   # e.g. "instance12345"
    token = frappe.db.get_single_value("WhatsApp Settings", "token2")      # e.g. "abcd1234"
    url = f"https://api.ultramsg.com/{instance_id}/messages/chat"
    payload = {
        'token': token,
        'to': str(mobile),   # must be in international format, no "+" sign
        'body': message 
    }
    headers = {'content-type': 'application/json'}
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        frappe.msgprint("Message sent successfully")
    else:
        frappe.msgprint(f"Failed to send message: {response.text}")
   
    return response



