from flask import Flask, render_template, Response, request, jsonify, url_for
import cv2
import os
import time
import math
import pyttsx3
import mediapipe as mp
import threading


app = Flask(__name__)


# Initialize MediaPipe and other globals
mp_pose = mp.solutions.pose
mp_draw = mp.solutions.drawing_utils
pose = mp_pose.Pose()
last_feedback = ""
last_feedback_time = 0
feedback_delay = 3  
is_streaming = True
# engine = pyttsx3.init()


# Global Functions
def calculate_angle(a, b, c):
    try:
        angle = math.degrees(math.atan2(c[1] - b[1], c[0] - b[0]) - math.atan2(a[1] - b[1], a[0] - b[0]))
        return abs(angle)
    except Exception as e:
        print(f"Error calculating angle: {e}")
        return None

feedback_lock = threading.Lock()

def speak(feedback):
    with feedback_lock:
        engine = pyttsx3.init()  # Initialize the engine here to avoid reusing the same instance
        engine.say(feedback)
        engine.runAndWait()
        engine.stop()

def provide_voice_feedback(feedback):
    global last_feedback, last_feedback_time
    current_time = time.time()

    # Ensure enough time has passed and feedback is different
    if feedback != last_feedback and feedback != "" and current_time - last_feedback_time > feedback_delay:
        print(f"Providing voice feedback: {feedback}")
        threading.Thread(target=speak, args=(feedback,)).start()  
        last_feedback = feedback
        last_feedback_time = current_time  


def squat_detection(result, img):
    feedback = ""
    if result.pose_landmarks:
        mp_draw.draw_landmarks(img, result.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        landmarks = result.pose_landmarks.landmark
        try:
            hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
            knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
            ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
            knee_angle = calculate_angle(hip, knee, ankle)

            if knee_angle is not None:
                if knee_angle < 60:
                    feedback = "Too Low!"
                elif knee_angle > 110:
                    feedback = "Too High!"
                else:
                    feedback = "Correct!"

                # Provide feedback only if it changes
                provide_voice_feedback(feedback)

                # Display the calculated knee angle on the frame
                cv2.putText(img, f"Knee Angle: {int(knee_angle)}", (20, 50), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 0, 255), 1)
        except Exception as e:
            print(f"Error in squat detection: {e}")
    return img

def plank_detection(result, img):
    feedback = ""
    if result.pose_landmarks:
        mp_draw.draw_landmarks(img, result.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        landmarks = result.pose_landmarks.landmark
        try:
            shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
            ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
            shoulder_hip_angle = calculate_angle(shoulder, hip, ankle)

            if shoulder_hip_angle is not None:
                if shoulder_hip_angle < 170:
                    feedback = "Hips too low!"
                elif shoulder_hip_angle > 190:
                    feedback = "Hips too high!"
                else:
                    feedback = "Correct!"

                # Provide feedback only if it changes
                provide_voice_feedback(feedback)

                # Display the calculated shoulder-hip angle on the frame
                cv2.putText(img, f"Shoulder-Hip Angle: {int(shoulder_hip_angle)}", (20, 50), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 0, 255), 1)
        except Exception as e:
            print(f"Error in plank detection: {e}")
    return img


# Pushup Detection
def pushup_detection(result, img):
    feedback = ""
    if result.pose_landmarks:
        mp_draw.draw_landmarks(img, result.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        landmarks = result.pose_landmarks.landmark
        try:
            shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
            wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
            elbow_angle = calculate_angle(shoulder, elbow, wrist)

            if elbow_angle is not None:
                if elbow_angle < 70:
                    feedback = "Too Low!"
                elif elbow_angle > 120:
                    feedback = "Too High!"
                else:
                    feedback = "Correct!"

                # Provide feedback only if it changes
                provide_voice_feedback(feedback)

                # Display the calculated elbow angle on the frame
                cv2.putText(img, f"Elbow Angle: {int(elbow_angle)}", (20, 50), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 0, 255), 1)
        except Exception as e:
            print(f"Error in push-up detection: {e}")
    return img



