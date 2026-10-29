import tkinter as tk
from tkinter import messagebox, simpledialog
import datetime
import os
import threading
import speech_recognition as sr
import pyttsx3
import webbrowser
import subprocess
import time
import pyautogui
import wikipedia
import cv2
import numpy as np
import urllib.request
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
try:
    import mysql.connector
except ImportError:
    mysql = None
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import mediapipe as mp

# Windows system volume control
from ctypes import cast, POINTER
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL

client = OpenAI()

try:
    engine = pyttsx3.init("sapi5")
except Exception:
    engine = pyttsx3.init()
voices = engine.getProperty("voices")

if voices:
    engine.setProperty("voice", voices[0].id)

engine.setProperty("rate", 170)
engine.setProperty("volume", 1.0)
speech_lock = threading.Lock()

conversation = []
listening = False
finger_mouse_running = False
eye_detector_running = False
face_unlock_running = False
face_registered = False
computer_control_running = False
gesture_volume_running = False

models_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
face_model_path = os.path.join(models_folder, "face_landmarker.task")
hand_model_path = os.path.join(models_folder, "hand_landmarker.task")
face_data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "face_data.json")
face_images_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "face_images")
mysql_host = os.getenv("MYSQL_HOST", "localhost")
mysql_user = os.getenv("MYSQL_USER", "computer_copilot")
mysql_password = os.getenv("MYSQL_PASSWORD", "")
mysql_database = os.getenv("MYSQL_DATABASE", "computer_copilot")
openai_model = os.getenv("OPENAI_MODEL", "gpt-6-luna")

face_model_url = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
hand_model_url = "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task"

m = tk.Tk()
m.title("Computer Copilot")
m.geometry("700x650")
m.resizable(False, False)

status_text = tk.StringVar()
status_text.set("Ready")
assistant_text = tk.StringVar()
assistant_text.set("Welcome to Computer Copilot")
speaking_mode = True

def speak(text):
    text = str(text)
    assistant_text.set(text)
    status_text.set("Speaking...")
    try:
        with speech_lock:
            engine.stop()
            engine.say(text)
            engine.runAndWait()
    except Exception as e:
        status_text.set("Voice error")
        print("Voice error:", e)
    finally:
        status_text.set("Ready")


def download_model(url, path):
    try:
        os.makedirs(models_folder, exist_ok=True)
        if not os.path.exists(path):
            speak("Downloading the camera model. Please wait.")
            urllib.request.urlretrieve(url, path)
        return True
    except Exception as e:
        speak("I could not download the camera model.")
        print("Model download error:", e)
        return False

def listen_command():
    recognizer = sr.Recognizer()

    try:
        with sr.Microphone() as source:
            status_text.set("Listening...")
            m.update()
            recognizer.pause_threshold = 1.0
            recognizer.adjust_for_ambient_noise(source, duration=1)

            try:
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
            except sr.WaitTimeoutError:
                return "none"

        status_text.set("Recognizing...")
        m.update()

        try:
            query = recognizer.recognize_google(audio, language="en-in")
            print("User said:", query)
            return query.lower()
        except sr.UnknownValueError:
            speak("I could not understand that.")
            return "none"
        except sr.RequestError:
            speak("There is a network problem.")
            return "none"
    except Exception as e:
        speak("Microphone error.")
        print("Microphone error:", e)
        return "none"

def speak_answer(text):
    if speaking_mode:
        speak(text)
    else:
        assistant_text.set(str(text))
        status_text.set("Ready")

def toggle_speaking_mode():
    global speaking_mode
    speaking_mode = not speaking_mode
    if speaking_mode:
        speaking_button.config(text="🔊 Speaking Mode: ON")
        status_text.set("Speaking mode enabled")
        speak("Speaking mode is now on. I will read my text answers aloud.")
    else:
        speaking_button.config(text="🔇 Speaking Mode: OFF")
        status_text.set("Speaking mode disabled")
        assistant_text.set("Speaking mode is off. Text answers will stay on screen.")

def ask_ai(query):
    global conversation

    try:
        conversation.append({"role": "user", "content": query})

        if len(conversation) > 10:
            conversation = conversation[-10:]

        response = client.responses.create(
            model=openai_model,
            instructions="You are Computer Copilot, a friendly voice assistant. Answer naturally and clearly. Keep answers reasonably short because they are spoken aloud. Do not use markdown unless necessary.",
            input=conversation
        )

        answer = response.output_text.strip()

        if not answer:
            answer = "I am not sure how to answer that."

        conversation.append({"role": "assistant", "content": answer})
        speak_answer(answer)

    except Exception as e:
        speak("I could not connect to the AI.")
        print("AI error:", e)

def greet_user():
    hour = int(datetime.datetime.now().hour)

    if 0 <= hour < 12:
        speak("Good Morning!")
    elif 12 <= hour < 18:
        speak("Good Afternoon!")
    else:
        speak("Good Evening!")

    speak("I am your Computer Copilot. How can I help you today?")

def open_youtube():
    speak("Opening YouTube")
    webbrowser.open("https://youtube.com")

def open_google():
    speak("Opening Google")
    webbrowser.open("https://google.com")

def open_gmail():
    speak("Opening Gmail")
    webbrowser.open("https://mail.google.com")

def open_whatsapp():
    speak("Opening WhatsApp")
    webbrowser.open("https://web.whatsapp.com")

def open_meet():
    speak("Opening Google Meet")
    webbrowser.open("https://meet.google.com")

def open_telegram():
    speak("Opening Telegram")
    webbrowser.open("https://web.telegram.org")

def open_chrome():
    try:
        speak("Opening Chrome")
        subprocess.Popen("cmd /c start chrome", shell=True)
    except Exception as e:
        speak("I could not open Chrome")
        print(e)

def open_calculator():
    try:
        speak("Opening Calculator")
        subprocess.Popen("calc.exe")
    except Exception as e:
        speak("I could not open Calculator")
        print(e)

