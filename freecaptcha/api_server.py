from fastapi import FastAPI, Query, Response, Form
from fastapi.responses import StreamingResponse, HTMLResponse
from typing import Optional
from io import BytesIO
from freecaptcha.image_generator import generate_captcha, RETURN_MODE_RETURN, RETURN_MODE_SAVE_FILE
import base64
import datetime
import os
from datetime import datetime, timedelta
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

PRIVATE_KEY = None
NONCE_SIZE = 12


def generate_or_load_key(path = "default_private.key"):
    if os.path.exists(path):
        return open(path, "rb").read()
    key = AESGCM.generate_key(bit_length = 256)
    with open(path, "wb") as f:
        f.write(key)
    return key


def create_secure_cookie_pair(cookie_name: str, key: bytes, data: str, ttl_minutes=5) -> dict:
    aes = AESGCM(key)
    global NONCE_SIZE
    nonce1 = os.urandom(NONCE_SIZE)
    nonce2 = os.urandom(NONCE_SIZE)
    salt = base64.urlsafe_b64encode(os.urandom(127)).decode()
    send_time = datetime.utcnow().isoformat()

    payload1 = f"{send_time}|{ttl_minutes}|{salt}".encode()
    payload2 = f"{send_time}|{data}".encode()

    encrypted1 = aes.encrypt(nonce1, payload1, None)
    encrypted2 = aes.encrypt(nonce2, payload2, None)

    return {
        f"{cookie_name}_time": base64.urlsafe_b64encode(nonce1 + encrypted1).decode(),
        f"{cookie_name}": base64.urlsafe_b64encode(nonce2 + encrypted2).decode()
    }



def read_secure_cookie(cookie_name: str, cookies, key: bytes) -> (bool, str):
    try:
        cookie_send_time = cookies[f"{cookie_name}_time"]
        cookie_name = cookie_name[f"{cookie_name}"]
        aes = AESGCM(key)
        ct1 = base64.urlsafe_b64decode(cookie_send_time)
        ct2 = base64.urlsafe_b64decode(cookie_answer)

        global NONCE_SIZE
        nonce1, encrypted1 = ct1[:NONCE_SIZE], ct1[NONCE_SIZE:]
        nonce2, encrypted2 = ct2[:NONCE_SIZE], ct2[NONCE_SIZE:]

        decrypted1 = aes.decrypt(nonce1, encrypted1, None).decode()
        decrypted2 = aes.decrypt(nonce2, encrypted2, None).decode()

        send_time1, ttl, salt = decrypted1.split("|")
        send_time2, value = decrypted2.split("|")

        assert send_time1 == send_time2
        ts = datetime.fromisoformat(send_time1)
        assert datetime.utcnow() - ts <= timedelta(minutes=ttl)

        return True, value  # Cookie recognised
    except Exception as e:
        return False, str(e)


def decrypt_data(private_key, encrypted: str) -> str:
    return private_key.decrypt(
        base64.urlsafe_b64decode(encrypted.encode()),
        padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
    ).decode()


app = FastAPI()


@app.get("/test", response_class = HTMLResponse)
def serve_test_page():
    with open("test_page.html", "r") as f:
      return f.read()


@app.get("/new_captcha")
def get_captcha(
    grid_size: int = Query(6, ge=3, le=30),
    noise_level: int = Query(3, ge=0, le=10),
    return_mode: str = Query("http"), # Could also be file
):
    if return_mode == "file":
        generate_captcha(grid_size, noise_level, RETURN_MODE_SAVE_FILE)
        return 200
    else:
        image, solution = generate_captcha(grid_size, noise_level, RETURN_MODE_RETURN)
        buf = BytesIO()
        image.save(buf, format="PNG")
        img_bytes = buf.getvalue()
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")

        return {
            "captcha_image": img_base64,
            "answer": solution
        }

@app.get("/check_captcha_passed_cookie_validity")
def http_check_captcha(
  captcha_passed_time: str = Query(),
  captcha_passed: str = Query()
):
  return str(is_captcha_complete({cookie.split("=")[0]: cookie.split("=")[1] for cookie in (captcha_passed_time, captcha_passed)})).lower()

@app.get("/embedded_captcha")
def generate_embedded_captcha(
    response: Response,
    grid_size: int = Query(6, ge=3, le=30),
    noise_level: int = Query(3, ge=0, le=10),
):
  global PRIVATE_KEY

  # CAPTCHA generation
  image, solution = generate_captcha(grid_size, noise_level, RETURN_MODE_RETURN)
  buf = BytesIO()
  image.save(buf, format="PNG")
  img_bytes = buf.getvalue()
  img_base64 = base64.b64encode(img_bytes).decode("utf-8")

  # Security features
  send_time = datetime.utcnow().isoformat()
  salt = base64.urlsafe_b64encode(os.urandom(16)).decode()
  # Encrypt send time with salt (to make CAPTCHAs expire)
  encrypted_send_time = encrypt_data(PUBLIC_KEY, f"{send_time}|{salt}".encode())

  # Encrypt captcha with send_time + salt (so that the server doesn't have to remember the answer)
  encrypted_answer = encrypt_data(PUBLIC_KEY, f"{captcha}|{send_time}|{salt}".encode())
  
  cookie_pair = create_secure_cookie_pair("captcha_answer", PRIVATE_KEY, solution, 5)
  for name, value in cookie_pair.items():
    response.set_cookie(name, value, httponly = True, path = "/")
  with open("embedded_captcha.html", "r") as f:
      return f.read().replace(r"{b64_image}", img_base64)


@app.get("/verify_embedded_captcha")
def verify_captcha(response: Response, answer: str = Form(...)):
  global PUBLIC_KEY
  cookies = request.cookies
  try:
      validity, captcha_value = read_secure_cookie("captcha_answer", cookies)
      if validity:
        if captcha_value == answer:
          cookie_pair = create_secure_cookie_pair("captcha_passed", PRIVATE_KEY, "true")
          for name, value in cookie_pair.items():
            response.set_cookie(name, value, httponly = True, path = "/")
          return "Success"
        else:
          return "Wrong answer"
      else:
        return "Invalid cookie, perhaps it has expired?"
  except Exception as e:
      return {"status": "CAPTCHA failed", "error": str(e)}

def is_captcha_complete(cookies: list[str]) -> bool:
  global PRIVATE_KEY
  try:
    _, value = read_secure_cookie("captcha_passed", cookies, PRIVATE_KEY)
    return value == "true"
  except:
    return False

def run_api_server(port: int = 3333, private_key_file: str = "private.key"):
  import uvicorn
  global PRIVATE_KEY
  PRIVATE_KEY = generate_or_load_key(private_key_file)
  uvicorn.run("freecaptcha.api_server:app", reload=True, port = port, host="localhost")