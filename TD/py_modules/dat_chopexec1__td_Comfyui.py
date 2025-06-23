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

def onOffToOn(channel, sampleIndex, val, prev):
	

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

	def queue_prompt(prompt):
		p = {"prompt": prompt}

		data = json.dumps(p).encode('utf-8')
		req =  request.Request("http://127.0.0.1:8188/prompt", data=data)
		request.urlopen(req)


	prompt = json.loads(prompt_text)
	#set the text prompt for our positive CLIPTextEncode
	sourceFile = str(op('latest')[1,0])
	prompt["12"]["inputs"]["image"] = sourceFile


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
	