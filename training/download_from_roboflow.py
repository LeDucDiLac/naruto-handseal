from roboflow import Roboflow
from dotenv import load_dotenv
load_dotenv()
rf = Roboflow(api_key=os.getenv("ROBOFLOW_API_KEY"))
project = rf.workspace("naruto-handseal").project("naruto-hand-sign-p8toe-awsaf")
version = project.version(1)
dataset = version.download("yolo26")
                