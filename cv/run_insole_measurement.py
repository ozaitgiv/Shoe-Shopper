from inference_sdk import InferenceHTTPClient
from dotenv import load_dotenv
import json
import os

load_dotenv()

dbg = False 

class PaperNotFoundError(Exception):
    """Raised when paper is not found in the image"""
    pass

class InsoleNotFoundError(Exception):
    """Raised when insole is not found in the image"""
    pass


# Initialize client with your API key
client = InferenceHTTPClient(
    api_url="https://serverless.roboflow.com",
    api_key = os.environ["ROBOFLOW_API_KEY"]
)

def run_insole_workflow(image_path):
    result = client.run_workflow(
        workspace_name="armaanai",
        workflow_id="insole-measuring",
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

        if class_id == 1:
            paper_dims = (width, height)
        elif class_id == 0:
            insole_dims = (width, height)

    return paper_dims, insole_dims

if __name__ == "__main__":
    image_path = input("Enter image path to analyze: ")

    result = run_insole_workflow(image_path)

    # Prints full prediction output
    # print(json.dumps(result, indent=2))

    result_json = result[0]
    paper, insole = parse_width_height(result[0])

    # Errors
    if (paper is None):
        raise PaperNotFoundError("Paper not detected in the image")
    if (insole is None):
        raise InsoleNotFoundError("Insole not detected in the image")
         
    """Using what we know about letter paper, we can create a pixel to inches conversion rate and extrapolate this to get the dimensions of the insole"""
    pixels_per_inch = paper[0] / 8.5
    paper_in_inches = (round(paper[0] / pixels_per_inch, 2), round(paper[1] / pixels_per_inch, 2))
    insole_in_inches = (round(insole[0] / pixels_per_inch, 2), round(insole[1] / pixels_per_inch, 2))
    
    if dbg:
        print(f"---pixel unit dimensions---")
        print(f"📄 Paper dimensions (w, h): {paper}")
        print(f"👟 Insole dimensions (w, h): {insole}")
    print(f"---Used Measurements---")
    print(f"📄 Paper dimensions in inches(w, h): {paper_in_inches}")
    print(f"👟 Insole dimensions in inches(w, h): {insole_in_inches}")
    
