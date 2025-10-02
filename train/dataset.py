from pathlib import Path
import random
from tqdm import tqdm
import shutil


def make_small_test_split(root_dir: str, to_keep: int = 0.1):
    root_path = Path(root_dir)
    full_images_dir = root_path / "images"
    full_labels_dir = root_path / "labels"

    small_images_dir = root_path.parent / "images"
    small_labels_dir = root_path.parent / "labels"

    small_images_dir.mkdir(parents=True, exist_ok=True)
    small_labels_dir.mkdir(parents=True, exist_ok=True)

    images = list(full_images_dir.glob("*.jpg"))
    images_count = len(images)

    new_images_count = int(images_count * to_keep)

    new_images = random.sample(images, new_images_count)

    for new_image in tqdm(new_images, desc="Making smaller test split..."):
        shutil.copy(new_image, small_images_dir / new_image.name)

        label_file = full_labels_dir / f"{new_image.stem}.txt"

        shutil.copy(label_file, small_labels_dir / label_file.name)
    
    print(f"New split has {new_images_count} images.")


if __name__ == "__main__":
    make_small_test_split("D:\\studia\\semestr_8\\zespolowy_projekt_badawczy\\qgis-yolo-plugin\\train\\dataset\\DOTANA\\test\\full")