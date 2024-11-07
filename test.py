import jwt

data = {
    "account_phone": "0715700411",
    "email": "aqeglipambuya@gmail.com",
    "family_name": "Mbuya",
    "given_name": "Aqeglipa",
    "name": "Aqeglipa Mbuya",
    "picture": "https://lh3.googleusercontent.com/a/ACg8ocIT_d6PJsuw4KxtCBnprPf-jLSjDva0vCP6UJMSmzvE3qnwaEvY",
    "sub": "114248626444216198151"
}
if 'sub' in data:
    print("LEt gooo!!")
encoded_data = jwt.encode(payload=data,
                              key='secret',
                              algorithm="HS256")
decoded_data = jwt.decode(jwt=encoded_data,
                              key='secret',
                              algorithms=["HS256"])
print(encoded_data)
print(encoded_data.count('.'))
print(decoded_data)