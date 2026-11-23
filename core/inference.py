"""Inference-only functions derived from the E3-R66 training engine."""
import random
import numpy as np
import pandas as pd
G={'radio':['rssi','snr'],'temporal':['delta_t_derived'],'phy':['c2','c8','c9','c15'],'protocol':['counter_step_derived']}
F=sum(G.values(),[])
CAL={}
PERM_MAP={}

def discretize(d):
    d = d.copy()
    for f in F:
        d['b_' + f] = np.searchsorted(qs[f], d[f].fillna(med[f]).to_numpy(), side='right').astype('int8')
    return d

def episodes(d):
    out = []
    for eid, g in d.groupby('episode_id', sort=True):
        g = g.sort_values('t')
        out.append({'id': eid, 'scenario': g.scenario.iloc[0], 'onset': int(g.onset.iloc[0]), 'n': len(g), 'b': {f: g['b_' + f].to_numpy() for f in F}})
    return out

def calibrated_bucket(v, n):
    c, s = CAL[n]
    return int(np.digitize(np.clip((v - c) / s, -8, 8), [-0.75, 0, 0.75]))

def local_state(e, t, name):
    cols = G[name]
    cur = tuple((int(e['b'][f][t]) for f in cols))
    prev = tuple((int(np.sign(int(e['b'][f][t]) - int(e['b'][f][max(0, t - 3)]))) for f in cols))
    return (min(3, t // 6),) + cur + prev

def reward(e, t, a):
    attack = e['scenario'] != 'normal'
    on = e['onset']
    if a == 1:
        return 18 - 0.35 * max(0, t - on) if attack and t >= on else -32
    if t == e['n'] - 1:
        return 9 if not attack else -24
    return -0.08

def advantage(e, t, name, q):
    s = local_state(e, t, name)
    return q.get((s, 1), 0) - q.get((s, 0), 0)

def coord_state(e, t, ins, mode, localq, ablate=None):
    base = (min(3, t // 6), int(ins), int(e['b']['rssi'][t]), int(e['b']['delta_t_derived'][t]))
    if not ins:
        return base
    if mode == 'central':
        return base + tuple((int(e['b'][f][t]) for f in F))
    return base + tuple((calibrated_bucket(advantage(PERM_MAP.get(e['id'], e) if mode == 'permuted' else e, t, n, localq[n]), n) for n in G if n != ablate))

def acts(t, ins):
    return (0, 1, 2) if t >= 5 and (not ins) else (0, 2) if t >= 5 else (0, 1) if not ins else (0,)

def coord_roll(e, q, mode, localq, rng, epsilon=0, learn=False, ablate=None):
    t = 0
    ins = False
    total = 0
    count = 0
    tds = []
    for _ in range(e['n'] * 2 + 1):
        s = coord_state(e, t, ins, mode, localq, ablate)
        available = tuple((a for a in acts(t, ins) if a != 1 or count == 0))
        a = rng.choice(available) if rng.random() < epsilon else max(available, key=lambda a: (q.get((s, a), 0), -a))
        if a == 1:
            nt = t
            ni = True
            r = -0.8
            done = False
            count += 1
        elif a == 2:
            nt = t
            ni = ins
            r = reward(e, t, 1)
            done = True
        elif t == e['n'] - 1:
            nt = t
            ni = ins
            r = reward(e, t, 0)
            done = True
        else:
            nt = t + 1
            ni = False
            r = -0.08
            done = False
        total += r
        if learn:
            ns = coord_state(e, nt, ni, mode, localq, ablate) if not done else None
            future = 0 if done else max((q.get((ns, z), 0) for z in acts(nt, ni) if z != 1 or count == 0))
            td = r + GAMMA * future - q.get((s, a), 0)
            q[s, a] = q.get((s, a), 0) + ALPHA * td
            tds.append(abs(td))
        if done:
            return ({'episode_id': e['id'], 'scenario': e['scenario'], 'y': int(e['scenario'] != 'normal'), 'pred': int(a == 2), 't': t, 'onset': e['onset'], 'inspections': count, 'reward': total}, float(np.mean(tds)) if tds else 0)
        t, ins = (nt, ni)
    raise RuntimeError('Episode exceeded finite horizon')

def evaluate(es, q, mode, localq, ablate=None):
    rng = random.Random(0)
    return pd.DataFrame([coord_roll(e, q, mode, localq, rng, ablate=ablate)[0] for e in es])