# Bicep Curl Detection
def bicep_curl_detection(result, img):
    feedback = ""
    if result.pose_landmarks:
        # Draw the landmarks on the frame
        mp_draw.draw_landmarks(img, result.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        landmarks = result.pose_landmarks.landmark
        try:
            # Get coordinates for shoulder, elbow, and wrist
            shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
            wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
            
            # Calculate the elbow angle
            elbow_angle = calculate_angle(shoulder, elbow, wrist)

            if elbow_angle is not None:
            # Define feedback based on the elbow angle
                if elbow_angle > 160:
                    feedback = "Lower the weight! Arm is too extended."
                elif elbow_angle < 30:
                    feedback = "Fully contracted! Arm is fully bent."
                elif 30 <= elbow_angle <= 160:
                    feedback = "Correct Form! Keep it up!"  # Arm is in an appropriate curl position

                # Provide feedback only if it changes
                provide_voice_feedback(feedback)

                # Display the calculated elbow angle on the frame
                cv2.putText(img, f"Elbow Angle: {int(elbow_angle)}", (20, 50), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 0, 255), 1)
        except Exception as e:
            print(f"Error in bicep curl detection: {e}")
    return img

def burpee_detection(result, img):
    feedback = ""
    if result.pose_landmarks:
        mp_draw.draw_landmarks(img, result.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        landmarks = result.pose_landmarks.landmark
        try:
            # Get key landmarks
            shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
            wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
            hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
            knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
            ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]

            # Calculate angles
            elbow_angle = calculate_angle(shoulder, elbow, wrist)
            knee_angle = calculate_angle(hip, knee, ankle)
            hip_angle = calculate_angle(shoulder, hip, knee)

            # Logic for burpee phases
            if hip_angle < 90 and knee_angle < 100:  # Squat phase
                feedback = "In squat position!"
            elif hip_angle > 160 and knee_angle > 160:  # Jump phase
                feedback = "Jump!"
            elif elbow_angle < 70:  # Push-up phase
                feedback = "Too Low in Push-up!"
            elif elbow_angle > 120 and hip_angle < 160:  # Coming up from push-up
                feedback = "Transition to standing"

            # Display feedback
            provide_voice_feedback(feedback)
            cv2.putText(img, feedback, (20, 50), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 255, 0), 2)

        except Exception as e:
            print(f"Error in burpee detection: {e}")
    return img

# Jumping Jack Detection
def jumping_jack_detection(result, img):
    feedback = ""
    if result.pose_landmarks:
        mp_draw.draw_landmarks(img, result.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        landmarks = result.pose_landmarks.landmark
        try:
            left_hand = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
            right_hand = [landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_WRIST.value].y]
            left_foot = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
            right_foot = [landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y]

            # Check positions for Jumping Jacks
            if left_hand[1] < right_hand[1] and left_foot[1] < right_foot[1]:
                feedback = "Great job! Keep going!"
            else:
                feedback = "Try to jump wider!"

            provide_voice_feedback(feedback)
            cv2.putText(img, feedback, (20, 50), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 0, 255), 1)
        except Exception as e:
            print(f"Error in jumping jack detection: {e}")
    return img


# Calf Raise Detection
def calf_raise_detection(result, img):
    feedback = ""
    if result.pose_landmarks:
        mp_draw.draw_landmarks(img, result.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        landmarks = result.pose_landmarks.landmark
        try:
            left_ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
            right_ankle = [landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE.value].y]
            left_heel = [landmarks[mp_pose.PoseLandmark.LEFT_HEEL.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HEEL.value].y]
            right_heel = [landmarks[mp_pose.PoseLandmark.RIGHT_HEEL.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_HEEL.value].y]

            # Checking if the user is on their toes (calf raise)
            if left_heel[1] < left_ankle[1] and right_heel[1] < right_ankle[1]:
                feedback = "Great! Keep raising your heels!"
            else:
                feedback = "Raise your heels higher"

            provide_voice_feedback(feedback)
            cv2.putText(img, feedback, (20, 50), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 0, 255), 1)
        except Exception as e:
            print(f"Error in calf raise detection: {e}")
    return img

