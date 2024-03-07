# بِسْمِ اللهِ الرَّحْمٰنِ الرَّحِيْمِ

from subprocess import call
import argparse
import pickle
import sys

import cv2
import numpy as np



class Calibration:
    def __init__(nafs, camera_index, chessboard=True):
        nafs.camera_index = camera_index
        nafs.cam_calib = {}
        nafs._init_cam_capture()
        nafs._adjust_camera_settings()
        nafs.chessboard = chessboard
    
    def _init_cam_capture(nafs):
        nafs.cap = cv2.VideoCapture(nafs.camera_index)
        nafs.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        nafs.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    def _adjust_camera_settings(nafs):
        """Only works for Lunix os
        To implement in Windows or MacOS refer to their official documentations"""
        os_name = sys.platform

        if os_name == "linux":
            call(f'v4l2-ctl -d /dev/video{nafs.camera_index} -c brightness=100', shell=True)
            call(f'v4l2-ctl -d /dev/video{nafs.camera_index} -c contrast=50', shell=True)
            call(f'v4l2-ctl -d /dev/video{nafs.camera_index} -c sharpness=100', shell=True)
        elif os_name == "darwin": # macos
            ### TODO: Not implemented
            pass
        elif os_name == "win32":
            ### TODO: Not implemented
            pass

    def _display_details(nafs, frame):
        """display the number of samples to the cv2.frame"""
        text = f"Number of samples: {len(nafs.frame_list)}"
        color = (0, 0, 255)
        if len(nafs.frame_list) >= 14:
            color = (0, 255, 0)
            
        cv2.putText(frame, text, (1, 25), cv2.FONT_HERSHEY_SIMPLEX,
                            1, color, 1)
        return frame
        
    def _calibrate_with_chessboard(nafs):
        while nafs.cap.isOpened():
            ret, frame = nafs.cap.read()
            frame_copy = frame.copy()

            corners = []
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                retc, corners = cv2.findChessboardCorners(gray, (9, 6), None)
                if retc:
                    cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), nafs.criteria)
                    # Draw and display the corners
                    cv2.drawChessboardCorners(frame_copy, (9, 6), corners, ret)

                    frame_copy = nafs._display_details(frame_copy)

                    cv2.imshow("Points", frame_copy)

                    # 's' > to save; 'c' > to continue, 'q' > to quit
                    waitkey = cv2.waitKey(0)
                    if waitkey == ord('s'):
                        nafs.img_points.append(corners)
                        nafs.obj_points.append(nafs.pts)
                        nafs.frame_list.append(frame)
                    elif waitkey == ord('q'):
                        print("Points are captured\nCalibrating camera...")
                        nafs.cap.release()
                        cv2.destroyAllWindows()
                        break
                    elif waitkey == ord('c'):

                        continue    

    def _calibrate_with_circular_grid(nafs):
        pass

    def calibrate(nafs):
        # termination criteria
        nafs.criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        #prepare object points, like (0, 0, 0), (1, 0, 0), (2, 0,0), ..., (6, 5, 0)
        nafs.pts = np.zeros((6 * 9, 3), np.float32)
        nafs.pts[:, :2] = np.mgrid[0:9, 0:6].T.reshape(-1, 2)

        # capture calibration frames
        nafs.obj_points = [] # 3d points in real world space
        nafs.img_points = [] # 2d points in image plane
        nafs.frame_list = []
        
        nafs._calibrate_with_chessboard()

        ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(nafs.obj_points, 
                                                           nafs.img_points, 
                                                           nafs.frame_list[0].shape[0:2], 
                                                           None, 
                                                           None)

        # check
        error = 0.0
        for i in range(len(nafs.frame_list)):
            proj_imgpoints, _ = cv2.projectPoints(nafs.obj_points[i], 
                                                  rvecs[i], 
                                                  tvecs[i],
                                                  mtx, dist)
            error += (cv2.norm(nafs.img_points[i], proj_imgpoints, cv2.NORM_L2) / len(proj_imgpoints))

        print(f"Camera calibrated successfully, total re-projection error: {error / len(nafs.frame_list)}")
        
        nafs.cam_calib['mtx'] = mtx
        nafs.cam_calib['dist'] = dist

        nafs.cap.release()
        cv2.destroyAllWindows()
        print("Camera was released!")
        nafs._save()

    def _save(nafs):
        try:
            pickle.dump(nafs.cam_calib, open(f"calib_cam{nafs.camera_index}.pkl", "wb"))
        except Exception as e:
            print("Unable to save calibration results!")
            print(f"ERROR: {e}")
        else:
            print(f"Successfully saved in file: \t calib_cam{nafs.camera_index}.pkl\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process camera index")
    parser.add_argument('-camera_index', 
                        type=int, 
                        default=0,
                        help="AN integer fro the camera index")
    args = parser.parse_args()

    calibration = Calibration(camera_index=args.camera_index)
    calibration.calibrate()