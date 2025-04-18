from fastapi import FastAPI, Query, Response
from fastapi.responses import StreamingResponse, HTMLResponse
from typing import Optional
from io import BytesIO
from .image_generator import generate_captcha, RETURN_MODE_RETURN, RETURN_MODE_SAVE_FILE
import base64
import datetime


from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
PRIVATE_KEY = None
PUBLIC_KEY = None


def get_or_generate_keys(pub_path=None, priv_path=None, size=2048):
    def load(path, priv=False):
        try: data = open(path, 'rb').read()
        except: return None
        return serialization.load_pem_private_key(data, None) if priv else serialization.load_pem_public_key(data)

    pub, priv = load(pub_path), load(priv_path, True)
    if not pub or not priv:
        priv = rsa.generate_private_key(public_exponent=65537, key_size=size)
        pub = priv.public_key()
        if priv_path: open(priv_path, 'wb').write(priv.private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
        if pub_path: open(pub_path, 'wb').write(pub.public_bytes(
            serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo))
    return pub, priv

def encrypt_data(public_key, data: bytes) -> str:
    return base64.urlsafe_b64encode(
        public_key.encrypt(
            data,
            padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        )
    ).decode()


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

@app.get("/embedded_captcha")
def generate_embeded_captcha(
    grid_size: int = Query(6, ge=3, le=30),
    noise_level: int = Query(3, ge=0, le=10),
):
  global PRIVATE_KEY
  global PUBLIC_KEY

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
  response.set_cookie("Captcha_Send_Time", encrypted_send_time, httponly=True, path="/")
  response.set_cookie("Captcha_Answer", encrypted_answer, httponly=True, path="/")
  with open("embedded_captcha.html", "r") as f:
      return f.read().replace(r"{b64_image}", img_base64)

@app.get("/verify_embedded_captcha")
def verify_captcha():
  global PUBLIC_KEY
  global PRIVATE_KEY
  cookies = request.cookies
  try:
      decrypted_send_time = decrypt_data(private_key, cookies["Captcha_Send_Time"])
      decrypted_answer = decrypt_data(private_key, cookies["Captcha_Answer"])
      
      send_time, salt = decrypted_send_time.split("|")
      captcha_value, st2, salt2 = decrypted_answer.split("|")

      # Validate consistency
      assert send_time == st2
      assert salt == salt2

      # Check time validity
      dt = datetime.fromisoformat(send_time)
      assert (datetime.utcnow() - dt).seconds < 5 * 60  # 5 min expiration

      return {"status": "CAPTCHA passed"}
  except Exception as e:
      return {"status": "CAPTCHA failed", "error": str(e)}

def run_api_server(port: int = 8000):
  global PRIVATE_KEY
  global PUBLIC_KEY
  PRIVATE_KEY = rsa.generate_private_key(public_exponent=65537, key_size=4096)
  PUBLIC_KEY = private_key.public_key()
  import uvicorn
  uvicorn.run("freecaptcha.api_server:app", reload=True, port = port)
