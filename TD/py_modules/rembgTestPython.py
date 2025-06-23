import json
from urllib import request

#This is the ComfyUI api prompt format.

#If you want it for a specific workflow you can "enable dev mode options"
#in the settings of the UI (gear beside the "Queue Size: ") this will enable
#a button on the UI to save workflows in api format.

#keep in mind ComfyUI is pre alpha software so this format will change a bit.

#this is the one for the default workflow
prompt_text = """
{
  "10": {
    "inputs": {
      "rem_mode": "RMBG-1.4",
      "image_output": "Preview",
      "save_prefix": "ComfyUI",
      "torchscript_jit": false,
      "add_background": "none",
      "refine_foreground": false,
      "images": [
        "30",
        0
      ]
    },
    "class_type": "easy imageRemBg",
    "_meta": {
      "title": "Image Remove Bg"
    }
  },
  "14": {
    "inputs": {
      "mask": [
        "10",
        1
      ]
    },
    "class_type": "MaskToImage",
    "_meta": {
      "title": "Convert Mask to Image"
    }
  },
  "15": {
    "inputs": {
      "filename_prefix": "mask",
      "images": [
        "14",
        0
      ]
    },
    "class_type": "SaveImage",
    "_meta": {
      "title": "Save Image"
    }
  },
  "30": {
    "inputs": {
      "image": "source1747328489.png"
    },
    "class_type": "LoadImageFromPath",
    "_meta": {
      "title": "Load Image From Path"
    }
  }
}
"""

def queue_prompt(prompt):
    p = {"prompt": prompt}

    # If the workflow contains API nodes, you can add a Comfy API key to the `extra_data`` field of the payload.
    # p["extra_data"] = {
    #     "api_key_comfy_org": "comfyui-87d01e28d*******************************************************"  # replace with real key
    # }
    # See: https://docs.comfy.org/tutorials/api-nodes/overview
    # Generate a key here: https://platform.comfy.org/login

    data = json.dumps(p).encode('utf-8')
    req =  request.Request("http://127.0.0.1:8188/prompt", data=data)
    request.urlopen(req)


prompt = json.loads(prompt_text)
#set the text prompt for our positive CLIPTextEncode
prompt["30"]["inputs"]["image"] = "source1747328743.png"


queue_prompt(prompt)