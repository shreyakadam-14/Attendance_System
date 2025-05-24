import cv2
import face_recognition
import pickle
import os
from supabase import create_client, Client

# Supabase Configuration
# Replace with your Supabase URL and Anon Key
SUPABASE_URL = "https://utuwostgbayulslrgorj.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InV0dXdvc3RnYmF5dWxzbHJnb3JqIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc0NjY2ODksImV4cCI6MjA2MzA0MjY4OX0.CXWXfed1QO7sSwaciQwBUb1CB8ajgF0X6QAVfnMWX_c"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Importing student images
folderPath = 'images'
pathList = os.listdir(folderPath)
print(pathList)
imgList = []
studentIds = []

for path in pathList:
    imgList.append(cv2.imread(os.path.join(folderPath, path)))
    studentIds.append(os.path.splitext(path)[0])

    fileName = f'{folderPath}/{path}'
    try:
        # Upload image to Supabase Storage bucket named 'images'
        with open(fileName, 'rb') as f:
            supabase.storage.from_('images').upload(f'images/{os.path.basename(path)}', f.read(), {'content-type': 'image/png'})
        print(f"Uploaded {fileName} to Supabase Storage.")
    except Exception as e:
        print(f"Error uploading {fileName} to Supabase Storage: {e}")

print(studentIds)

def findEncodings(imagesList):
    encodeList = []
    for img in imagesList:
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # Handle cases where face_encodings might return an empty list
        encodings = face_recognition.face_encodings(img)
        if encodings:
            encodeList.append(encodings[0])
        else:
            print(f"Warning: No face found in one of the images. Skipping encoding for that image.")
            # You might want to remove the corresponding studentId or handle this error
            # in a way that prevents issues later. For now, it will just skip.
    return encodeList

print("Encoding Started ...")
encodeListKnown = findEncodings(imgList)
encodeListKnownWithIds = [encodeListKnown, studentIds]
print("Encoding Complete")

file = open("EncodeFile.p", 'wb')
pickle.dump(encodeListKnownWithIds, file)
file.close()
print("File Saved")