def open_notepad():
    try:
        speak("Opening Notepad")
        subprocess.Popen("notepad.exe")
        time.sleep(2)
        pyautogui.write("HEY!!", interval=0.05)
        pyautogui.press("enter")
    except Exception as e:
        speak("I could not open Notepad")
        print(e)

def open_paint():
    try:
        speak("Opening Paint")
        subprocess.Popen("mspaint.exe")
    except Exception as e:
        speak("I could not open Paint")
        print(e)

def open_file_explorer():
    try:
        speak("Opening File Explorer")
        subprocess.Popen("explorer.exe")
    except Exception as e:
        speak("I could not open File Explorer")
        print(e)

def show_time():
    str_time = datetime.datetime.now().strftime("%I:%M %p")
    speak("The time is " + str_time)

def show_date():
    today = datetime.datetime.now().strftime("%d %B %Y")
    speak("Today's date is " + today)

def download_python():
    speak("Opening the Python download page")
    webbrowser.open("https://www.python.org/downloads/")

def download_pycharm():
    speak("Opening the official PyCharm download page")
    webbrowser.open("https://www.jetbrains.com/pycharm/download/?section=windows")

def show_news():
    speak("Opening News")
    webbrowser.open("https://youtube.com/@abpmajhatv?si=qMn1qPNZrgXlZfzi")

def mute_volume():
    try:
        speak("Muting volume")
        pyautogui.press("volumemute")
    except Exception as e:
        speak("I could not mute the volume")
        print(e)

def take_screenshot():
    try:
        folder = os.path.join(os.path.expanduser("~"), "Pictures", "ComputerCopilot")
        os.makedirs(folder, exist_ok=True)

        filename = datetime.datetime.now().strftime("screenshot_%Y%m%d_%H%M%S.png")
        filepath = os.path.join(folder, filename)

        powershell_command = "Add-Type -AssemblyName System.Windows.Forms; Add-Type -AssemblyName System.Drawing; $screen = [System.Windows.Forms.Screen]::PrimaryScreen; $bitmap = New-Object System.Drawing.Bitmap $screen.Bounds.Width, $screen.Bounds.Height; $graphics = [System.Drawing.Graphics]::FromImage($bitmap); $graphics.CopyFromScreen($screen.Bounds.Location, [System.Drawing.Point]::Empty, $screen.Bounds.Size); $bitmap.Save('" + filepath.replace("'", "''") + "'); $graphics.Dispose(); $bitmap.Dispose()"

        result = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", powershell_command],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise Exception(result.stderr)

        if not os.path.exists(filepath):
            raise Exception("Screenshot file was not created")

        speak("Screenshot taken and saved")
        print("Screenshot saved:", filepath)

    except Exception as e:
        speak("I could not take the screenshot")
        print("Screenshot error:", e)

def wikipedia_search(query):
    try:
        search_text = query
        search_text = search_text.replace("wikipedia", "")
        search_text = search_text.replace("search", "")
        search_text = search_text.replace("for", "")
        search_text = search_text.strip()

        if not search_text:
            speak("Please tell me what you want to search on Wikipedia")
            return

        speak("Searching Wikipedia for " + search_text)

        result = wikipedia.summary(search_text, sentences=2)
        print("Wikipedia:", result)
        speak(result)

    except wikipedia.exceptions.DisambiguationError:
        speak("Wikipedia found multiple results. Please be more specific")
    except wikipedia.exceptions.PageError:
        speak("I could not find that topic on Wikipedia")
    except Exception as e:
        speak("Wikipedia search failed")
        print("Wikipedia error:", e)

def type_message():
    try:
        speak("Opening Notepad for typing")
        subprocess.Popen("notepad.exe")
        time.sleep(2)

        speak("Please tell me what I should type")
        query = listen_command()

        if query == "none":
            return

        pyautogui.write(query, interval=0.05)
        pyautogui.press("enter")
        speak("Message typed successfully")

    except Exception as e:
        speak("I could not type the message")
        print(e)

def keyboard_control():
    try:
        speak("Keyboard control started")
        query = listen_command()

        if query == "none":
            return

        if "press enter" in query or query == "enter":
            pyautogui.press("enter")
            speak("Enter pressed")
        elif "press space" in query or query == "space":
            pyautogui.press("space")
            speak("Space pressed")
        elif "press backspace" in query or query == "backspace":
            pyautogui.press("backspace")
            speak("Backspace pressed")
        elif "press tab" in query or query == "tab":
            pyautogui.press("tab")
            speak("Tab pressed")
        elif "press escape" in query or query == "escape":
            pyautogui.press("esc")
            speak("Escape pressed")
        elif "press delete" in query or query == "delete":
            pyautogui.press("delete")
            speak("Delete pressed")
        elif "press up" in query:
            pyautogui.press("up")
            speak("Up pressed")
        elif "press down" in query:
            pyautogui.press("down")
            speak("Down pressed")
        elif "press left" in query:
            pyautogui.press("left")
            speak("Left pressed")
        elif "press right" in query:
            pyautogui.press("right")
            speak("Right pressed")
        elif "copy" in query:
            pyautogui.hotkey("ctrl", "c")
            speak("Copied")
        elif "paste" in query:
            pyautogui.hotkey("ctrl", "v")
            speak("Pasted")
        elif "select all" in query:
            pyautogui.hotkey("ctrl", "a")
            speak("Selected all")
        elif "save" in query:
            pyautogui.hotkey("ctrl", "s")
            speak("Saved")
        else:
            pyautogui.write(query, interval=0.05)
            speak("Typed successfully")

    except Exception as e:
        speak("Keyboard control failed")
        print("Keyboard error:", e)


def stop_computer_control():
    global computer_control_running
    computer_control_running = False
    try:
        computer_control_button.config(text="🖱 Computer Control")
    except:
        pass
    speak("Computer control stopped")

