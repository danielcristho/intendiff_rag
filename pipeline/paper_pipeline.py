"""Draw the manuscript pipeline from the documented static analysis workflow.

Usage: MPLCONFIGDIR=/tmp/intendiff-mpl .venv/bin/python pipeline/paper_pipeline.py
"""
from pathlib import Path

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
from matplotlib.path import Path as PlotPath


def render():
    plt.rcParams.update({'font.family': 'DejaVu Sans', 'pdf.fonttype': 42,
                         'svg.fonttype': 'none'})
    fig, ax = plt.subplots(figsize=(7.2, 4.6))
    ax.set(xlim=(0, 12), ylim=(0, 7.5))
    ax.axis('off')
    fig.subplots_adjust(left=.01, right=.99, bottom=.01, top=.99)
    ink, blue, muted = '#243442', '#17638a', '#526675'
    boxes, labels = [], []

    def box(x, y, w, h, title, body, fill='#f2f6f8'):
        patch = FancyBboxPatch((x, y), w, h,
                              boxstyle='round,pad=0.02,rounding_size=0.08',
                              linewidth=.8, edgecolor=ink, facecolor=fill, zorder=3)
        ax.add_patch(patch)
        heading = ax.text(x+w/2, y+h-.24, title, ha='center', va='center',
                          fontsize=8.2, weight='bold', color=ink, zorder=4)
        text = ax.text(x+w/2, y+(h-.43)/2, body, ha='center', va='center',
                       fontsize=7.5, linespacing=1.35, color=ink, zorder=4)
        boxes.append(patch)
        labels.append((patch, heading, text))

    def edge(points, dashed=False, head=True):
        path = PlotPath(points, [PlotPath.MOVETO] + [PlotPath.LINETO]*(len(points)-1))
        ax.add_patch(FancyArrowPatch(path=path, arrowstyle='-|>' if head else '-',
                                    mutation_scale=9, linewidth=.9, color=blue,
                                    linestyle=(0, (4, 3)) if dashed else '-', zorder=2))

    ax.text(6, 7.27, 'IntentDiff-RAG: static analysis of one package update',
            ha='center', fontsize=10, weight='bold', color=ink)
    box(.25, 5.9, 8.55, 1.0, 'Package version pair',
        'Predecessor archive + target archive (same package)', '#eaf2f7')
    box(9.2, 5.9, 2.55, 1.0, 'Knowledge base',
        '50 malicious + 25 benign\nSeparate from test data', '#f6f3ed')

    box(.25, 3.85, 2.55, 1.5, 'Smart-diff',
        'Normalize and compare\nKeep complete diff hunks\nUp to 28,000 tokens')
    box(3.2, 3.85, 2.55, 1.5, 'Predecessor intent',
        'Description + keywords\nScripts + README\nUp to 1,024 tokens')
    box(6.15, 3.85, 2.65, 1.5, 'Capability changes',
        'Scan both raw archives\nNew / changed capabilities\nUsed as the retrieval query')
    box(9.2, 3.85, 2.55, 1.5, 'Retrieve examples',
        'Jaccard ranking + hash ties\nExclude related examples\nSelect M, MM or MB', '#f6f3ed')

    for x in (1.525, 4.475, 7.475):
        edge([(x, 5.9), (x, 5.35)])
    edge([(10.475, 5.9), (10.475, 5.35)])
    edge([(8.8, 4.6), (9.2, 4.6)])

    box(2.9, 1.95, 4.0, 1.25, 'Assemble the prompt',
        'Same smart-diff in every configuration\nAdd intent and examples when enabled', '#eaf2f7')
    edge([(1.525, 3.85), (1.525, 2.575), (2.9, 2.575)])
    edge([(4.475, 3.85), (4.475, 3.2)], dashed=True)
    edge([(10.475, 3.85), (10.475, 2.575), (6.9, 2.575)], dashed=True)

    box(2.9, .35, 4.0, 1.05, 'Local language model',
        'Fixed decision instructions\nJSON Schema-constrained output', '#eaf2f7')
    box(8.1, .35, 3.65, 1.05, 'Verdict and supporting text',
        'malicious / benign\nShort reason + evidence')
    edge([(4.9, 1.95), (4.9, 1.4)])
    edge([(6.9, .875), (8.1, .875)])

    ax.text(.25, 1.45, 'All package analysis\nis static; sample code\nis never executed.',
            fontsize=7.5, color=muted, va='top', linespacing=1.4)
    ax.text(6, .04, 'Dashed arrows: optional context.  M: malicious example; B: benign example.',
            fontsize=7, color=muted, ha='center', va='bottom')

    # Fail if wording no longer fits a box when the diagram is edited later.
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for patch, *texts in labels:
        bounds = patch.get_window_extent(renderer)
        for text in texts:
            tb = text.get_window_extent(renderer)
            if not (bounds.x0 <= tb.x0 and tb.x1 <= bounds.x1
                    and bounds.y0 <= tb.y0 and tb.y1 <= bounds.y1):
                raise ValueError(f'Diagram text does not fit: {text.get_text()}')

    out = Path('labs/latex/figures')
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out/'pipeline.pdf', bbox_inches='tight', pad_inches=.04)
    fig.savefig(out/'pipeline.svg', bbox_inches='tight', pad_inches=.04)
    fig.savefig(out/'pipeline.png', dpi=300, bbox_inches='tight', pad_inches=.04)
    plt.close(fig)


if __name__ == '__main__':
    render()
