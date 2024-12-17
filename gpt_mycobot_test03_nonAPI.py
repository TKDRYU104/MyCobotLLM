import openai
import serial
import serial.tools.list_ports
from pymycobot.mycobot import MyCobot
import time

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

# ChatGPT APIで連続動きの角度ステップを取得
def get_steps_from_chatgpt(command):
    prompt = (
        "You are an assistant for controlling a MyCobot robotic arm.  \n"
        "Each motor has specific characteristics as follows:  \n"
        "Joint 0: Base motor (yaw axis)  \n"
        "Joint 1: Motor above the base (pitch axis)  \n"
        "Joint 2: Above Joint 1 (pitch axis)  \n"
        "Joint 3: Above Joint 2 (pitch axis)  \n"
        "Joint 4: Above Joint 3 (yaw axis)  \n"
        "Joint 5: Topmost motor (roll axis).  \n\n"
        "Translate the user's command into multiple steps of angles for all 6 joints.  \n"
        "Each step must be represented as a line of exactly 6 comma-separated numbers.  \n\n"
        "Example command:  \n"
        "\"Move the base motor to 30 degrees, then tilt Joint 2 by 45 degrees, and finally rotate the topmost motor to 90 degrees.\"  \n\n"
        "Expected response:  \n"
        "30, 0, 0, 0, 0, 0  \n"
        "30, 0, 45, 0, 0, 0  \n"
        "30, 0, 45, 0, 0, 90  \n\n"
        "Respond with **only the steps as lines of 6 comma-separated numbers**, and do not include any explanations or extra text.\n\n"
        f"Command: {command}"
    )

    response = openai.ChatCompletion.create(
        model="gpt-4",  # gpt-4 または gpt-3.5-turbo
        messages=[{"role": "system", "content": prompt}]
    )
    return response["choices"][0]["message"]["content"].strip()

# MyCobotを連続的に動かすメイン処理
def execute_steps(mc, steps_text):
    steps = steps_text.splitlines()
    for i, step in enumerate(steps):
        try:
            angles = list(map(float, step.split(',')))
            if len(angles) != 6:
                raise ValueError("Incorrect number of angles")
            print(f"Step {i + 1}: Moving MyCobot with angles: {angles}")
            mc.send_angles(angles, 50)  # MyCobotに角度を送信
            time.sleep(1)  # ステップ間の遅延時間
        except Exception as e:
            print(f"Error at Step {i + 1}: {step}. Error: {e}")

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

                # ChatGPTに指示を送信し、複数ステップを取得
                steps_text = get_steps_from_chatgpt(user_command)
                print("Received steps from ChatGPT:")
                print(steps_text)

                # 連続的にMyCobotを動かす
                execute_steps(mc, steps_text)

            except KeyboardInterrupt:
                print("\nExiting program. Goodbye!")
                break
    else:
        print("Failed to set up MyCobot.")