def execute_computer_control(query):
    if "stop computer control" in query or "stop control mode" in query:
        stop_computer_control()
        return False

    try:
        if query.startswith("type "):
            text = query[5:].strip()
            if text:
                pyautogui.write(text, interval=0.03)
                speak("Text typed")
                return True

        if query in ("click", "left click", "click mouse"):
            pyautogui.click()
            speak("Clicked")
            return True

        if query in ("double click", "double-click"):
            pyautogui.doubleClick()
            speak("Double clicked")
            return True

        if query in ("right click", "right-click"):
            pyautogui.rightClick()
            speak("Right clicked")
            return True

        if "scroll up" in query:
            pyautogui.scroll(5)
            speak("Scrolled up")
            return True

        if "scroll down" in query:
            pyautogui.scroll(-5)
            speak("Scrolled down")
            return True

        if query in ("move mouse to center", "center mouse"):
            width, height = pyautogui.size()
            pyautogui.moveTo(width // 2, height // 2, duration=0.3)
            speak("Mouse moved to the center")
            return True

        if query in ("press enter", "enter"):
            pyautogui.press("enter")
            speak("Enter pressed")
            return True

        if query in ("press space", "space"):
            pyautogui.press("space")
            speak("Space pressed")
            return True

        if query in ("press tab", "tab"):
            pyautogui.press("tab")
            speak("Tab pressed")
            return True

        if query in ("press escape", "escape", "esc"):
            pyautogui.press("esc")
            speak("Escape pressed")
            return True

        if "copy" == query:
            pyautogui.hotkey("ctrl", "c")
            speak("Copied")
            return True

        if "paste" == query:
            pyautogui.hotkey("ctrl", "v")
            speak("Pasted")
            return True

        if "select all" == query:
            pyautogui.hotkey("ctrl", "a")
            speak("Selected all")
            return True

        if "save" == query:
            pyautogui.hotkey("ctrl", "s")
            speak("Saved")
            return True

        if query in ("open browser", "open web browser"):
            open_chrome()
            return True

        if query in ("open file explorer", "open explorer"):
            open_file_explorer()
            return True

        if query in ("open notepad", "open text editor"):
            open_notepad()
            return True

        speak("I did not recognize that computer control command")
        return True
    except Exception as e:
        speak("Computer control failed")
        print("Computer control error:", e)
        return True

def computer_control():
    global computer_control_running
    if computer_control_running:
        stop_computer_control()
        return

    computer_control_running = True
    try:
        computer_control_button.config(text="🛑 Stop Computer Control")
    except:
        pass
    speak("Computer control is on. Say type, click, scroll, or press a key. Say stop computer control to stop.")
    threading.Thread(target=computer_control_loop, daemon=True).start()

def computer_control_loop():
    global computer_control_running
    while computer_control_running and listening:
        query = listen_command()
        if query == "none":
            continue
        if not execute_computer_control(query):
            break
    if computer_control_running and not listening:
        computer_control_running = False
        try:
            computer_control_button.config(text="🖱 Computer Control")
        except:
            pass

def setup_mysql():
    if mysql is None:
        return False
    try:
        connection = mysql.connector.connect(host=mysql_host, user=mysql_user, password=mysql_password)
        cursor = connection.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS " + mysql_database)
        cursor.close()
        connection.close()
        connection = mysql.connector.connect(host=mysql_host, user=mysql_user, password=mysql_password, database=mysql_database)
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS faces (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100) NOT NULL, image_path VARCHAR(500) NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
        connection.commit()
        cursor.close()
        connection.close()
        os.makedirs(face_images_folder, exist_ok=True)
        return True
    except Exception as e:
        print("MySQL error:", e)
        return False

def save_face_to_mysql(name, image_path):
    if mysql is None:
        return None
    try:
        connection = mysql.connector.connect(host=mysql_host, user=mysql_user, password=mysql_password, database=mysql_database)
        cursor = connection.cursor()
        cursor.execute("INSERT INTO faces (name, image_path) VALUES (%s, %s)", (name, image_path))
        connection.commit()
        row_id = cursor.lastrowid
        cursor.close()
        connection.close()
        return row_id
    except Exception as e:
        print("MySQL save error:", e)
        return None

def get_registered_faces():
    if mysql is None:
        return []
    try:
        connection = mysql.connector.connect(host=mysql_host, user=mysql_user, password=mysql_password, database=mysql_database)
        cursor = connection.cursor()
        cursor.execute("SELECT id, name, image_path FROM faces ORDER BY id")
        rows = cursor.fetchall()
        cursor.close()
        connection.close()
        return rows
    except Exception as e:
        print("MySQL read error:", e)
        return []

def extract_face_embedding(image, landmarker):
    if image is None or image.size == 0:
        return None
    if len(image.shape) == 2:
        rgb_image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    else:
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)
    result = landmarker.detect(mp_image)
    if not result.face_landmarks:
        return None
    landmarks = result.face_landmarks[0]
    if len(landmarks) < 10:
        return None
    points = np.array([[p.x, p.y, p.z] for p in landmarks], dtype=np.float32)
    center = points[1].copy()
    points = points - center
    scale = float(np.max(np.linalg.norm(points[:, :2], axis=1)))
    if scale <= 1e-6:
        return None
    points = points / scale
    embedding = points.reshape(-1)
    norm = float(np.linalg.norm(embedding))
    if norm <= 1e-6:
        return None
    return (embedding / norm).astype(np.float32)

