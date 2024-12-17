#連続的動作不可
#初期ver

import openai
import serial
import serial.tools.list_ports
from pymycobot.mycobot import MyCobot

# OpenAI APIキーを設定
openai.api_key = "API_KEY"

# setup()関数の定義
def setup():
    print("\n=== Setup MyCobot Connection ===")

    plist = list(serial.tools.list_ports.comports())
    if not plist:
        print("No available serial ports found!")
        return None

    idx = 1
    for port in plist:
        print(f"{idx} : {port}")
        idx += 1

    _in = input(f"\nPlease input 1 - {idx - 1} to choose a port: ")
    port = str(plist[int(_in) - 1]).split(" - ")[0].strip()
    print(f"Selected port: {port}\n")

    baud = 115200
    _baud = input("Please input baud rate (default: 115200): ")
    try:
        baud = int(_baud) if _baud else baud
    except ValueError:
        print("Invalid baud rate. Using default: 115200")
    print(f"Selected baud rate: {baud}\n")

    DEBUG = False
    f = input("Enable DEBUG mode? [Y/n]: ")
    if f.lower() in ["y", "yes", ""]:
        DEBUG = True

    mc = MyCobot(port, baud, debug=DEBUG)
    print("\n=== Setup Complete ===")
    return mc

# ChatGPT APIで角度を取得する関数
def get_angles_from_chatgpt(command):
    prompt = (
        "You are an assistant for controlling a MyCobot robotic arm.  \n"
        "Each motor has specific characteristics as follows:  \n"
        "Joint 0: Base motor (yaw axis)  \n"
        "Joint 1: Motor above the base (pitch axis)  \n"
        "Joint 2: Above Joint 1 (pitch axis)  \n"
        "Joint 3: Above Joint 2 (pitch axis)  \n"
        "Joint 4: Above Joint 3 (yaw axis)  \n"
        "Joint 5: Topmost motor (roll axis).  \n\n"
        "Translate the user's command into angles for all 6 joints.  \n"
        "Example commands:  \n"
        "1. \"Move the topmost motor 90 degrees clockwise.\" → `0, 0, 0, 0, 0, 90`  \n"
        "2. \"Rotate the base motor 45 degrees and tilt Joint 2 by 30 degrees.\" → `45, 0, 30, 0, 0, 0`  \n"
        "3. \"Slightly move all motors.\" → `10, 20, 30, 40, 50, 60`.  \n\n"
        "Respond with **only 6 comma-separated numbers** and no additional text.\n\n"
        f"Command: {command}"
    )

    response = openai.ChatCompletion.create(
        model="gpt-4",  # モデルを指定
        messages=[{"role": "system", "content": prompt}]
    )
    return response["choices"][0]["message"]["content"].strip()


# メイン部分
if __name__ == "__main__":
    mc = setup()
    if mc:
        while True:
            try:
                user_command = input("Enter your command to control MyCobot:\n>> ")
                if user_command.lower() in ["exit", "終了"]:
                    print("Exiting program. Goodbye!")
                    break

                # ChatGPTに指示を送信
                angles_text = get_angles_from_chatgpt(user_command)
                print(f"ChatGPT response: {angles_text}")  # デバッグ用出力

                # 応答をパースしてMyCobotに送信
                try:
                    angles = list(map(float, angles_text.split(',')))
                    if len(angles) != 6:
                        raise ValueError("Incorrect number of angles")
                    print(f"Moving MyCobot with angles: {angles}")
                    mc.send_angles(angles, 50)
                    print("MyCobot moved successfully.")
                except ValueError as e:
                    print(f"Invalid response from ChatGPT: {angles_text}. Error: {e}. Please try again.")
            except KeyboardInterrupt:
                print("\nExiting program. Goodbye!")
                break
    else:
        print("Failed to set up MyCobot.")