# Wall Sit Detection
def wall_sit_detection(result, img):
    feedback = ""
    if result.pose_landmarks:
        mp_draw.draw_landmarks(img, result.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        landmarks = result.pose_landmarks.landmark
        try:
            left_knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
            right_knee = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y]
            left_hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
            right_hip = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
            left_ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]

            # Check if the knees are at a 90-degree angle (ideal for wall sit)
            knee_angle = calculate_angle(left_hip, left_knee, left_ankle)  # Calculate approximate knee angle

            if 80 <= knee_angle <= 100:
                feedback = "Perfect wall sit! Hold the position!"
            else:
                feedback = "Bend your knees to form a 90-degree angle!"

            provide_voice_feedback(feedback)
            cv2.putText(img, f"Knee Angle: {int(knee_angle)}", (20, 50), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 0, 255), 1)
        except Exception as e:
            print(f"Error in wall sit detection: {e}")
    return img

def pullup_detection(result, img):
    feedback = ""
    if result.pose_landmarks:
        mp_draw.draw_landmarks(img, result.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        landmarks = result.pose_landmarks.landmark
        try:
            
            shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
            wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x, landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
            elbow_angle = calculate_angle(shoulder, elbow, wrist)

            
            if elbow_angle is not None:
                if elbow_angle <= 50:
                    feedback = "correct pull-up!"
                elif elbow_angle > 160:
                    feedback = "Extend your arms and prepare to pull up!"  
                elif elbow_angle > 60 and elbow_angle < 130:
                    feedback = "Keep pulling"

                
                provide_voice_feedback(feedback)

                cv2.putText(img, f"Elbow Angle: {int(elbow_angle)}", (20, 50), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 0, 255), 1)

        except Exception as e:
            print(f"Error in pull-up detection: {e}")
    return img


def deadlifts_detection(result, img):
    feedback = ""
    if result.pose_landmarks:
        mp_draw.draw_landmarks(img, result.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        landmarks = result.pose_landmarks.landmark
        try:
            # Get key landmarks
            shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
            knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
            
            # Calculate hip-knee angle
            hip_knee_angle = calculate_angle(shoulder, hip, knee)

            # Deadlift feedback logic
            if hip_knee_angle is not None:
                if hip_knee_angle >= 160:
                    feedback = "Fully stand up, good form!"
                elif 90 <= hip_knee_angle < 160:
                    feedback = "Lower your torso, keep your back straight."
                else:
                    feedback = "You're too low, lift your chest and straighten your back!"

                # Provide feedback only if it changes
                provide_voice_feedback(feedback)

                # Display the calculated hip-knee angle on the frame
                cv2.putText(img, f"Hip-Knee Angle: {int(hip_knee_angle)}", (20, 50), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 0, 255), 1)

        except Exception as e:
            print(f"Error in deadlifts detection: {e}")
    
    return img


def situp_detection(result, img):
    feedback = ""
    if result.pose_landmarks:
        mp_draw.draw_landmarks(img, result.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        landmarks = result.pose_landmarks.landmark
        try:
            
            shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
            knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
            hip_angle = calculate_angle(shoulder, hip, knee)

            shoulder_to_hip_dist = abs(shoulder[1] - hip[1])

            if hip_angle is not None:
                if shoulder_to_hip_dist > 0.3:  
                    if hip_angle < 60:
                        feedback = "Too Low! Curl up more!"
                    elif hip_angle > 90:
                        feedback = "Too High! Lower your torso!"
                    else:
                        feedback = "Great!correct sit-up"

                provide_voice_feedback(feedback)
                cv2.putText(img, f"Hip Angle: {int(hip_angle)}", (20, 50), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 0, 255), 1)

        except Exception as e:
            print(f"Error in sit-up detection: {e}")
    
    return img

