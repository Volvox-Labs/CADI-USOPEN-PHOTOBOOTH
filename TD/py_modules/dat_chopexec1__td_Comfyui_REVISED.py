# me - this DAT
# 
# channel - the Channel object which has changed
# sampleIndex - the index of the changed sample
# val - the numeric value of the changed sample
# prev - the previous sample value
# 
# Make sure the corresponding toggle is enabled in the CHOP Execute DAT.
import json
from urllib import request


import time

def queue_prompt(prompt):
    p = {"prompt": prompt}
    data = json.dumps(p).encode('utf-8')
    req = request.Request("http://127.0.0.1:8188/prompt", data=data)
    response = request.urlopen(req)
    response_data = json.load(response)
    return response_data["prompt_id"]

def get_node_output_value(prompt_id, node_id="69"):
    url = f"http://127.0.0.1:8188/history/{prompt_id}"

    for _ in range(20):
        try:
            response = request.urlopen(url)
            result = json.load(response)
            if prompt_id in result["history"]:
                outputs = result["history"][prompt_id]["outputs"]
                if node_id in outputs:
                    return outputs[node_id]
        except:
            pass
        time.sleep(0.5)

    return None

def onOffToOn(channel, sampleIndex, val, prev):
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
            "12",
            0
        ]
        },
        "class_type": "easy imageRemBg",
        "_meta": {
        "title": "Image Remove Bg"
        }
    },
    "12": {
        "inputs": {
        "image": "source1748459219.png"
        },
        "class_type": "LoadImage",
        "_meta": {
        "title": "Load Image"
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
    "21": {
        "inputs": {
        "mask_bbox_padding": 10,
        "resolution": 64,
        "mask_type": "based_on_depth",
        "mask_expand": 1,
        "rand_seed": 88,
        "detect_thr": 0.9000000000000001,
        "presence_thr": 0.9000000000000001,
        "image": [
            "12",
            0
        ]
        },
        "class_type": "MeshGraphormer-DepthMapPreprocessor",
        "_meta": {
        "title": "MeshGraphormer Hand Refiner"
        }
    },
    "24": {
        "inputs": {
        "mask": [
            "21",
            1
        ]
        },
        "class_type": "MaskToImage",
        "_meta": {
        "title": "Convert Mask to Image"
        }
    },
    "35": {
        "inputs": {
        "output_type": "int",
        "*": [
            "62",
            0
        ]
        },
        "class_type": "easy convertAnything",
        "_meta": {
        "title": "Convert Any"
        }
    },
    "36": {
        "inputs": {
        "preview": "",
        "source": [
            "62",
            0
        ]
        },
        "class_type": "PreviewAny",
        "_meta": {
        "title": "Preview Any"
        }
    },
    "62": {
        "inputs": {
        "brightness_threshold": 50,
        "mask": [
            "24",
            0
        ]
        },
        "class_type": "MaskAvgValueToBool",
        "_meta": {
        "title": "Avg Mask → Boolean"
        }
    },
    "67": {
        "inputs": {
        "expression": "1 - a",
        "a": [
            "35",
            0
        ]
        },
        "class_type": "MathExpression|pysssss",
        "_meta": {
        "title": "Math Expression 🐍"
        }
    },
    "69": {
        "inputs": {
        "a": [
            "67",
            0
        ]
        },
        "class_type": "CM_IntToBool",
        "_meta": {
        "title": "IntToBool"
        }
    },
    "76": {
        "inputs": {
        "preview": "",
        "source": [
            "69",
            0
        ]
        },
        "class_type": "PreviewAny",
        "_meta": {
        "title": "Preview Any"
        }
    },
    "90": {
        "inputs": {
        "save_condition": [
            "69",
            0
        ],
        "filename_prefix": "mask_",
        "images": [
            "14",
            0
        ]
        },
        "class_type": "SaveImageIfTrueSimple",
        "_meta": {
        "title": "Save Image If True (Simple)"
        }
    }
    }
	"""

    prompt = json.loads(prompt_text)
    sourceFile = str(op('latest')[1,0])
    prompt["12"]["inputs"]["image"] = sourceFile

    prompt_id = queue_prompt(prompt)
    output = get_node_output_value(prompt_id, node_id="69")

    if output:
        bool_result = output.get("result", [None])[0]
        print("Node 69 boolean value:", bool_result)
    else:
        print("No output received from node 69.")
        
        
    queue_prompt(prompt)
    
    return	
 
def whileOn(channel, sampleIndex, val, prev):
	return

def onOnToOff(channel, sampleIndex, val, prev):
	return

def whileOff(channel, sampleIndex, val, prev):
	return

def onValueChange(channel, sampleIndex, val, prev):
	return
	