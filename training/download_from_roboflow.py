from roboflow import Roboflow
from dotenv import load_dotenv
import os

load_dotenv()
rf = Roboflow(api_key=os.getenv("ROBOFLOW_API_KEY"))
project = rf.workspace("naruto-handseal").project("naruto-handsign")
version = project.version(2)
dataset = version.download("yolo26")
                