def train_face_model():
    rows = get_registered_faces()
    if not rows:
        return False, "No registered users were found in MySQL"
    landmarker = get_face_landmarker()
    if landmarker is None:
        return False, "The MediaPipe face model could not be loaded"
    templates = []
    try:
        for row_id, name, image_path in rows:
            if not os.path.exists(image_path):
                continue
            image = cv2.imread(image_path)
            if image is None:
                continue
            embedding = extract_face_embedding(image, landmarker)
            if embedding is not None:
                templates.append({"id": int(row_id), "name": name, "embedding": embedding.tolist()})
    finally:
        landmarker.close()
    if not templates:
        return False, "No usable face embeddings were found"
    try:
        with open(face_data_path, "w", encoding="utf-8") as file:
            json.dump(templates, file)
        return True, ""
    except Exception as e:
        print("Face model save error:", e)
        return False, str(e)

def load_face_model():
    if not os.path.exists(face_data_path):
        return []
    try:
        with open(face_data_path, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, list) else []
    except Exception as e:
        print("Face model load error:", e)
        return []

def find_best_face_match(embedding, templates):
    best_name = None
    best_distance = 1.0
    for template in templates:
        saved = np.array(template.get("embedding", []), dtype=np.float32)
        if saved.shape != embedding.shape:
            continue
        distance = float(1.0 - np.dot(embedding, saved))
        if distance < best_distance:
            best_distance = distance
            best_name = template.get("name")
    return best_name, best_distance

def get_name_by_id(row_id):
    for saved_id, name, image_path in get_registered_faces():
        if saved_id == row_id:
            return name
    return None

def ask_registration_name():
    name = simpledialog.askstring("Register Face", "What is your name?", parent=m)
    if name is None:
        speak("Face registration cancelled.")
        return None
    name = name.strip()
    if not name:
        speak("Please enter a name.")
        return None
    return name

def start_register_face():
    name = ask_registration_name()
    if name:
        threading.Thread(target=register_face, args=(name,), daemon=True).start()

def register_face(name):
    global face_registered
    try:
        if not setup_mysql():
            speak("MySQL is not available. Please check your MySQL settings.")
            return
        speak("Hello " + name + ". Look at the camera. I will register your face.")
        landmarker = get_face_landmarker()
        if landmarker is None:
            speak("Face registration could not start.")
            return
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            speak("I could not open the camera.")
            landmarker.close()
            return
        samples = []
        start_time = time.time()
        while time.time() - start_time < 10:
            success, frame = camera.read()
            if not success:
                continue
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            result = landmarker.detect(mp_image)
            if result.face_landmarks:
                face = get_face_crop(frame, result.face_landmarks[0])
                if face is not None:
                    gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
                    gray = cv2.resize(gray, (200, 200))
                    if not samples or cv2.norm(gray, samples[-1], cv2.NORM_L2) > 2500:
                        samples.append(gray.copy())
                    cv2.putText(frame, "Face detected - registering", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.imshow("Face Registration - Press Q to stop", frame)
            if len(samples) >= 8:
                break
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        camera.release()
        cv2.destroyAllWindows()
        landmarker.close()
        if len(samples) < 3:
            speak("I could not capture enough face samples.")
            return
        saved_count = 0
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in name)
        for index, sample in enumerate(samples, 1):
            image_path = os.path.abspath(os.path.join(face_images_folder, safe_name + "_" + stamp + "_" + str(index) + ".jpg"))
            if cv2.imwrite(image_path, sample):
                row_id = save_face_to_mysql(name, image_path)
                if row_id is not None:
                    saved_count += 1
        if saved_count == 0:
            speak("The face images could not be saved to MySQL.")
            return
        trained, detail = train_face_model()
        if not trained:
            speak("The face was saved to MySQL, but face recognition could not be trained.")
            print("Training detail:", detail)
            return
        face_registered = True
        speak(name + " has been registered successfully in MySQL.")
    except Exception as e:
        speak("Face registration failed.")
        print("Face registration error:", e)
        cv2.destroyAllWindows()

def face_unlock():
    global face_unlock_running
    if face_unlock_running:
        speak("Face unlock is already running.")
        return
    if mysql is None:
        speak("MySQL connector is not installed.")
        return
    rows = get_registered_faces()
    if not rows:
        speak("No users are registered yet. Please register a face first.")
        return
    trained, detail = train_face_model()
    if not trained:
        speak("I could not prepare the face recognition model.")
        print("Training detail:", detail)
        return
    templates = load_face_model()
    if not templates:
        speak("The face recognition model is empty.")
        return
    face_unlock_running = True
    try:
        speak("Face unlock started. Look at the camera.")
        landmarker = get_face_landmarker()
        if landmarker is None:
            face_unlock_running = False
            return
        camera = cv2.VideoCapture(0)
        if not camera.isOpened():
            speak("I could not open the camera.")
            landmarker.close()
            face_unlock_running = False
            return
        unlocked = False
        recognized_name = None
        start_time = time.time()
        while time.time() - start_time < 15:
            success, frame = camera.read()
            if not success:
                continue
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            result = landmarker.detect(mp_image)
            message = "Looking for a registered face"
            if result.face_landmarks:
                face = get_face_crop(frame, result.face_landmarks[0])
                if face is not None:
                    embedding = extract_face_embedding(face, landmarker)
                    if embedding is not None:
                        name, distance = find_best_face_match(embedding, templates)
                        if name and distance < 0.28:
                            message = "FACE RECOGNIZED: " + name
                            recognized_name = name
                            unlocked = True
                        else:
                            message = "Face not recognized"
            cv2.putText(frame, message, (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0) if unlocked else (0, 0, 255), 2)
            cv2.imshow("Face Unlock - Press Q to stop", frame)
            if unlocked:
                speak("Welcome " + recognized_name + ". Access granted.")
                break
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
        camera.release()
        cv2.destroyAllWindows()
        landmarker.close()
        if not unlocked:
            speak("No registered user was recognized.")
    except Exception as e:
        speak("Face unlock failed.")
        print("Face unlock error:", e)
        cv2.destroyAllWindows()
    face_unlock_running = False

