# WikiTools

Simple toolset to work with Azure DevOps Wiki

## markdown_server.py

`markdown_server.py` is a script that serves markdown files as HTML over a local web server. It allows you to view and navigate markdown files in your browser.

### Usage for extract_n_copy_images.py

```bash
python markdown_server.py --directory "<markdown_files_directory>" --port "<port_number>"
```

### Example for markdown_server.py

```bash
python markdown_server.py --directory "C:\Users\user\Projects\MarkdownFiles" --port 8000
```

### Arguments for markdown_server.py

- `--directory`: Path to the directory containing markdown files to be served.
- `--port`: Port number on which the server will run.

### Requirements for markdown_server.py

- Python 3.x
- Flask

### Installation for markdown_server.py

Clone the repository and navigate to the script directory:

```bash
git clone <repository_url>
cd <repository_directory>
pip install -r requirements.txt
```

## extract_n_copy_images.py

`extract_n_copy_images.py` is a script designed to extract images from a source markdown file and copy them to a specified destination directory. It also updates the image paths in the destination markdown file.

### Usage

```bash
python extract_n_copy_images.py --source-md "<source_markdown_file>" --destination "<destination_directory>" --root "<root_directory>" --dest-md "<destination_markdown_file>"
```

### Example

```bash
python extract_n_copy_images.py --source-md "C:\Users\user\Projects\HPC Wiki\AzureHPCandAI\AzureHPCandAI\High-Complexity-Low-Volume-aka-HCLV-Wiki\High-Performance-Computing-Overview\GPU-Optimized-VMs\TSGs\TSG%3A-increase-FPS-on-RDP.md" --destination "C:\Users\user\Projects\HPC Wiki\AzureIaaSVM\AzureIaaSVM\.attachments\SME-Topics\Performance" --root "C:\Users\user\Projects\HPC Wiki\AzureHPCandAI\AzureHPCandAI" --dest-md "C:\Users\user\Projects\HPC Wiki\AzureIaaSVM\AzureIaaSVM\SME-Topics\Performance\TSGs\Zooming_Slow_In_RDP_Perf.md"
```

### Arguments

- `--source-md`: Path to the source markdown file from which images will be extracted.
- `--destination`: Path to the directory where the extracted images will be copied.
- `--root`: Root directory for resolving relative paths in the source markdown file.
- `--dest-md`: Path to the destination markdown file where image paths will be updated.

### Requirements

- Python 3.x

### Installation

Clone the repository and navigate to the script directory:

```bash
git clone <repository_url>
cd <repository_directory>
```

## License

This project is licensed under the MIT License.

## Author and Feedback

© 2025 &mdash; ∞ Ivan Rusakov. All rights reserved.

[![Report an Issue](https://img.shields.io/github/issues-raw/ivanrusakov_microsoft/WikiTools?style=flat-square&logo=github&color=ff69b4)](https://github.com/ivanrusakov_microsoft/WikiTools/issues)