def side_plank_detection(result, img):
    feedback = ""
    if result.pose_landmarks:
        mp_draw.draw_landmarks(img, result.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        landmarks = result.pose_landmarks.landmark
        
        try:
            left_shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x, landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            left_hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
            left_ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
            left_elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]

            body_angle = calculate_angle(left_shoulder, left_hip, left_ankle)
            elbow_angle = calculate_angle(left_shoulder, left_elbow, left_hip)

            if 170 <= body_angle <= 180 and 80 <= elbow_angle <= 100:
                feedback = "Perfect side plank! Hold the position."
            else:
                feedback = "Adjust your body. Keep your body straight and elbow under your shoulder."

            provide_voice_feedback(feedback)
            cv2.putText(img, feedback, (20, 50), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 0, 255), 1)

        except Exception as e:
            print(f"Error in side plank detection: {e}")
    
    return img

def lunge_detection(result, img):
    feedback = ""
    if result.pose_landmarks:
        mp_draw.draw_landmarks(img, result.pose_landmarks, mp_pose.POSE_CONNECTIONS)
        landmarks = result.pose_landmarks.landmark
        
        try:
            left_knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
            left_hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x, landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
            left_ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x, landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
            right_knee = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x, landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y]

            front_knee_angle = calculate_angle(left_hip, left_knee, left_ankle)
            back_knee_angle = calculate_angle(left_hip, right_knee, left_ankle) 

            if 80 <= front_knee_angle <= 100 and back_knee_angle > 160:
                feedback = "Good lunge! Keep going!"
            else:
                feedback = "Adjust your form. Front knee should be at 90 degrees."

            provide_voice_feedback(feedback)
            cv2.putText(img, feedback, (20, 50), cv2.FONT_HERSHEY_COMPLEX_SMALL, 1, (0, 0, 255), 1)

        except Exception as e:
            print(f"Error in lunge detection: {e}")
    
    return img

def detect_exercise_from_frame(frame, selected_exercise):
    """Detect exercise based on selected type and frame"""
    result = pose.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    
    if selected_exercise == 'squat':
        return squat_detection(result, frame)
    elif selected_exercise == 'plank':
        return plank_detection(result, frame)
    elif selected_exercise == 'pushup':
        return pushup_detection(result, frame)
    elif selected_exercise == 'bicep':
        return bicep_curl_detection(result, frame)
    elif selected_exercise == 'Burpees':
        return burpee_detection(result, frame)
    elif selected_exercise == 'Pull up':
        return pullup_detection(result, frame)
    elif selected_exercise == 'Wall Sit':
        return wall_sit_detection(result, frame)
    elif selected_exercise == 'Calf Raise':
        return calf_raise_detection(result, frame)
    elif selected_exercise == 'Jumping Jack':
        return jumping_jack_detection(result, frame)
    elif selected_exercise == 'Deadlift':
        return deadlifts_detection(result, frame)
    elif selected_exercise == 'Sit up':
        return situp_detection(result, frame)
    elif selected_exercise == 'side_plank':
        return side_plank_detection(result, frame)
    elif selected_exercise == 'lunge':
        return lunge_detection(result, frame)
    else:
        return frame

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/set_exercise', methods=['POST'])
def set_exercise():
    global is_streaming
    data = request.get_json()
    selected_exercise = data.get('exercise')
    is_streaming = True  # Start streaming when exercise is set
    return jsonify({"status": "exercise_set", "exercise": selected_exercise})

@app.route('/stop_stream', methods=['POST'])
def stop_stream():
    global is_streaming
    is_streaming = False  # Stop the camera stream
    return jsonify({"status": "stopped"})

 
def gen_frames(selected_exercise):
    global is_streaming
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        print("Error: Camera not initialized correctly")
        return
    
    while is_streaming:  # Only run the loop while streaming is True
        success, frame = camera.read()
        if not success:
            print("Error: Failed to read from the camera")
            break
        else:
            # Detect the exercise in the frame
            frame = detect_exercise_from_frame(frame, selected_exercise)
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    camera.release()
    print("Camera feed stopped")


@app.route('/video_feed/<exercise>')
def video_feed(exercise):
    """Route for live camera feed with selected exercise"""
    time.sleep(2)  # Add a small delay to ensure the camera feed stabilizes
    return Response(gen_frames(exercise), mimetype='multipart/x-mixed-replace; boundary=frame')




def allowed_file(filename):
    """Check if the file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'mp4', 'avi', 'mov'}

if __name__ == "__main__":
    app.run(debug=True)
