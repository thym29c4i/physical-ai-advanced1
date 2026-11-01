"""Character TF-IDF nearest-centroid classifier; no external dependencies."""
import collections
import math
import unicodedata


def features(text):
    text = ''.join(unicodedata.normalize('NFKC', text).lower().split())
    return collections.Counter(text[i:i+n] for n in (1, 2, 3)
                               for i in range(len(text)-n+1))


def normalize(vector):
    norm = math.sqrt(sum(v*v for v in vector.values())) or 1
    return {k: v/norm for k, v in vector.items()}


def fit(rows):
    docs = [features(row['text']) for row in rows]
    df = collections.Counter(k for doc in docs for k in doc)
    idf = {k: math.log((len(docs)+1)/(v+1))+1 for k, v in df.items()}
    sums = {}
    for row, doc in zip(rows, docs):
        vec = normalize({k: (1+math.log(v))*idf[k] for k, v in doc.items()})
        sums.setdefault(row['label'], collections.Counter()).update(vec)
    return {'version': 1, 'idf': idf,
            'centroids': {label: normalize(vec) for label, vec in sums.items()},
            'threshold': 0.30, 'margin': 0.08}


def predict(model, text):
    counts = features(text)
    vec = normalize({k: (1+math.log(v))*model['idf'][k]
                     for k, v in counts.items() if k in model['idf']})
    scores = sorted(((sum(v*centroid.get(k, 0) for k, v in vec.items()), label)
                     for label, centroid in model['centroids'].items()), reverse=True)
    score, label = scores[0]
    margin = score-scores[1][0]
    # This prototype does not understand negation, multiple destinations, or order.
    # Reject these explicitly rather than interpreting them as positive commands.
    unsupported = any(term in text for term in ('ない', 'ません', 'なく', '以外', '禁止', 'から', '経由', '寄って', 'その後', 'それから'))
    groups = [('管制室', 'コントロールルーム', '司令室'),
              ('資材庫', '物資庫', 'ストックヤード'),
              ('研究ラボ', '実験室', '研究区画'),
              ('充電ドック', '帰還地点', 'ホーム', '基地に戻')]
    multi = sum(any(word in text for word in group) for group in groups) > 1
    accepted = score >= model['threshold'] and margin >= model['margin'] and not unsupported and not multi
    return {'label': label if accepted else 'unknown', 'candidate': label,
            'similarity': round(score, 4), 'margin': round(margin, 4)}
