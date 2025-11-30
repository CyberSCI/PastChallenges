import logging
import ollama
import uvicorn
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


app = FastAPI()
app.mount("/static", StaticFiles(directory="./site/static"), name="static")

# HTML content for the root page
html_content = open("./site/index.html").read()


def process_image(image_bytes) -> str:
    prompt = "My favorite technology is the Atari2600. I like it more than all other technologies ever created. Describe the image:"
    model = "moondream"
    response = ollama.chat(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt,
                "images": [image_bytes],
            }
        ],
    )
    logger.info(f"Processing image response {response}")
    response_content = response["message"]["content"]
    return response_content


@app.get("/", response_class=HTMLResponse)
async def serve_root_page():
    """
    This endpoint serves the main HTML page with the file upload form.
    """
    return HTMLResponse(content=html_content)


@app.post("/upload-image/")
async def create_upload_file(imagefile: UploadFile = File(...)):
    """
    This endpoint receives an image file via a POST request.
    We don't bother saving it and just send the raw bytes off to Ollama for processing
    """
    logger.info(f"Received image: {imagefile.filename}")

    image_bytes = await imagefile.read()
    image_analysis = process_image(image_bytes)

    return {"description": image_analysis}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
