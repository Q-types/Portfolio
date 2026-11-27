"""Actual bounded sklearn LDA; descriptive fit diagnostics, no semantic score."""
from .evaluation import select


def compare(data, rubric):
    from sklearn.decomposition import LatentDirichletAllocation
    from sklearn.feature_extraction.text import CountVectorizer
    import numpy as np
    reviews, _ = select(data, rubric)
    ids = sorted(reviews)
    cfg = rubric['topic']
    vectorizer = CountVectorizer(lowercase=True, stop_words='english', max_features=cfg['max_features'])
    x = vectorizer.fit_transform([reviews[rid]['text'] for rid in ids])
    words = vectorizer.get_feature_names_out()
    results = []
    for k in cfg['k']:
        model = LatentDirichletAllocation(n_components=k, random_state=cfg['seed'],
                                         max_iter=cfg['max_iter'], learning_method='batch', n_jobs=1)
        weights = model.fit_transform(x)
        topics = []
        for component in model.components_:
            order = sorted(range(len(words)), key=lambda i: (-component[i], words[i]))[:cfg['top_words']]
            topics.append([{'word': str(words[i]), 'weight': float(component[i])} for i in order])
        results.append({'k': k, 'iterations': model.n_iter_, 'fit_perplexity': float(model.perplexity(x)),
                        'components': model.components_.tolist(), 'top_words': topics,
                        'document_topic_weights': weights.tolist(), 'finite': bool(np.isfinite(weights).all())})
    return {'status': 'executed', 'method': 'sklearn LatentDirichletAllocation',
            'scope': 'in-sample descriptive comparison on invented negative reviews; no held-out or semantic accuracy',
            'review_ids': ids, 'vocabulary': words.tolist(), 'config': cfg, 'comparisons': results,
            'bertopic': 'pending; not loaded', 'emotion': 'pending; no pretrained inference',
            'issue_extraction': 'authored mock; no LLM called', 'selection': 'none; both predeclared k retained'}
