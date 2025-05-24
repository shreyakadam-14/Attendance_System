import os
import pickle
import numpy as np
import cv2
import face_recognition
import cvzone
from datetime import datetime
from supabase import create_client, Client
import requests

SUPABASE_URL = "https://utuwostgbayulslrgorj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV0dXdvc3RnYmF5dWxzbHJnb3JqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc0NjY2ODksImV4cCI6MjA2MzA0MjY4OX0.CXWXfed1QO7sSwaciQwBUb1CB8ajgF0X6QAVfnMWX_c"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

cap = cv2.VideoCapture(0)
cap.set(3, 640)
cap.set(4, 480)

if not cap.isOpened():
    exit()

imgBackground = cv2.imread('resources/background.png')
if imgBackground is None:
    exit()

folderModePath = 'resources/Modes'
if not os.path.exists(folderModePath):
    exit()

modePathList = os.listdir(folderModePath)
imgModeList = []
for path in modePathList:
    img = cv2.imread(os.path.join(folderModePath, path))
    if img is not None:
        imgModeList.append(img)

if not imgModeList:
    exit()

try:
    with open('EncodeFile.p', 'rb') as file:
        encodeListKnownWithIds = pickle.load(file)
    encodeListKnown, studentIds = encodeListKnownWithIds
except:
    exit()

modeType = 0
counter = 0
id = -1
imgStudent = []
studentInfo = None

