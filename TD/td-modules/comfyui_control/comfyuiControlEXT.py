# pylint: disable=missing-docstring,logging-fstring-interpolation
from vvox_tdtools.base import BaseEXT
import json
from vvox_tdtools.parhelper import ParTemplate
try:
	# import td
	from td import OP # type: ignore
	# TDJ = op.TDModules.mod.TDJSON
	# TDF = op.TDModules.mod.TDFunctions
except ModuleNotFoundError:
	from vvox_tdtools.td_mock import OP  #pylint: disable=ungrouped-imports 
	# from tdconfig import TDJSON as TDJ
	# from tdconfig import TDFunctions as TDF


class ComfyuiControlEXT(BaseEXT):
	def __init__(self, myop: OP) -> None:
		BaseEXT.__init__(self, myop, par_callback_on=True)
		self._createControlsPage()
		self.Me.par.opshortcut = 'comfyui_control'
		self.in_progress_prompts = op("in_progress_prompts")
		self.comfyui_url = root.var("comfyui_url")
		self.prompt_text =  """
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
		pass

	def OnInit(self):
		# return False if initialization fails
		return True
	
	def RequestComfy(self):
		prompt = json.loads(self.prompt_text)
	#set the text prompt for our positive CLIPTextEncode
		sourceFile = str(self.Me.par.Currentcapture.eval())
		prompt["12"]["inputs"]["image"] = sourceFile
		print("sourceFile: ", sourceFile)
		p = {"prompt": prompt}
		data = json.dumps(p).encode('utf-8')        
		op("webclient1").request(f"{self.comfyui_url}/prompt","POST", data=data)
		self.Me.par.Waitforcompletion = True
		op('completion_timer').par.start.pulse()
		print("Made Request to Comfy, starting pulse to find response")
		pass
		
	def CheckIfWorkflowComplete(self, prompt_id, prompt_data, row_index):
		print('hi')
		if not prompt_data["status"]:
			print("Prompt ID not found yet")
		else:
			status = prompt_data["status"]
			print(status["status_str"])
			
			if status["status_str"] == "success":
				#print(f"✅ Prompt {prompt_id} finished.")
				self.Me.par.Waitforcompletion = False
				print("The Prompt  Completed:  " + status["status_str"])  # Return the full prompt result if needed
				handstat = bool(prompt_data["outputs"]["36"]["text"][0])
				print("Hand Status: " + str(handstat))
				if self.Me.par.Enablehanddetection.eval():
					if handstat:
						op.state_control.par.Nextstate = op.state_control.PhotoCaptureScene
					else:
						print("NO HAND")
				images = prompt_data["outputs"]["90"]["images"]
				if images:
					image_path = images[0]["filename"]
					print("file path: " + str(image_path))
					op("result").replaceRow(0, str(image_path))
					op("in_progress_prompts").deleteRow(row_index)  # Remove the completed prompt from the in_progress_prompts table
					if self.in_progress_prompts.numRows == 0:
						op("completion_timer").par.initialize.pulse()
				# op('handstat').replaceRow(0,str(handstat))
		
	def HandleResponse(self, data: str) -> None:
		response = json.loads(data)
		if "prompt_id" in response:
			print("Starting workflow with id ", response["prompt_id"])
			op("in_progress_prompts").appendRow([response["prompt_id"]])
		else:
			
			if self.in_progress_prompts.numRows != 0:
				current_run_id = op("in_progress_prompts")[0,0].val
				print( " with prompt_id: ", current_run_id)
				if current_run_id in response:
					print("Found prompt_id in history: ", current_run_id)
					self.CheckIfWorkflowComplete(current_run_id, response[current_run_id],0)
					
		# Here you can handle the response data as needed
		# For example, you might want to parse it and update some parameters or UI elements
		pass
	
	def CheckForCompletion(self) -> None:
		print("Making request")
		op("webclient1").request(f"{self.comfyui_url}/history","GET")
		pass


	# Below is an example of a parameter callback. Simply create a method that starts with "_on" and then the name of the parameter.

	# def _onExampletoggle(self, par):
	#     self.Logger.debug(f"_onExampleToggle - val: {par.eval()}")
	#     pass

	# Below is an example of creating an event loop by overriding the OnFrameStart method.

	# def OnFrameStart(self, frame: int):
	#     if frame % 60 == 0:
	#         self.OnEventLoop1()
	#     return 

	# def OnEventLoop1(self):
	#     self.Print('every second')
	#     pass

	def _onProcessphoto(self, par):
		self.Print(f"_onProcessPhoto - val: {par.eval()}")
		self.RequestComfy()
		pass

	def _createControlsPage(self) -> None:
		page = self.GetPage('Controls')
		wait_for_completion_toggle = ParTemplate("WaitForCompletion", par_type='Toggle', label='WaitForCompletion')
		wait_for_completion_toggle.readOnly = True
		pars = [
			ParTemplate('ProcessPhoto', par_type='Pulse', label='ProcessPhoto'),
			ParTemplate("CurrentCapture", par_type='File', label='CurrentCapture'),
			ParTemplate("EnableHandDetection",par_type="Toggle", label="EnableHandDetection"),
			wait_for_completion_toggle,
		]
		for par in pars:
			par.createPar(page)

		pass

