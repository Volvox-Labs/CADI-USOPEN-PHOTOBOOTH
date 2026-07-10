import json
import os
import subprocess
import time

import requests
import segno

BASE_URL = "https://ingest.curatorlive.com/upload"
MICROSITE_URL = "https://share.curatorlive.com/"
EVENT_CODE = "QFSVY8"
FFMPEG_PATH = "C:/ProgramData/chocolatey/bin/ffmpeg.exe"
AUTH_TOKEN = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIzIiwianRpIjoiOTRlMjg5NWNhOGFmZWVjN2YyMjBkMWQ1ODI2OWU2YzY0YzVmNWEzN2RmOGZmZmZjN2MyYzk2ZjBkNDFlOTgwMTc4NjRjZDg0M2YwYzEwOWYiLCJpYXQiOjE3NTM0NzgxNDcuNjUxNDU5LCJuYmYiOjE3NTM0NzgxNDcuNjUxNDYsImV4cCI6MTc4NTAxNDE0Ny42MzI0OTksInN1YiI6IjE0MjQ1Iiwic2NvcGVzIjpbImFwaSIsInJlYWQtZXZlbnRzIiwidXBsb2FkIl19.OQ5-Fz_1q-npufiyaV76PboSt6R-o8YXDSG3Hj-1iw1Zfo16iBYBsaO8THDhMikQ4QXD5s3zTXMvl-lkAY_IJiSqfrPEYqItBKhskDD1d4fuWE6zotPDS51CizvnTuzapdoUow1ilEzbtPewoGjbAeBx8UpeIV_vjj25Hzns6V1yd68wCDoPLDX6t8BxH_l-Di9VBfVRiv3Fo8lx2ylAMs_EfyOGHDLToMqXvYgNoaNptUOh0JwtPdJyBrGanU2qic--kOsHA8eZszI2eIDspi61Rl8_PNuNCcSGbQvJ18GLNh1sm5T4STORKOtnNrgRun4Zt1yStsCrMvZBw7f7hOqsX4CvIc328BjzsHd1pZl7_dkpT1t-75xp9c_n-z9tVZN1ThNG2Vg0QEtAP9s-AUMBtYt2K-krYFLe1qU06y-ITH8aX1DR8bivMnDX70T9PSADggePKfN5OkK45FZSYnUYWtfkMuHdO04CRc7BepEvj2KsYPzJHDH7QX2OERO1mgIr1jkrn4YZx6hf6usqvWUK5nqToNxO6PiZNURS1gVCI7-WyeRBrdItZLs7UP_8LgpTEuLqDEe8YFFu4pzZPk-9fgyJ4kFpnfs3PKIJQD83HVlKP3wSDmfek1TZHH_c38k_69YBchMzElZ67Ty2A_W_Nnahc5_IQp4Nt2DL7FE"
QR_CODE_DIR = "C:/Users/VVOX_NUC_0724/Documents/cadi/qrcode"


def _upload_video(video_file, timestamp):
	headers = {"Authorization": f"Bearer {AUTH_TOKEN}"}
	url = f"{BASE_URL}/{EVENT_CODE}"
	files = {"image": video_file}
	data = {"image_type": "video", "timestamp": timestamp, "faces": 0}
	try:
		response = requests.post(url, headers=headers, data=data, files=files, timeout=15)
		response.raise_for_status()
		return response.json()
	except requests.exceptions.RequestException as e:
		return {
			"result": "error",
			"error": str(e),
			"statusCode": e.response.status_code if e.response is not None else None,
			"data": None,
			"response_body": e.response.text if e.response is not None else None,
		}
	except json.JSONDecodeError:
		return {"result": "error", "error": "Invalid JSON response", "statusCode": response.status_code, "data": None, "response_body": response.text}


def _process_and_upload(file_name):
	if not file_name or not os.path.isfile(file_name):
		return {"status": "video_upload_error", "message": f"File not found: {file_name}"}

	base_name = file_name.replace("\\", "/").split("/")[-1].rsplit(".", 1)[0]
	qrcode_file_name = os.path.join(QR_CODE_DIR, f"{base_name}_qrcode.png")
	output_file_name = f"{base_name}_processed.mp4"
	print("Processing file to",output_file_name)
	ffmpeg_result = subprocess.run([
		FFMPEG_PATH,
		"-y",
		"-i", file_name,
		"-c:v", "libx264",
		"-movflags", "+faststart",
		"-pix_fmt", "yuv420p",
		"-preset", "fast",
		"-crf", "20",
		output_file_name,
	], stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW, check=True)
	if ffmpeg_result.returncode != 0:
		ffmpeg_log = ffmpeg_result.stdout.decode(errors="replace")
		print(f"ffmpeg failed ({ffmpeg_result.returncode}):\n{ffmpeg_log[-4000:]}")
		return {"status": "video_upload_error", "message": f"ffmpeg failed with code {ffmpeg_result.returncode}"}

	with open(output_file_name, "rb") as video_file:
		video_response = _upload_video(video_file, int(time.time()))
		retries = 2
		while video_response["result"] == "error" and retries > 0:
			video_file.seek(0)
			video_response = _upload_video(video_file, int(time.time()))
			retries -= 1

	if video_response["result"] == "error":
		return {"status": "video_upload_error", "message": f"Upload failed: {video_response['error']}"}
	else:
		print("Successfully uploaded", video_response)
	takeaway_id = video_response["data"]["id"]
	takeaway_url = f"{MICROSITE_URL}/{EVENT_CODE}/{takeaway_id}"
	qrcode = segno.make_qr(takeaway_url)
	qrcode.save(qrcode_file_name, scale=20, border=2)

	return {"status": "video_upload_success", "qr_code_path": qrcode_file_name}


def Setup(tmClientExt: object) -> object:
	"""
	Runs on the main thread. Reads the file path off the upload_control COMP
	(a plain TD object access) and returns it as a plain-data payload for RunInThread.
	"""
	movie = op.upload_control.par.Filepath.eval()
	return {"file_name": movie}


def RunInThread(tmClientExt: object, payload: object) -> None:
	"""
	Runs off the main thread. Must not touch any TD object - only plain Python
	(ffmpeg subprocess, HTTP upload, QR generation). Any raised exception is
	caught by the ThreadManager and routed to OnExcept below.
	"""
	result = _process_and_upload(payload["file_name"])
	tmClientExt.clientQueueManager.SetSuccessPayload(result)


def OnRefresh(tmClientExt: object, refreshPayload: object|None):
	pass


def OnSuccess(tmClientExt: object, successPayload: object):
	op.upload_control.HandleUploadResult(successPayload)


def OnExcept(tmClientExt: object, args):
	op.upload_control.HandleUploadException(args)
