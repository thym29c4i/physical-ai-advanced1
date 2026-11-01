import json
import math
import time
from pathlib import Path

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from std_msgs.msg import String
from intent import predict
from navigation import GOALS, velocity

ROOT = Path(__file__).resolve().parents[1]


class Delivery(Node):
    def __init__(self):
        super().__init__('ai_delivery')
        self.model = json.loads((ROOT/'models/intent.json').read_text())
        self.pose = None
        self.last_odom = 0
        self.goal = None
        self.started = 0
        self.cmd = self.create_publisher(Twist, '/cmd_vel', 10)
        self.status = self.create_publisher(String, '/status', 10)
        self.create_subscription(Odometry, '/odom', self.odometry, 10)
        self.create_subscription(String, '/instruction', self.instruction, 10)
        self.create_timer(0.05, self.step)
        self.event('READY', note='Waiting for odometry and Japanese instruction')

    def event(self, state, **details):
        entry = dict(state=state, wall_time=time.time(), **details)
        text = json.dumps(entry, ensure_ascii=False)
        print(text, flush=True)
        with (ROOT/'results/events.jsonl').open('a') as out:
            out.write(text+'\n')
        self.status.publish(String(data=text))

    def odometry(self, msg):
        p, q = msg.pose.pose.position, msg.pose.pose.orientation
        yaw = math.atan2(2*(q.w*q.z+q.x*q.y), 1-2*(q.y*q.y+q.z*q.z))
        self.pose = (p.x, p.y, yaw)
        self.last_odom = time.monotonic()

    def stop(self):
        self.goal = None
        self.cmd.publish(Twist())

    def instruction(self, msg):
        # An explicit stop also works when odometry is unavailable.
        if msg.data.strip().lower() in ('停止', '止まれ', 'ストップ', 'stop'):
            self.stop()
            self.event('STOPPED')
            return
        self.stop()
        result = predict(self.model, msg.data)
        self.event('INTERPRETED', instruction=msg.data, **result)
        if result['label'] == 'unknown':
            self.event('REJECTED', note='行き先を一つ、肯定文で指定してください')
        elif self.pose is None or time.monotonic()-self.last_odom > 2:
            self.event('REJECTED', note='Odometry not ready; retry after simulation starts')
        else:
            self.goal = result['label']
            self.started = time.monotonic()
            self.event('MOVING', goal=self.goal, target=GOALS[self.goal])

    def step(self):
        if self.goal is None:
            self.cmd.publish(Twist())
            return
        if time.monotonic()-self.last_odom > 2 or time.monotonic()-self.started > 90:
            self.stop()
            self.event('ABORTED', note='Odometry timeout or travel timeout')
            return
        linear, angular, arrived = velocity(*self.pose, GOALS[self.goal])
        if arrived:
            goal = self.goal
            self.stop()
            self.event('ARRIVED', goal=goal, pose=self.pose)
            return
        msg = Twist()
        msg.linear.x, msg.angular.z = linear, angular
        self.cmd.publish(msg)


def main():
    rclpy.init()
    node = Delivery()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            node.stop()
            node.destroy_node()
            rclpy.shutdown()


if __name__ == '__main__':
    main()
