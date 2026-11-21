"""Download the original public CDC files and verify the analysis source bytes."""
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import json
from urllib.request import urlopen
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / 'work' / 'raw'
SOURCES = [
    {
        'name': 'adult25.csv',
        'url': 'https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/NHIS/2025/adult25csv.zip',
        'archive_sha256': '94d5477ffc3a03e292a3000da8eb5ad71626ae8032bbaa98c9711b7a3b572570',
        'sha256': '011b46e814e619acd970a1449a7f7d6a97f52c7ffe07e955c753f791da23d12b',
        'size_bytes': 22038942,
    },
    {
        'name': 'adultinc25.csv',
        'url': 'https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/NHIS/2025/adultinc25csv.zip',
        'archive_sha256': '861bd254d29a375ae276539efe73775374f9205e5b4933ace2f07aa588d42535',
        'sha256': '6bb0bb5df0a9b066a098efda6e5b423b8a765d9f02359cf8622becc0943b861a',
        'size_bytes': 6237095,
    },
]


def main():
    DEST.mkdir(parents=True, exist_ok=True)
    for item in SOURCES:
        target = DEST / item['name']
        if target.exists():
            data = target.read_bytes()
        else:
            with urlopen(item['url'], timeout=90) as response:
                archive = response.read()
            if sha256(archive).hexdigest() != item['archive_sha256']:
                raise ValueError(f"CDC archive has changed: {item['name']}")
            with ZipFile(BytesIO(archive)) as z:
                candidates = [n for n in z.namelist() if Path(n).name.lower() == item['name']]
                if len(candidates) != 1:
                    raise ValueError(f"Expected one CSV in archive: {item['name']}")
                data = z.read(candidates[0])
        if len(data) != item['size_bytes'] or sha256(data).hexdigest() != item['sha256']:
            raise ValueError(f"Source CSV does not match the analyzed version: {item['name']}")
        if not target.exists():
            temporary = target.with_suffix('.csv.partial')
            temporary.write_bytes(data)
            temporary.replace(target)
        print(f"Verified {item['name']}: {len(data):,} bytes, SHA256 {item['sha256']}")
    manifest = ROOT / 'results' / 'source_checksums.json'
    manifest.write_text(json.dumps(SOURCES, indent=2) + '\n')


if __name__ == '__main__':
    main()
