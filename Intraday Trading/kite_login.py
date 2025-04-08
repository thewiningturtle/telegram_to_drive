from kiteconnect import KiteConnect

# Replace with your API key and secret from Kite dashboard
api_key = "f9x86tckkv42mkgj"
api_secret = "enok19f7m3trolyngp59cggmyqvwz3ga"

kite = KiteConnect(api_key=api_key)

print("Login URL:")
print(kite.login_url())

# After login, you'll get a request token in the URL — paste it here
request_token = input("Paste your request token here: ")

# Exchange request token for access token
data = kite.generate_session(request_token, api_secret=api_secret)
print("Access Token:", data["access_token"])
