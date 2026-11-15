"""The decoding grid of the sampling ablation (D111).

    python pipeline/sampling_grid.py --selfcheck
"""
import sys

from runner import run_key

TEMPERATURES = (0.0, 0.3, 0.7, 1.0)
SEEDS = (0, 1, 2)
MODELS = ('qwen3', 'qwen25')


def cells(temperatures=TEMPERATURES, seeds=SEEDS):
    return [(temperature, seed) for temperature in temperatures for seed in seeds]


def stem(tag, temperature, seed):
    return f'test.{tag}.t{temperature:.1f}.s{seed}'


def selfcheck():
    grid = cells()
    assert len(grid) == 12
    # A collision would make the resume check skip a whole cell as already done.
    assert len({run_key('m', 'DIFF', 'p', s, t) for t, s in grid}) == len(grid)
    assert len({stem('qwen3', t, s) for t, s in grid}) == len(grid)
    # The reference cell must address the same runs as the historical T=0 results.
    assert run_key('m', 'DIFF', 'p', 0, 0.0) == 'm|DIFF|p|0|0.0'
    assert stem('qwen3', 0.3, 2) == 'test.qwen3.t0.3.s2'
    print('ok')


if __name__ == '__main__':
    if '--selfcheck' in sys.argv:
        selfcheck()
