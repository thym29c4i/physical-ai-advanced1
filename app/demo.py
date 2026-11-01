"""Run an end-to-end demonstration against the live ROS/Gazebo system."""
import json
import time
from pathlib import Path
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from nav_msgs.msg import Odometry

ROOT = Path(__file__).resolve().parents[1]


def main():
    rclpy.init()
    node = Node('delivery_demo')
    pub = node.create_publisher(String, '/instruction', 10)
    statuses, odometry = [], []
    node.create_subscription(String, '/status', lambda msg: statuses.append(json.loads(msg.data)), 10)
    node.create_subscription(Odometry, '/odom', lambda msg: odometry.append(msg.pose.pose.position), 10)
    results = []

    def until(predicate, seconds):
        deadline = time.monotonic()+seconds
        while time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=.1)
            if predicate():
                return True
        return False

    try:
        if not until(lambda: odometry and pub.get_subscription_count() > 0, 60):
            raise RuntimeError('Controller or odometry did not become ready')
        for text, expected in [('管制室まで物資を届けて', 'ARRIVED'),
                               ('資材庫へ向かってください', 'ARRIVED'),
                               ('研究ラボへ配送をお願いします', 'ARRIVED'),
                               ('充電ドックに戻って', 'ARRIVED'),
                               ('天気を教えて', 'REJECTED')]:
            statuses.clear()
            start = time.monotonic()
            pub.publish(String(data=text))
            finished = until(lambda: any(s['state'] in ('ARRIVED', 'REJECTED', 'ABORTED') for s in statuses), 100)
            final = next((s for s in statuses if s['state'] in ('ARRIVED', 'REJECTED', 'ABORTED')), {})
            row = dict(instruction=text, expected=expected, observed=final,
                       seconds=round(time.monotonic()-start, 2),
                       passed=bool(finished and final.get('state') == expected))
            results.append(row)
            print(json.dumps(row, ensure_ascii=False), flush=True)
            if not row['passed']:
                raise RuntimeError('Demonstration did not reach expected state')
            until(lambda: False, 3)
    finally:
        pub.publish(String(data='停止'))
        rclpy.spin_once(node, timeout_sec=.1)
        (ROOT/'results/demo_evaluation.json').write_text(json.dumps(results, ensure_ascii=False, indent=2))
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
