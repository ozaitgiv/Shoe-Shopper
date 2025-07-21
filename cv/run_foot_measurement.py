from inference_sdk import InferenceHTTPClient
from dotenv import load_dotenv
import json
import os

load_dotenv()

dbg = False 

class PaperNotFoundError(Exception):
    pass

class FootNotFoundError(Exception):
    pass


# Initialize client with your API key
client = InferenceHTTPClient(
    api_url="https://serverless.roboflow.com",
    api_key = os.environ["ROBOFLOW_API_KEY"]
)

def run_insole_workflow(image_path):
    result = client.run_workflow(
        workspace_name="armaanai",
        workflow_id="foot-measuring",
        images={"image": image_path},
        use_cache=True
    )
    return result

def parse_width_height(result_json):
    paper_dims = None
    insole_dims = None
    predictions_list = result_json["predictions"]["predictions"]
    for pred in predictions_list:
        class_id = pred.get("class_id")
        width = pred.get("width")
        height = pred.get("height")

        if class_id == 2:
            paper_dims = (width, height)
        elif class_id == 0:
            foot_dims = (width, height)

    return paper_dims, foot_dims 

if __name__ == "__main__":
    image_path = input("Enter image path to analyze: ")

    result = run_insole_workflow(image_path)

    # Prints full prediction output
    # print(json.dumps(result, indent=2))

    result_json = result[0]
    paper, foot = parse_width_height(result[0])

    # Errors
    if (paper is None):
        raise PaperNotFoundError("Paper not detected in the image")
    if (foot is None):
        raise FootNotFoundError("Foot not detected in the image")
         
    """Using what we know about letter paper, we can create a pixel to inches conversion rate and extrapolate this to get the dimensions of the insole"""
    pixels_per_inch = paper[0] / 8.5
    paper_in_inches = (round(paper[0] / pixels_per_inch, 2), round(paper[1] / pixels_per_inch, 2))
    foot_in_inches = (round(foot[0] / pixels_per_inch, 2), round(foot[1] / pixels_per_inch, 2))
    
    if dbg:
        print(f"---pixel unit dimensions---")
        print(f"📄 Paper dimensions (w, h): {paper}")
        print(f"🦶 Insole dimensions (w, h): {foot}")
    print(f"---Used Measurements---")
    print(f"📄 Paper dimensions in inches(w, h): {paper_in_inches}")
    print(f"🦶 Insole dimensions in inches(w, h): {foot_in_inches}")
