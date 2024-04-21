import shutil
import subprocess
import zipfile
from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent

class Main:
    def __init__(self, epub_file: str|Path) -> None:
        self.epub_file = Path(epub_file)

    def check_pngquant(self) -> None:
        if not shutil.which("pngquant"):
            raise FileNotFoundError("[!] pngquant is not in the PATH.")

    def main(self) -> None:
        self.check_pngquant()
        def pngquant(_path: Path) -> None:
            res = subprocess.Popen(
                ["pngquant", "--ext", ".png", "--force",
                "--quality", "0-45", "8", str(_path)],
                stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT)
            return res.communicate()[0]
        if not self.epub_file.exists():
            raise FileNotFoundError(f"[!] {self.epub_file} does not exist.")
        tmp = SCRIPT_DIR / "unpacked"
        if not tmp.exists():
            tmp.mkdir()
        with zipfile.ZipFile(self.epub_file, "r") as epub:
            epub.extractall(tmp)
        pngs = tmp.rglob("*.png")
        with ThreadPoolExecutor() as executor:
            for png in pngs:
                executor.submit(pngquant, png)
        all_files = tmp.rglob("*")
        with zipfile.ZipFile(SCRIPT_DIR / f"{self.epub_file.stem}_Compressed.epub", "w") as epub_out:
            for p in [x for x in all_files if not x.is_dir()]:
                relative_filename = p.relative_to(tmp).parent / p.name
                epub_out.writestr(str(relative_filename), p.read_bytes())

class ArgparseNS:
    epub_input: str|Path = SCRIPT_DIR / "Cure Dolly Complete Grammar Series Transcript (in minor editing).epub"

if __name__ == '__main__':
    parser = ArgumentParser(description="""
    A simple Python script that can compress the PNG files inside the ePub files,
    in this case "Cure Dolly Complete Grammar Series Transcript (in minor editing)"
    which can be fount at: https://docs.google.com/document/d/1XpuXerkGU8waJ4DPDNJA4bGeqOvM-csXjTe57iHARHc,
    with the help of pngquant (https://pngquant.org). pngquant should be in the PATH.
    """)
    parser.add_argument("-i", "--input", help="Path of the input ePub file.", dest="epub_input")
    args = parser.parse_args(namespace=ArgparseNS)
    main = Main(args.epub_input)
    main.main()