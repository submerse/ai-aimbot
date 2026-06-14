import onnxruntime as ort
import numpy as np
import cv2
import time
import win32api
import serial
from utils.general import (cv2, non_max_suppression)
import torch

from config import aaMovementAmp, useMask, maskHeight, maskWidth, aaQuitKey, confidence, headshot_mode, cpsDisplay, visuals, onnxChoice, centerOfScreen, maskSide
import gameSelection

def main():
    port = input("Enter Arduino COM port (e.g. COM3 or /dev/ttyACM0): ").strip()
    arduino = serial.Serial()
    arduino.port = port
    arduino.baudrate = 115200
    arduino.timeout = 0.01
    arduino.dtr = False
    arduino.open()
    time.sleep(2)

    camera, cWidth, cHeight = gameSelection.gameSelection()

    count = 0
    sTime = time.time()
    TARGET_FPS = 120
    frame_interval = 1.0 / TARGET_FPS
    last_frame_time = time.time()

    # Pre-compute mask side once — avoids .lower() call every frame
    _maskSide = maskSide.lower() if useMask else None

    onnxProvider = ""
    if onnxChoice == 1:
        onnxProvider = "CPUExecutionProvider"
    elif onnxChoice == 2:
        onnxProvider = "DmlExecutionProvider"
    elif onnxChoice == 3:
        onnxProvider = "CUDAExecutionProvider"
    elif onnxChoice == 4:
        onnxProvider = "TensorrtExecutionProvider"

    print(f"Available providers: {ort.get_available_providers()}")
    print(f"Using provider: {onnxProvider}")

    so = ort.SessionOptions()
    so.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
    so.intra_op_num_threads = 4
    ort_sess = ort.InferenceSession('best.onnx', sess_options=so, providers=[onnxProvider])
    print(f"Active providers: {ort_sess.get_providers()}")

    COLORS = np.random.uniform(0, 255, size=(1500, 3))

    last_mid_coord = None
    while win32api.GetAsyncKeyState(ord(aaQuitKey)) == 0:

        npImg = np.array(camera.get_latest_frame())

        if useMask:
            if _maskSide == "right":
                npImg[-maskHeight:, -maskWidth:, :] = 0
            elif _maskSide == "left":
                npImg[-maskHeight:, :maskWidth, :] = 0
            else:
                raise Exception('ERROR: Invalid maskSide! Please use "left" or "right"')

        # Preprocessing: strip alpha, HWC->CHW, add batch dim, normalize — all in one pass
        img = npImg[:, :, :3] if npImg.shape[2] == 4 else npImg
        im = np.ascontiguousarray(img.transpose(2, 0, 1)[np.newaxis].astype(np.float16) / 255)

        outputs = ort_sess.run(None, {'images': im})

        pred = non_max_suppression(
            torch.from_numpy(outputs[0]), confidence, confidence, 0, False, max_det=10)

        # Build targets as plain numpy array — no pandas overhead
        targets_list = []
        for det in pred:
            if len(det):
                for *xyxy, conf, cls in reversed(det):
                    x1, y1, x2, y2 = float(xyxy[0]), float(xyxy[1]), float(xyxy[2]), float(xyxy[3])
                    targets_list.append([
                        (x1 + x2) / 2,  # cx
                        (y1 + y2) / 2,  # cy
                        x2 - x1,        # w
                        y2 - y1,        # h
                        float(conf)
                    ])

        if targets_list:
            targets = np.array(targets_list, dtype=np.float32)

            if centerOfScreen:
                dist = (targets[:, 0] - cWidth)**2 + (targets[:, 1] - cHeight)**2
                targets = targets[np.argsort(dist)]

            if last_mid_coord is not None:
                dist = np.sum((targets[:, :2] - last_mid_coord)**2, axis=1)
                targets = targets[np.argsort(dist)[::-1]]

            xMid = targets[0, 0]
            yMid = targets[0, 1]
            box_height = targets[0, 3]

            headshot_offset = box_height * (0.38 if headshot_mode else 0.2)
            mouseMove = [xMid - cWidth, (yMid - headshot_offset) - cHeight]

            if win32api.GetAsyncKeyState(0x2):
                dx = int(mouseMove[0] * aaMovementAmp)
                dy = int(mouseMove[1] * aaMovementAmp)
                arduino.write(f"M{dx},{dy}\n".encode())
            last_mid_coord = np.array([xMid, yMid], dtype=np.float32)

        else:
            last_mid_coord = None

        if visuals:
            for i in range(len(targets_list)):
                halfW = round(targets[i, 2] / 2)
                halfH = round(targets[i, 3] / 2)
                midX, midY = targets[i, 0], targets[i, 1]
                startX, startY = int(midX - halfW), int(midY - halfH)
                endX, endY = int(midX + halfW), int(midY + halfH)
                label = f"Human: {targets[i, 4] * 100:.2f}%"
                cv2.rectangle(npImg, (startX, startY), (endX, endY), COLORS[0], 2)
                y = startY - 15 if startY - 15 > 15 else startY + 15
                cv2.putText(npImg, label, (startX, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, COLORS[0], 2)

            cv2.imshow('Live Feed', npImg)
            if (cv2.waitKey(1) & 0xFF) == ord('q'):
                exit()

        count += 1
        if (time.time() - sTime) > 1:
            if cpsDisplay:
                print("CPS: {}".format(count))
            count = 0
            sTime = time.time()

        now = time.time()
        sleep_time = frame_interval - (now - last_frame_time)
        if sleep_time > 0:
            time.sleep(sleep_time)
        last_frame_time = now

    camera.stop()
    arduino.close()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print("ERROR: " + str(e))
