"""
بِسْمِ اللهِ الرَّحْمٰنِ الرَّحِيْمِ
"""

from subprocess import call
import argparse
import yaml
import sys

import cv2
import numpy as np



class Calibration:
    def __init__(self, camera_index, chessboard=True):
        self.camera_index = camera_index
        self.cap = cv2.VideoCapture(camera_index)
        self.image_width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.image_height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.cam_calib = {
            "image_width": self.image_width,
            "image_height": self.image_height,
            "camera_matrix": {
                "rows": 3,
                "cols": 3,
                "data": [],
            },
            "distortion_coefficients": {
                "rows": 1,
                "cols": 5,
                "data": [],
            },
        }
        self._adjust_camera_settings()
        self.chessboard = chessboard

    def _adjust_camera_settings(self):
        """Only works for Lunix os
        To implement in Windows or MacOS refer to their official documentations"""
        os_name = sys.platform

        if os_name == "linux":
            call(f'v4l2-ctl -d /dev/video{self.camera_index} -c brightness=100', shell=True)
            call(f'v4l2-ctl -d /dev/video{self.camera_index} -c contrast=50', shell=True)
            call(f'v4l2-ctl -d /dev/video{self.camera_index} -c sharpness=100', shell=True)
        elif os_name == "darwin": # macos
            ### TODO: Not implemented
            pass
        elif os_name == "win32":
            ### TODO: Not implemented
            pass

    def _display_details(self, frame):
        """display the number of samples to the cv2.frame"""
        text = f"Number of samples: {len(self.frame_list)}"
        color = (0, 0, 255)
        if len(self.frame_list) >= 14:
            color = (0, 255, 0)

        cv2.putText(frame, text, (1, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, color, 1)
        return frame

    def _calibrate_with_chessboard(self):
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            frame_copy = frame.copy()
            corners = []
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                retc, corners = cv2.findChessboardCorners(gray, (9, 6), None)
                if retc:
                    cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), self.criteria)
                    # Draw and display the corners
                    cv2.drawChessboardCorners(frame_copy, (9, 6), corners, ret)

                    frame_copy = self._display_details(frame_copy)

                    cv2.imshow("Points", frame_copy)

                    # 's' > to save; 'c' > to continue, 'q' > to quit
                    waitkey = cv2.waitKey(0)
                    if waitkey == ord('s'):
                        self.img_points.append(corners)
                        self.obj_points.append(self.pts)
                        self.frame_list.append(frame)
                    elif waitkey == ord('q'):
                        print("Points are captured\nCalibrating camera...")
                        self.cap.release()
                        cv2.destroyAllWindows()
                        break
                    elif waitkey == ord('c'):
                        continue

    def _calibrate_with_circular_grid(self):
        pass

    def calibrate(self):
        # termination criteria
        self.criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        #prepare object points, like (0, 0, 0), (1, 0, 0), (2, 0,0), ..., (6, 5, 0)
        self.pts = np.zeros((6 * 9, 3), np.float32)
        self.pts[:, :2] = np.mgrid[0:9, 0:6].T.reshape(-1, 2)

        # capture calibration frames
        self.obj_points = [] # 3d points in real world space
        self.img_points = [] # 2d points in image plane
        self.frame_list = []

        self._calibrate_with_chessboard()

        ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
            self.obj_points,
            self.img_points,
            self.frame_list[0].shape[0:2],
            None,
            None
            )

        # check
        error = 0.0
        for i in range(len(self.frame_list)):
            proj_imgpoints, _ = cv2.projectPoints(
                self.obj_points[i],
                rvecs[i],
                tvecs[i],
                mtx, dist
                )
            error += (cv2.norm(self.img_points[i], proj_imgpoints, cv2.NORM_L2) / len(proj_imgpoints))

        print(f"Camera calibrated successfully, total re-projection error: {error / len(self.frame_list)}")

        self.cam_calib['camera_matrix']['data'] = mtx.tolist()
        self.cam_calib['distortion_coefficients']['data'] = dist.tolist()

        self.cap.release()
        cv2.destroyAllWindows()
        print("Camera was released!")
        self._save()

    def _save(self):
        try:
            with open(f"calib_cam{self.camera_index}.yaml", "w") as file:
                yaml.dump(self.cam_calib, file)
        except Exception as e:
            print("Unable to save calibration results!")
            print(f"Error: {e}")
        else:
            print(f"Successfully saved!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process camera index")
    parser.add_argument('-camera_index',
                        type=int,
                        default=0,
                        help="An integer for the camera index")
    args = parser.parse_args()

    calibration = Calibration(camera_index=args.camera_index)
    calibration.calibrate()
