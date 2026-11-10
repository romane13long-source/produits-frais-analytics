"""Lance tout le pipeline : Bronze (data/raw) -> Silver -> Gold -> livrables Comex (docs/)."""
import runpy
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"
sys.path.insert(0, str(SRC))

for step in ["clean_product", "clean_loss_rate", "clean_price", "clean_transaction", "build_gold",
             "build_dashboard", "build_slides"]:
    print(f"\n=== {step}")
    runpy.run_path(str(SRC / f"{step}.py"), run_name="__main__")