while True:
    success, img = cap.read()
    if not success:
        break

    imgS = cv2.resize(img, (0, 0), fx=0.5, fy=0.5)
    imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
    faceCurFrame = face_recognition.face_locations(imgS)
    encodeCurFrame = []

    if faceCurFrame:
        try:
            encodeCurFrame = face_recognition.face_encodings(imgS, faceCurFrame)
        except:
            modeType = 0
            counter = 0
            id = -1
            studentInfo = None
            imgStudent = []
            continue
    else:
        modeType = 0
        counter = 0
        id = -1
        studentInfo = None
        imgStudent = []

    imgBackground[162:642, 55:695] = img
    if 0 <= modeType < len(imgModeList) and imgModeList[modeType] is not None:
        imgBackground[44:677, 808:1222] = imgModeList[modeType]
    elif imgModeList and imgModeList[0] is not None:
        imgBackground[44:677, 808:1222] = imgModeList[0]
    else:
        cv2.rectangle(imgBackground, (808, 44), (1222, 677), (0, 0, 0), -1)

    if faceCurFrame and encodeCurFrame:
        encodeFace = encodeCurFrame[0]
        faceLoc = faceCurFrame[0]

        if modeType == 0:
            matches = face_recognition.compare_faces(encodeListKnown, encodeFace)
            faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
            matchIndex = np.argmin(faceDis)

            if matches[matchIndex]:
                y1, x2, y2, x1 = faceLoc
                y1, x2, y2, x1 = y1 * 2, x2 * 2, y2 * 2, x1 * 2
                bbox = 55 + x1, 162 + y1, x2 - x1, y2 - y1
                imgBackground = cvzone.cornerRect(imgBackground, bbox, rt=0)
                id = studentIds[matchIndex]
                if counter == 0:
                    #cvzone.putTextRect(imgBackground, "Loading...", (275, 400), scale=2, thickness=2, colorR=(255, 255, 255), colorB=(0, 0, 0), offset=10)
                    cv2.imshow("Face Attendance", imgBackground)
                    cv2.waitKey(1)
                    counter = 1
                    modeType = 1

        elif modeType == 1:
            if counter == 1:
                try:
                    response = supabase.table("students").select("*").eq("id", id).execute()
                    if response.data:
                        studentInfo = response.data[0]
                        image_found = False
                        for ext in ["png", "jpg", "jpeg"]:
                            img_url = supabase.storage.from_("images").get_public_url(f"images/{id}.{ext}")
                            try:
                                img_response = requests.get(img_url)
                                img_response.raise_for_status()
                                img_array = np.frombuffer(img_response.content, np.uint8)
                                imgStudent = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
                                if imgStudent is not None and imgStudent.shape[0] > 0 and imgStudent.shape[1] > 0:
                                    imgStudent = cv2.resize(imgStudent, (216, 216))
                                    image_found = True
                                    break
                            except:
                                continue
                        if not image_found:
                            imgStudent = np.zeros((216, 216, 3), np.uint8)

                        last_attendance = studentInfo.get('last_attendance')
                        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        try:
                            if last_attendance:
                                datetimeObject = datetime.strptime(last_attendance, "%Y-%m-%d %H:%M:%S")
                                secondsElapsed = (datetime.now() - datetimeObject).total_seconds()
                                if secondsElapsed > 30:
                                    total_attendance = studentInfo['total_attendance'] + 1
                                    supabase.table("students").update({
                                        "total_attendance": total_attendance,
                                        "last_attendance": now_str
                                    }).eq("id", id).execute()
                                    studentInfo['total_attendance'] = total_attendance
                                    studentInfo['last_attendance'] = now_str
                                else:
                                    modeType = 3
                            else:
                                total_attendance = studentInfo.get('total_attendance', 0) + 1
                                supabase.table("students").update({
                                    "total_attendance": total_attendance,
                                    "last_attendance": now_str
                                }).eq("id", id).execute()
                                studentInfo['total_attendance'] = total_attendance
                                studentInfo['last_attendance'] = now_str
                        except:
                            pass
                    else:
                        modeType = 0
                        counter = 0
                        id = -1
                        studentInfo = None
                        imgStudent = []
                except:
                    modeType = 0
                    counter = 0
                    id = -1
                    studentInfo = None
                    imgStudent = []

            if studentInfo is not None:
                if 0 <= modeType < len(imgModeList) and imgModeList[modeType] is not None:
                    imgBackground[44:677, 808:1222] = imgModeList[modeType]

                cv2.putText(imgBackground, str(studentInfo.get('total_attendance', 0)), (861, 125), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 1)
                cv2.putText(imgBackground, str(studentInfo.get('major', 'N/A')), (1006, 550), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(imgBackground, str(id), (1006, 493), cv2.FONT_HERSHEY_COMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(imgBackground, str(studentInfo.get('standing', 'N/A')), (910, 625), cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                cv2.putText(imgBackground, str(studentInfo.get('year', 'N/A')), (1025, 625), cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)
                cv2.putText(imgBackground, str(studentInfo.get('starting_year', 'N/A')), (1125, 625), cv2.FONT_HERSHEY_COMPLEX, 0.6, (100, 100, 100), 1)

                student_name = studentInfo.get('name', 'Unknown Student')
                (w, _), _ = cv2.getTextSize(student_name, cv2.FONT_HERSHEY_COMPLEX, 1, 1)
                offset = (414 - w) // 2
                cv2.putText(imgBackground, student_name, (808 + offset, 445), cv2.FONT_HERSHEY_COMPLEX, 1, (50, 50, 50), 1)

                if imgStudent is not None and isinstance(imgStudent, np.ndarray) and imgStudent.shape[0] > 0 and imgStudent.shape[1] > 0:
                    imgBackground[175:391, 909:1125] = imgStudent
                else:
                    imgBackground[175:391, 909:1125] = np.zeros((216, 216, 3), np.uint8)

                counter += 1
                if counter > 10 and modeType == 1:
                    modeType = 2
                    counter = 0

            elif modeType == 2:
                counter += 1
                if counter > 20:
                    counter = 0
                    modeType = 0
                    id = -1
                    studentInfo = None
                    imgStudent = []

            elif modeType == 3:
                if counter < 10:
                    cv2.putText(imgBackground, "Already Checked In!", (830, 400), cv2.FONT_HERSHEY_COMPLEX, 0.8, (0, 255, 0), 2)
                counter += 1
                if counter > 20:
                    counter = 0
                    modeType = 0
                    id = -1
                    studentInfo = None
                    imgStudent = []
    else:
        modeType = 0
        counter = 0
        id = -1
        studentInfo = None
        imgStudent = []

    cv2.imshow("Face Attendance", imgBackground)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
