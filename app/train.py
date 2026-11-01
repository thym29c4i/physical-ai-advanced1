import json
from pathlib import Path
from intent import fit, predict

ROOT = Path(__file__).resolve().parents[1]


def train(root=ROOT):
    rows = json.loads((root/'data/commands.json').read_text())
    model = fit(rows['train'])
    (root/'models').mkdir(exist_ok=True)
    (root/'models/intent.json').write_text(json.dumps(model, ensure_ascii=False))
    results = [dict(row, prediction=predict(model, row['text'])) for row in rows['test']]
    correct = sum(row['label'] == row['prediction']['label'] for row in results)
    report = {'correct': correct, 'total': len(results), 'examples': results,
              'note': 'Small manually authored holdout set; not evidence of general Japanese understanding.'}
    (root/'results').mkdir(exist_ok=True)
    (root/'results/intent_evaluation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2))
    print(f'Intent evaluation: {correct}/{len(results)} (including rejection cases)')
    return report


if __name__ == '__main__':
    train()
