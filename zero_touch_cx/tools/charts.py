from __future__ import annotations
from pathlib import Path
import matplotlib.pyplot as plt
from ..observability import span

TMP_DIR = Path(__file__).resolve().parents[2] / "artifacts"
TMP_DIR.mkdir(exist_ok=True)

def bar_chart(title: str, labels: list[str], values: list[float], filename: str) -> str:
    with span("bar_chart", title=title):
        path = TMP_DIR / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        fig = plt.figure()
        ax = fig.add_subplot(111)
        ax.bar(labels, values)
        ax.set_title(title)
        fig.tight_layout()
        fig.savefig(path)
        plt.close(fig)
        return str(path)