def get_face_landmarker():
    if not download_model(face_model_url, face_model_path):
        return None

    try:
        base_options = python.BaseOptions(model_asset_path=face_model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_faces=1,
            min_face_detection_confidence=0.5,
            min_face_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        return vision.FaceLandmarker.create_from_options(options)
    except Exception as e:
        speak("I could not start the face detector.")
        print("Face landmarker error:", e)
        return None

def get_hand_landmarker():
    if not download_model(hand_model_url, hand_model_path):
        return None

    try:
        base_options = python.BaseOptions(model_asset_path=hand_model_path)
        options = vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_hands=1,
            min_hand_detection_confidence=0.5,
            min_hand_presence_confidence=0.5,
            min_tracking_confidence=0.5
        )
        return vision.HandLandmarker.create_from_options(options)
    except Exception as e:
        speak("I could not start the hand detector.")
        print("Hand landmarker error:", e)
        return None

def get_face_crop(frame, landmarks):
    height, width = frame.shape[:2]
    points = []

    for landmark in landmarks:
        x = int(landmark.x * width)
        y = int(landmark.y * height)
        points.append((x, y))

    if not points:
        return None

    x_values = [point[0] for point in points]
    y_values = [point[1] for point in points]

    x1 = max(min(x_values) - 30, 0)
    y1 = max(min(y_values) - 40, 0)
    x2 = min(max(x_values) + 30, width)
    y2 = min(max(y_values) + 40, height)

    if x2 <= x1 or y2 <= y1:
        return None

    face = frame[y1:y2, x1:x2]

    if face.size == 0:
        return None

    return face

