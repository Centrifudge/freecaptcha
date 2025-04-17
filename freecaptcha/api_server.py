from fastapi import FastAPI, Query, Response
from fastapi.responses import StreamingResponse
from typing import Optional
from io import BytesIO
import freecaptcha.image_generator as image_generator
import base64


app = FastAPI()

@app.get("/test_captcha")
def serve_test_page():
    return Response(content="""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <title>CAPTCHA Test</title>
    </head>
    <body>
      <h1>CAPTCHA Test</h1>
      <button onclick="loadCaptcha()">Get New CAPTCHA</button>
      <div>
        <img id="captchaImg" alt="CAPTCHA will appear here" style="margin-top: 10px; width:80vw;" />
      </div>
      <p>Answer (for testing): <span id="captchaAnswer"></span></p>

      <script>
        async function loadCaptcha() {
          const response = await fetch('/new_captcha?grid_size=10&noise_level=3&return_mode=file');
          const data = await response.json();
          document.getElementById('captchaImg').src = 'data:image/png;base64,' + data.captcha_image;
          document.getElementById('captchaAnswer').textContent = data.answer;
        }
      </script>
    </body>
    </html>
    """, media_type="text/html")

@app.get("/new_captcha")
def get_captcha(
    grid_size: int = Query(10, ge=3, le=30),
    noise_level: int = Query(3, ge=0, le=10),
    return_mode: str = Query("http"), # Could also be file
):
    if return_mode == "file":
        image_generator.generate_captcha(grid_size, noise_level, image_generator.RETURN_MODE_SAVE_FILE)
        return 200
    else:
        image, solution = image_generator.generate_captcha(grid_size, noise_level, image_generator.RETURN_MODE_RETURN)
        buf = BytesIO()
        image.save(buf, format="PNG")
        img_bytes = buf.getvalue()
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")

        return {
            "captcha_image": img_base64,
            "answer": solution
        }


def run_api_server(port: int = 8000):
    import uvicorn
    uvicorn.run("api_server:app", reload=True, port = port)
