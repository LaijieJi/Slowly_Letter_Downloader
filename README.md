# Slowly Letter Downloader

Automates the downloading of letters from the Slowly pen-pal app and saves them as PDFs.

## Requirements

- Python 3.13 or later
- Chromium (installed automatically via Playwright)

On macOS, Python 3.13 requires the Tk bindings to be installed separately:

```bash
brew install python-tk@3.13
```

## Installation

```bash
pip install -r requirements.txt
playwright install chromium
```

## Usage

Launch the application:

```bash
python main.py
```

1. Click **Login**. A browser window will open to the Slowly web app.
2. Scan the QR code using the Slowly app on your phone. The browser will close automatically once login is detected.
3. Select the penpals you wish to download letters from.
4. Click **Run**. Letters are saved as PDFs in the `letters/` directory, organised by penpal name.

Running the program again will skip letters that have already been downloaded.

## Features

- Cross-platform - runs on Windows, macOS, and Linux
- Downloads letters from one or more penpals in a single run
- Preserves images and stamps embedded in letters
- Skips already-downloaded letters on subsequent runs
- Light and dark themes, follows system appearance by default

## Output

Downloaded PDFs are saved to `letters/<penpal_name>/` with names in the format `letter{N}_{sender}_{date}.pdf`. Each PDF contains metadata (letter number and penpal name) for deduplication.

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

## License

[MIT](https://choosealicense.com/licenses/mit/)
