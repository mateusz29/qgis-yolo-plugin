from pathlib import Path
from ultralytics import YOLO
from itertools import product
import json


def validate_models(
    models_root: Path,
    datasets_root: Path,
    results_dir: Path,
    versions=("11", "12"),
    datasets=("ships", "DOTANA_no_ships"),
    sizes=("s", "m", "l", "x"),
    soft_nms=(False, True)
):
    results = []

    combos = list(product(datasets, versions, sizes, soft_nms))

    for dataset, ver, size, soft_nms in combos:
        model_name = f"{dataset}_yolo{ver}{size}"
        model_path = models_root / (model_name + ".pt")
        data_path = datasets_root / (dataset + ".yaml")

        if not model_path.exists():
            print(f"Model not found: {model_path}")
            continue
        if not data_path.exists():
            print(f"Dataset not found: {data_path}")
            continue

        model = YOLO(model_path)

        metrics = model.val(
            data=str(data_path),
            split="test",
            softnms=soft_nms
        )

        result_entry = {
            "model": model_name,
            "version": ver,
            "dataset": dataset,
            "size": size,
            "soft_nms": soft_nms,
            "map50": metrics.box.map50,
            "map50_95": metrics.box.map,
            "precision": metrics.box.mp,
            "recall": metrics.box.mr,
        }
        results.append(result_entry)

    results_file = results_dir / "validation_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=4)

    print("\n=== Summary ===")
    for r in results:
        print(f"{r['model']:<35} "
              f"mAP@0.5: {r['map50']:.4f} | "
              f"mAP@0.5:0.95: {r['map50_95']:.4f} | "
              f"P: {r['precision']:.4f} | "
              f"R: {r['recall']:.4f}")
    
    print("\n=== Rankings per Dataset ===")
    metrics_to_sort = ["map50", "map50_95"]

    for dataset in set(r["dataset"] for r in results):
        print(f"\n📊 Dataset: {dataset}")
        dataset_results = [r for r in results if r["dataset"] == dataset]

        for metric in metrics_to_sort:
            sorted_results = sorted(dataset_results, key=lambda x: x[metric], reverse=True)
            print(f"\n🔹 Sorted by {metric.upper()}:")
            for rank, r in enumerate(sorted_results, 1):
                print(f"{rank:2d}. {r['model']:<35} {metric}: {r[metric]:.4f}")



if __name__ == "__main__":
    ROOT = Path(__file__).resolve().parent
    MODELS_ROOT = ROOT / "models"
    DATASETS_ROOT = ROOT / "dataset"

    validate_models(MODELS_ROOT, DATASETS_ROOT, ROOT)
