"""Small desktop control panel shown alongside Gazebo (also captured in video)."""
import json
from pathlib import Path
import tkinter as tk
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

ROOT = Path(__file__).resolve().parents[1]
rclpy.init()
node = Node('delivery_panel')
pub = node.create_publisher(String, '/instruction', 10)
window = tk.Tk()
window.title('Delivery control')
window.geometry('1280x250+0+550')
window.overrideredirect(True)
window.attributes('-topmost', True)
window.configure(bg='#142131')
font = 'Noto Sans CJK JP'
instruction = tk.StringVar(value='管制室まで物資を届けて')
status = tk.StringVar(value='準備中：位置情報の受信を待っています')
detail = tk.StringVar(value='行き先：緑＝管制室　青＝資材庫　橙＝研究ラボ')
tk.Label(window, text='LUNA CARGO｜月面基地の配送ロボット', font=(font, 18, 'bold'), fg='white', bg='#142131').pack(anchor='w', padx=22, pady=(10, 0))
row = tk.Frame(window, bg='#142131')
row.pack(fill='x', padx=22, pady=8)
entry = tk.Entry(row, textvariable=instruction, font=(font, 13), width=33)
entry.pack(side='left')


def send(text=None):
    text = text if text is not None else instruction.get()
    instruction.set(text)
    pub.publish(String(data=text))


tk.Button(row, text='指示を送る', command=send, font=(font, 11)).pack(side='left', padx=8)
for title, text in [('管制室へ', '管制室まで物資を届けて'), ('資材庫へ', '資材庫へ向かってください'), ('研究ラボへ', '研究ラボへ配送をお願いします'), ('帰還', '充電ドックに戻って'), ('不明指示', '天気を教えて'), ('停止', '停止')]:
    tk.Button(row, text=title, command=lambda t=text: send(t), font=(font, 10)).pack(side='left', padx=3)
tk.Label(window, textvariable=status, font=(font, 16, 'bold'), fg='#78dfbc', bg='#142131').pack(anchor='w', padx=22)
tk.Label(window, textvariable=detail, font=(font, 12), fg='#d5e1ef', bg='#142131').pack(anchor='w', padx=22, pady=4)
tk.Label(window, text='緑＝管制室　｜　青＝資材庫　｜　橙＝研究ラボ　　白＝充電ドック　｜　重力1.62m/s²（簡易月面環境）', font=(font, 11), fg='#a4b6cb', bg='#142131').pack(anchor='w', padx=22)
names = {'reception': '管制室', 'warehouse': '資材庫', 'workshop': '研究ラボ', 'home': '充電ドック', 'unknown': '判定できません'}
offset = 0


def update():
    global offset
    path = ROOT/'results/events.jsonl'
    if path.exists():
        with path.open() as stream:
            stream.seek(offset)
            for line in stream:
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                state = event['state']
                if state == 'READY':
                    status.set('待機中：行き先を指定してください')
                    instruction.set('管制室まで物資を届けて')
                    detail.set('指示の行き先をAIが判定し、ロボットが自動で移動します')
                elif state == 'INTERPRETED':
                    instruction.set(event['instruction'])
                    detail.set(f"AIの判定：{names[event['label']]}　類似度：{event['similarity']:.3f}（正解確率ではありません）")
                elif state == 'MOVING':
                    status.set(f"走行中 → {names[event['goal']]}")
                elif state == 'ARRIVED':
                    status.set(f"到着：{names[event['goal']]}で停止しました")
                elif state == 'REJECTED':
                    status.set('指示を確認できないため、走行しません')
                elif state == 'ABORTED':
                    status.set('走行を中断しました。位置情報とシミュレーションを確認してください')
                elif state == 'STOPPED':
                    status.set('停止しました')
            offset = stream.tell()
    rclpy.spin_once(node, timeout_sec=0)
    window.after(150, update)


window.bind('<Return>', lambda _: send())
window.after(150, update)
window.mainloop()
node.destroy_node()
rclpy.shutdown()
