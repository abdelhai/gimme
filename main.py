import os, uuid
import openai
from deta import Drive
from fastapi import FastAPI, Response
from pydantic import BaseModel
import requests

from dotenv import load_dotenv

load_dotenv()

app = FastAPI()
files = Drive("files")
openai.api_key = os.getenv("OPEN_API_KEY")
BLACKHOLE = os.getenv("BLACKHOLE", None)
host = os.getenv("DETA_SPACE_APP_HOSTNAME")
onspace = os.getenv("DETA_SPACE_APP")
protocol = "https://" if onspace else "http://"


class Payload(BaseModel):
    prompt: str


def get_image_from_prompt(prompt):
    response = openai.Image.create(
        prompt=prompt,
        n=1,
        size="512x512",
    )
    imgurl = response["data"][0]["url"]
    r = requests.get(imgurl)
    sp = prompt.replace(" ", "_")
    iid = str(uuid.uuid4())[:8]
    name = f"{sp}_{iid}.png"
    files.put(name, r.content)
    if BLACKHOLE:
        r = requests.post(
            json={"url": imgurl},
            url=BLACKHOLE,
        )
    return Response(f"{protocol}{host}/i/{name}", media_type="text/plain")


@app.post("/image")
def generate(p: Payload):
    if not openai.api_key:
        return Response("set your openai api key ya dingus. it's in the app's settings")
    return get_image_from_prompt(p.prompt)


# server image from drive
@app.get("/i/{name}")
def serve(name: str):
    file = files.get(name)
    if not file:
        return Response("File not found ya dingus", status_code=404)
    return Response(file.read(), media_type="image/png")


@app.get("/__space/actions")
def meta():
    return {
        "actions": [
            {
                "name": "image",
                "path": "/image",
                "title": "Generate Image",
                "input": [{"name": "prompt", "type": "string"}],
            },
        ]
    }
