A simple Python script that can compress the PNG files inside the epub files,
in this case "Cure Dolly Complete Grammar Series Transcript (in minor editing)"
which can be fount at: https://docs.google.com/document/d/1XpuXerkGU8waJ4DPDNJA4bGeqOvM-csXjTe57iHARHc,
with the help of pngquant (https://pngquant.org). pngquant should be in the PATH.

# Usage

`
python.exe opt.py --help
`

```
usage: opt.py [-h] [-i EPUB_INPUT]

A simple Python script that can compress the PNG files inside the epub files, in this case "Cure Dolly Complete Grammar Series Transcript (in minor
editing)" which can be fount at: https://docs.google.com/document/d/1XpuXerkGU8waJ4DPDNJA4bGeqOvM-csXjTe57iHARHc, with the help of pngquant
(https://pngquant.org). pngquant should be in the PATH.

options:
  -h, --help            show this help message and exit
  -i EPUB_INPUT, --input EPUB_INPUT
                        Path of the input epub file.
```

![](res/how-to-download.png)
*You need to download the document as an epub file from the Google Docs link provided above.*

# Credits
This particular script doesn't do much actually, all the credits belong to the people/projects below.

- [Organic Japanese with Cure Dolly](https://www.youtube.com/@organicjapanesewithcuredol49): Created all Japanese videos on YouTube.
- [Mordraug/Nunko](https://docs.google.com/document/d/1XpuXerkGU8waJ4DPDNJA4bGeqOvM-csXjTe57iHARHc) Psrepared transcripts in the form of Google Docs.
- [pngquant](https://pngquant.org) Program used for compressing PNG files.