def eye_detector():
    global eye_detector_running

    if eye_detector_running:
        speak("Eye detector is already running.")
        return

    eye_detector_running = True

    try:
        speak("Eye detector started. Look at the camera.")

        landmarker = get_face_landmarker()

        if landmarker is None:
            eye_detector_running = False
            return

        camera = cv2.VideoCapture(0)

        if not camera.isOpened():
            speak("I could not open the camera.")
            landmarker.close()
            eye_detector_running = False
            return

        while eye_detector_running:
            success, frame = camera.read()

            if not success:
                continue

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            result = landmarker.detect(mp_image)

            if result.face_landmarks:
                landmarks = result.face_landmarks[0]
                height, width = frame.shape[:2]

                eye_indices = [33, 133, 159, 145, 362, 263, 386, 374]

                for index in eye_indices:
                    if index < len(landmarks):
                        x = int(landmarks[index].x * width)
                        y = int(landmarks[index].y * height)
                        cv2.circle(frame, (x, y), 5, (0, 255, 0), -1)

                cv2.putText(
                    frame,
                    "Eyes detected",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2
                )

            cv2.imshow("Eye Detector - Press Q to stop", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        camera.release()
        cv2.destroyAllWindows()
        landmarker.close()
        speak("Eye detector stopped.")

    except Exception as e:
        speak("Eye detector failed.")
        print("Eye detector error:", e)
        cv2.destroyAllWindows()

    eye_detector_running = False

def stop_eye_detector():
    global eye_detector_running
    eye_detector_running = False

# ============================================================
# GESTURE VOLUME CONTROL
# ============================================================

def get_volume_controller():
    """Return the Windows master-volume controller."""
    try:
        devices = AudioUtilities.GetSpeakers()

        # Newer pycaw versions expose EndpointVolume directly.
        try:
            return devices.EndpointVolume
        except AttributeError:
            # Compatibility with older pycaw versions.
            interface = devices.Activate(
                IAudioEndpointVolume._iid_,
                CLSCTX_ALL,
                None
            )
            return cast(interface, POINTER(IAudioEndpointVolume))

    except Exception as e:
        print("Could not connect to Windows volume:", e)
        return None


def set_system_volume(volume_percent):
    """Set Windows master volume from 0 to 100 percent."""
    try:
        volume_percent = max(0.0, min(100.0, float(volume_percent)))
        volume_controller = get_volume_controller()

        if volume_controller is not None:
            volume_controller.SetMasterVolumeLevelScalar(
                volume_percent / 100.0,
                None
            )
            return True

    except Exception as e:
        print("Volume error:", e)

    return False


def gesture_volume():
    """Control Windows volume continuously with thumb-index distance."""
    global gesture_volume_running

    if gesture_volume_running:
        speak("Gesture volume is already running.")
        return

    # Both modes need the camera, so avoid opening camera twice.
    if finger_mouse_running:
        speak("Please stop finger mouse before starting gesture volume.")
        return

    gesture_volume_running = True
    camera = cv2.VideoCapture(0)
    landmarker = None

    if not camera.isOpened():
        speak("I could not open the camera.")
        gesture_volume_running = False
        return

    try:
        landmarker = get_hand_landmarker()

        if landmarker is None:
            gesture_volume_running = False
            return

        speak("Gesture volume started. Move your thumb and index finger apart to increase volume.")

        # Tune these two values for your camera/hand position if needed.
        MIN_DISTANCE = 0.035   # Fingers very close -> 0%
        MAX_DISTANCE = 0.25    # Fingers far apart -> 100%

        # Distance smoothing. Larger = smoother, but slower response.
        SMOOTHING = 0.20

        # Ignore tiny volume changes caused by hand jitter.
        DEAD_ZONE = 2.0        # percent

        # Limit how often Windows receives a volume update.
        UPDATE_INTERVAL = 0.05

        smoothed_distance = None
        last_volume = None
        last_update_time = 0.0

        while gesture_volume_running:
            success, frame = camera.read()

            if not success:
                continue

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(
                image_format=mp.ImageFormat.SRGB,
                data=rgb_frame
            )
            result = landmarker.detect(mp_image)

            if result.hand_landmarks:
                landmarks = result.hand_landmarks[0]

                # MediaPipe hand landmarks:
                # 4 = thumb tip, 8 = index finger tip
                thumb_tip = landmarks[4]
                index_tip = landmarks[8]

                # Distance in normalized MediaPipe coordinates.
                distance = (
                    (index_tip.x - thumb_tip.x) ** 2
                    + (index_tip.y - thumb_tip.y) ** 2
                ) ** 0.5

                # Smooth the distance to reduce jitter.
                if smoothed_distance is None:
                    smoothed_distance = distance
                else:
                    smoothed_distance = (
                        smoothed_distance * (1.0 - SMOOTHING)
                        + distance * SMOOTHING
                    )

                # Map distance continuously to 0-100% volume.
                normalized = (
                    (smoothed_distance - MIN_DISTANCE)
                    / (MAX_DISTANCE - MIN_DISTANCE)
                )
                normalized = max(0.0, min(1.0, normalized))
                target_volume = normalized * 100.0

                current_time = time.time()

                if last_volume is None:
                    last_volume = target_volume
                    set_system_volume(target_volume)
                    last_update_time = current_time

                elif (
                    abs(target_volume - last_volume) >= DEAD_ZONE
                    and current_time - last_update_time >= UPDATE_INTERVAL
                ):
                    if set_system_volume(target_volume):
                        last_volume = target_volume
                        last_update_time = current_time

                # Draw thumb/index points and their connecting line.
                height, width = frame.shape[:2]
                thumb_x = int(thumb_tip.x * width)
                thumb_y = int(thumb_tip.y * height)
                index_x = int(index_tip.x * width)
                index_y = int(index_tip.y * height)

                cv2.line(
                    frame,
                    (thumb_x, thumb_y),
                    (index_x, index_y),
                    (255, 255, 255),
                    3
                )
                cv2.circle(frame, (thumb_x, thumb_y), 10, (255, 255, 255), -1)
                cv2.circle(frame, (index_x, index_y), 10, (255, 255, 255), -1)

                display_volume = int(round(target_volume))

                cv2.putText(
                    frame,
                    f"Volume: {display_volume}%",
                    (20, 45),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    (255, 255, 255),
                    3
                )

                cv2.putText(
                    frame,
                    "Move fingers apart = UP | together = DOWN",
                    (20, 80),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.65,
                    (255, 255, 255),
                    2
                )

            else:
                cv2.putText(
                    frame,
                    "Show one hand to control volume",
                    (20, 45),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (255, 255, 255),
                    2
                )

            cv2.imshow("Gesture Volume - Press Q to stop", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except Exception as e:
        print("Gesture volume error:", e)
        speak("Gesture volume failed.")

    finally:
        gesture_volume_running = False

        if camera is not None:
            camera.release()

        try:
            cv2.destroyWindow("Gesture Volume - Press Q to stop")
        except Exception:
            cv2.destroyAllWindows()

        if landmarker is not None:
            try:
                landmarker.close()
            except Exception:
                pass

        speak("Gesture volume stopped.")


def stop_gesture_volume():
    global gesture_volume_running
    gesture_volume_running = False

    try:
        cv2.destroyWindow("Gesture Volume - Press Q to stop")
    except Exception:
        pass


def finger_mouse():
    global finger_mouse_running

    if finger_mouse_running:
        speak("Finger mouse is already running.")
        return

    finger_mouse_running = True

    try:
        speak("Finger mouse started. Move your index finger to control the mouse.")

        landmarker = get_hand_landmarker()

        if landmarker is None:
            finger_mouse_running = False
            return

        camera = cv2.VideoCapture(0)

        if not camera.isOpened():
            speak("I could not open the camera.")
            landmarker.close()
            finger_mouse_running = False
            return

        screen_width, screen_height = pyautogui.size()
        previous_x = screen_width // 2
        previous_y = screen_height // 2
        clicking = False

        while finger_mouse_running:
            success, frame = camera.read()

            if not success:
                continue

            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            result = landmarker.detect(mp_image)

            if result.hand_landmarks:
                landmarks = result.hand_landmarks[0]

                index_tip = landmarks[8]
                thumb_tip = landmarks[4]

                x = int(index_tip.x * screen_width)
                y = int(index_tip.y * screen_height)

                x = max(0, min(screen_width - 1, x))
                y = max(0, min(screen_height - 1, y))

                smooth_x = int(previous_x * 0.65 + x * 0.35)
                smooth_y = int(previous_y * 0.65 + y * 0.35)

                pyautogui.moveTo(smooth_x, smooth_y, duration=0.01)

                previous_x = smooth_x
                previous_y = smooth_y

                distance = ((index_tip.x - thumb_tip.x) ** 2 + (index_tip.y - thumb_tip.y) ** 2) ** 0.5

                if distance < 0.05 and not clicking:
                    pyautogui.click()
                    clicking = True

                if distance >= 0.07:
                    clicking = False

                height, width = frame.shape[:2]
                ix = int(index_tip.x * width)
                iy = int(index_tip.y * height)

                cv2.circle(frame, (ix, iy), 10, (0, 255, 0), -1)
                cv2.putText(
                    frame,
                    "Finger Mouse",
                    (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0, 255, 0),
                    2
                )

            cv2.imshow("Finger Mouse - Press Q to stop", frame)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

        camera.release()
        cv2.destroyAllWindows()
        landmarker.close()
        speak("Finger mouse stopped.")

    except Exception as e:
        speak("Finger mouse failed.")
        print("Finger mouse error:", e)
        cv2.destroyAllWindows()

    finger_mouse_running = False

def stop_finger_mouse():
    global finger_mouse_running
    finger_mouse_running = False

def show_help():
    help_text = """
You can say:

Open YouTube
Open YT
Open Google
Open Chrome
Open Gmail
Open WhatsApp
Open Meet
Open Telegram
Open Calculator
Open Notepad
Open Paint
Open File Explorer

What is the time
What is today's date

Download Python
Download PyCharm
Show news

Mute volume
Take screenshot

Wikipedia Python
Wikipedia computer
Wikipedia technology

Type a message
Keyboard control
Computer control
Type hello
Click
Double click
Right click
Scroll up
Scroll down
Press Enter
Copy
Paste
Select all
Save
Stop computer control

Start finger mouse
Stop finger mouse
Start gesture volume
Stop gesture volume
Start eye detector
Stop eye detector
Register my face
Face unlock
MySQL multi-user face database with MediaPipe recognition

Help

Or ask me anything normally.

Say stop listening to stop continuous mode.
Say exit to close Copilot.
"""

    messagebox.showinfo("Computer Copilot Help", help_text)
    speak("I have shown the available commands")

def process_command(query):
    if query == "none":
        return True

    if "stop listening" in query or "stop listening mode" in query or "stop conversation" in query:
        stop_listening()
        speak("Continuous listening stopped")
        return True

    if "stop gesture volume" in query:
        stop_gesture_volume()
        speak("Gesture volume stopped.")

    elif "start gesture volume" in query or "gesture volume" in query:
        if finger_mouse_running:
            speak("Please stop finger mouse first.")
        elif not gesture_volume_running:
            threading.Thread(target=gesture_volume, daemon=True).start()

    elif "stop finger mouse" in query:
        stop_finger_mouse()

    elif "start finger mouse" in query or "finger mouse" in query:
        threading.Thread(target=finger_mouse, daemon=True).start()

    elif "stop eye detector" in query:
        stop_eye_detector()

    elif "start eye detector" in query or "eye detector" in query:
        threading.Thread(target=eye_detector, daemon=True).start()

    elif "register my face" in query or "register face" in query:
        start_register_face()

    elif "face unlock" in query or "unlock with face" in query:
        threading.Thread(target=face_unlock, daemon=True).start()

    elif "computer control" in query or "control mode" in query:
        computer_control()

    elif "keyboard control" in query or "voice keyboard" in query:
        keyboard_control()

    elif "open youtube" in query or "open yt" in query:
        open_youtube()

    elif "open google" in query:
        open_google()

    elif "open gmail" in query or "open email" in query:
        open_gmail()

    elif "open whatsapp" in query or "open whats app" in query:
        open_whatsapp()

    elif "open meet" in query or "open google meet" in query:
        open_meet()

    elif "open telegram" in query:
        open_telegram()

    elif "open chrome" in query:
        open_chrome()

    elif "calculator" in query or "open calculator" in query:
        open_calculator()

    elif "notepad" in query or "open notepad" in query:
        open_notepad()

    elif "paint" in query or "open paint" in query:
        open_paint()

    elif "file explorer" in query or "open explorer" in query:
        open_file_explorer()

    elif "the time" in query or "current time" in query or "what time" in query:
        show_time()

    elif "today's date" in query or "current date" in query or "what is the date" in query:
        show_date()

    elif "download python" in query:
        download_python()

    elif "download pycharm" in query:
        download_pycharm()

    elif "pycharm" in query:
        download_pycharm()

    elif "news" in query or "show news" in query:
        show_news()

    elif "volume" in query or "mute" in query:
        mute_volume()

    elif "screenshot" in query or "screen shot" in query or "take screen" in query:
        take_screenshot()

    elif "wikipedia" in query:
        wikipedia_search(query)

    elif "type a message" in query or "type message" in query:
        type_message()

    elif "help" in query or "what can you do" in query:
        show_help()

    elif "exit" in query or "close copilot" in query or "quit" in query or "bye" in query:
        stop_listening()
        speak("Exiting Computer Copilot")
        m.destroy()
        return False

    else:
        ask_ai(query)

    return True

def continuous_listening():
    global listening

    while listening:
        query = listen_command()

        if not listening:
            break

        if query == "none":
            continue

        if not process_command(query):
            break

def start_listening():
    global listening

    if listening:
        speak("I am already listening")
        return

    listening = True

    listen_button.config(text="🎤 Listening...")
    stop_button.config(state="normal")
    status_text.set("Continuous listening started")

    threading.Thread(target=continuous_listening, daemon=True).start()

def stop_listening():
    global listening, computer_control_running
    listening = False
    computer_control_running = False
    stop_gesture_volume()

    try:
        listen_button.config(text="🎤 Start Listening")
        stop_button.config(state="disabled")
    except:
        pass

def start_copilot():
    welcome_frame.pack_forget()
    copilot_frame.pack(fill="both", expand=True)
    speak("Computer Copilot started")
    greet_user()

def close_copilot():
    stop_listening()
    stop_finger_mouse()
    stop_gesture_volume()
    stop_eye_detector()
    speak("Goodbye")
    m.destroy()

# ---------------- THEME MODE ----------------
current_theme = "Dark"

THEMES = {
    "Dark": {
        "bg": "#111827", "fg": "#F9FAFB", "button_bg": "#1F2937",
        "button_fg": "#F9FAFB", "entry_bg": "#374151"
    },
    "Light": {
        "bg": "#F3F4F6", "fg": "#111827", "button_bg": "#FFFFFF",
        "button_fg": "#111827", "entry_bg": "#FFFFFF"
    },
    "Cyber Blue": {
        "bg": "#071A2B", "fg": "#67E8F9", "button_bg": "#0B3553",
        "button_fg": "#67E8F9", "entry_bg": "#123B5A"
    },
    "Neon Purple": {
        "bg": "#1A0B2E", "fg": "#E9D5FF", "button_bg": "#3B1764",
        "button_fg": "#F3E8FF", "entry_bg": "#4C1D70"
    }
}

def apply_theme(widget, theme):
    """Apply the selected theme recursively to the Copilot UI."""
    colors = THEMES[theme]
    try:
        if isinstance(widget, (tk.Tk, tk.Toplevel, tk.Frame, tk.LabelFrame)):
            widget.configure(bg=colors["bg"])
        elif isinstance(widget, tk.Label):
            widget.configure(bg=colors["bg"], fg=colors["fg"])
        elif isinstance(widget, tk.Button):
            widget.configure(
                bg=colors["button_bg"], fg=colors["button_fg"],
                activebackground=colors["entry_bg"],
                activeforeground=colors["fg"],
                relief="flat"
            )
        elif isinstance(widget, tk.Entry):
            widget.configure(
                bg=colors["entry_bg"], fg=colors["fg"],
                insertbackground=colors["fg"]
            )
        elif isinstance(widget, tk.Text):
            widget.configure(
                bg=colors["entry_bg"], fg=colors["fg"],
                insertbackground=colors["fg"]
            )
    except tk.TclError:
        pass

    for child in widget.winfo_children():
        apply_theme(child, theme)


def set_theme(theme):
    global current_theme
    if theme not in THEMES:
        return
    current_theme = theme
    apply_theme(m, theme)
    try:
        theme_button.config(text=f"🎨 Theme: {theme}")
    except tk.TclError:
        pass


def choose_theme():
    chooser = tk.Toplevel(m)
    chooser.title("Choose Theme")
    chooser.geometry("300x330")
    chooser.resizable(False, False)
    chooser.transient(m)

    colors = THEMES[current_theme]
    chooser.configure(bg=colors["bg"])

    tk.Label(
        chooser, text="🎨 Choose Your Theme",
        font=("Arial", 16, "bold"), bg=colors["bg"], fg=colors["fg"]
    ).pack(pady=18)

    for theme in THEMES:
        tk.Button(
            chooser,
            text=theme,
            font=("Arial", 12),
            width=20,
            bg=colors["button_bg"],
            fg=colors["button_fg"],
            activebackground=colors["entry_bg"],
            activeforeground=colors["fg"],
            relief="flat",
            command=lambda t=theme: (set_theme(t), chooser.destroy())
        ).pack(pady=6)

    chooser.grab_set()

welcome_frame = tk.Frame(m)
welcome_frame.pack(fill="both", expand=True)

welcome_title = tk.Label(
    welcome_frame,
    text="Welcome to Computer Copilot",
    font=("Arial", 24, "bold")
)
welcome_title.pack(pady=70)

welcome_text = tk.Label(
    welcome_frame,
    text="Your AI voice-controlled computer assistant",
    font=("Arial", 13)
)
welcome_text.pack(pady=10)

start_button = tk.Button(
    welcome_frame,
    text="Start Copilot",
    font=("Arial", 14),
    width=20,
    command=start_copilot
)
start_button.pack(pady=30)

copilot_frame = tk.Frame(m)

title_label = tk.Label(
    copilot_frame,
    text="Computer Copilot",
    font=("Arial", 22, "bold")
)
title_label.pack(pady=15)

assistant_label = tk.Label(
    copilot_frame,
    textvariable=assistant_text,
    font=("Arial", 16, "bold"),
    wraplength=620,
    justify="left",
    anchor="w"
)
assistant_label.pack(fill="x", padx=35, pady=(5, 8))

status_label = tk.Label(
    copilot_frame,
    textvariable=status_text,
    font=("Arial", 11),
    wraplength=600
)
status_label.pack(pady=(0, 10))

listen_button = tk.Button(
    copilot_frame,
    text="🎤 Start Listening",
    font=("Arial", 14),
    width=20,
    command=start_listening
)
listen_button.pack(pady=6)

stop_button = tk.Button(
    copilot_frame,
    text="⏹ Stop Listening",
    font=("Arial", 12),
    width=20,
    command=stop_listening,
    state="disabled"
)
stop_button.pack(pady=6)

speaking_button = tk.Button(
    copilot_frame,
    text="🔊 Speaking Mode: ON",
    font=("Arial", 12),
    width=20,
    command=toggle_speaking_mode
)
speaking_button.pack(pady=6)

computer_control_button = tk.Button(
    copilot_frame,
    text="🖱 Computer Control",
    font=("Arial", 12),
    width=20,
    command=computer_control
)
computer_control_button.pack(pady=6)

finger_button = tk.Button(
    copilot_frame,
    text="🖐 Finger Mouse",
    font=("Arial", 12),
    width=20,
    command=lambda: threading.Thread(target=finger_mouse, daemon=True).start()
)
finger_button.pack(pady=6)

gesture_volume_button = tk.Button(
    copilot_frame,
    text="🔊 Gesture Volume",
    font=("Arial", 12),
    width=20,
    command=lambda: threading.Thread(target=gesture_volume, daemon=True).start()
)
gesture_volume_button.pack(pady=6)

theme_button = tk.Button(
    copilot_frame,
    text="🎨 Theme: Dark",
    font=("Arial", 12),
    width=20,
    command=choose_theme
)
theme_button.pack(pady=6)

eye_button = tk.Button(
    copilot_frame,
    text="👁 Eye Detector",
    font=("Arial", 12),
    width=20,
    command=lambda: threading.Thread(target=eye_detector, daemon=True).start()
)
eye_button.pack(pady=6)

register_button = tk.Button(
    copilot_frame,
    text="🙂 Register Face",
    font=("Arial", 12),
    width=20,
    command=lambda: start_register_face()
)
register_button.pack(pady=6)

unlock_button = tk.Button(
    copilot_frame,
    text="🔐 Face Unlock",
    font=("Arial", 12),
    width=20,
    command=lambda: threading.Thread(target=face_unlock, daemon=True).start()
)
unlock_button.pack(pady=6)

help_button = tk.Button(
    copilot_frame,
    text="Help",
    font=("Arial", 12),
    width=20,
    command=show_help
)
help_button.pack(pady=6)

exit_button = tk.Button(
    copilot_frame,
    text="Exit",
    font=("Arial", 12),
    width=20,
    command=close_copilot
)
exit_button.pack(pady=6)

m.protocol("WM_DELETE_WINDOW", close_copilot)

set_theme(current_theme)

m.mainloop()
