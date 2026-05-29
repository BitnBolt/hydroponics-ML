"""Execute main.ipynb and save outputs back into the file."""
import nbformat
from nbclient import NotebookClient
from pathlib import Path

nb_path = Path('main.ipynb')
with open(nb_path, encoding='utf-8') as f:
    nb = nbformat.read(f, as_version=4)

client = NotebookClient(nb, timeout=300, kernel_name='python3')
client.execute()

with open(nb_path, 'w', encoding='utf-8') as f:
    nbformat.write(nb, f)

print(f'Executed and saved: {nb_path.resolve()}')
