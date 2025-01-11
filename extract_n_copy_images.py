import argparse
import os
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import unquote, quote


def parse_arguments():
    """
    Parse command-line arguments.
    Returns:
        args: Parsed arguments containing source_md, dest_md, destination, root, verbose, dry_run, overwrite, and interactive.
    """
    parser = argparse.ArgumentParser(
        description='Extract images from a source Markdown file, copy them to a destination folder, and update image paths in a destination Markdown file.'
    )
    parser.add_argument(
        '--source-md',
        type=str,
        required=True,
        help='Path to the source Markdown (.md) file.'
    )
    parser.add_argument(
        '--dest-md',
        type=str,
        required=True,
        help='Path to the destination Markdown (.md) file where updated image paths will be written.'
    )
    parser.add_argument(
        '--destination',
        type=str,
        required=True,
        help='Path to the destination folder where images will be copied.'
    )
    parser.add_argument(
        '--root',
        type=str,
        required=True,
        help='Root directory corresponding to the web server\'s root ("/").'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Increase output verbosity.'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simulate the copy and update operations without making any changes.'
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--overwrite',
        action='store_true',
        help='Overwrite existing files in the destination without prompting.'
    )
    group.add_argument(
        '--interactive',
        action='store_true',
        help='Prompt for each existing file to decide whether to overwrite.'
    )
    return parser.parse_args()


def read_markdown_file(filepath):
    """
    Read the content of the Markdown file.
    Args:
        filepath (Path): Path to the Markdown file.
    Returns:
        str: Content of the file.
    """
    try:
        with filepath.open('r', encoding='utf-8') as file:
            content = file.read()
        return content
    except Exception as e:
        print(f"Error reading file {filepath}: {e}")
        sys.exit(1)


def extract_image_paths(markdown_content):
    """
    Extract image paths from Markdown content that start with /.attachments/.
    Args:
        markdown_content (str): The content of the Markdown file.
    Returns:
        list: List of image paths matching the criteria.
    """
    # Regex to match Markdown image syntax: ![alt text](/.attachments/path/to/image)
    pattern = re.compile(r'!\[.*?\]\((/\.attachments/[^)]+)\)')
    matches = pattern.findall(markdown_content)
    return matches


def decode_url_path(url_path):
    """
    Decode URL-encoded characters in the path.
    Args:
        url_path (str): URL-encoded path.
    Returns:
        str: Decoded path.
    """
    try:
        decoded_path = unquote(url_path)
        return decoded_path
    except Exception as e:
        print(f"Error decoding URL path '{url_path}': {e}")
        return url_path  # Return the original path if decoding fails


def sanitize_directory_name(directory_name):
    """
    Remove or replace characters that are invalid in directory names.
    Args:
        directory_name (str): The original directory name.
    Returns:
        str: Sanitized directory name.
    """
    # Define a set of invalid characters based on common filesystem restrictions
    invalid_chars = '<>:"/\\|?*'
    sanitized = ''.join(c if c not in invalid_chars else '_' for c in directory_name)
    return sanitized


def prepare_destination_image_paths(image_paths):
    """
    Prepare the destination image paths by removing nested .attachments directories
    Args:
        image_paths (list): List of original image paths extracted from source Markdown.
    Returns:
        list: List of modified image paths for the destination Markdown.
    """
    prepared_paths = []
    for path in image_paths:
        # If the path starts with '/.attachments/', process it
        if path.startswith('/.attachments/'):
            # Parse the path
            p = Path(path)
            parts = p.parts  # tuple (starts with '/')
            # Reconstruct the path without nested .attachments
            new_parts = []
            for part in parts:
                if part.lower() == '.attachments' and len(new_parts) > 1:
                    # Skip any nested .attachments directories
                    continue
                new_parts.append(part)
            # Reconstruct the path
            new_path = Path(*new_parts).as_posix()
            prepared_paths.append(new_path)
        else:
            # Handle relative paths if necessary
            prepared_path = re.sub(r'^(\.\./)+\.attachments/', '/.attachments/', path)
            prepared_paths.append(prepared_path)
    return prepared_paths


def resolve_image_paths(image_paths, root_dir):
    """
    Convert image paths to absolute paths based on the root directory.
    Args:
        image_paths (list): List of image paths.
        root_dir (Path): Root directory corresponding to "/".
    Returns:
        list: List of absolute image paths as Path objects.
    """
    absolute_paths = []
    for path in image_paths:
        # Decode URL-encoded path
        decoded_path = decode_url_path(path)

        # Normalize path separators
        normalized_path = Path(decoded_path).as_posix()  # Use posix to handle forward slashes

        if decoded_path.startswith('/'):
            # Absolute path relative to root_dir
            relative_path = decoded_path.lstrip('/')
            absolute_path = root_dir / Path(relative_path)
        else:
            # Relative path to the root_dir
            absolute_path = root_dir / Path(normalized_path)

        # Resolve to absolute path without strict checking
        try:
            absolute_path = absolute_path.resolve(strict=False)
            absolute_paths.append(absolute_path)
        except Exception as e:
            print(f"Error resolving path '{decoded_path}': {e}")

    return absolute_paths


def copy_images(image_absolute_paths, prepared_image_paths, destination, root_dir, dry_run=False, verbose=False, overwrite=False, interactive=False):
    """
    Copy images to the destination folder using the prepared image paths.
    Args:
        image_absolute_paths (list): List of absolute image paths as Path objects.
        prepared_image_paths (list): List of prepared image paths for destination Markdown.
        destination (Path): Destination folder path.
        root_dir (Path): Root directory corresponding to "/".
        dry_run (bool): If True, simulate the copy operation.
        verbose (bool): If True, provide detailed output.
        overwrite (bool): If True, overwrite existing files without prompting.
        interactive (bool): If True, prompt for each existing file to decide whether to overwrite.
    Returns:
        dict: Mapping of original image paths to new image paths.
    """
    if not destination.exists():
        if dry_run:
            if verbose:
                print(f"[Dry-Run] Would create destination directory: {destination}")
        else:
            try:
                destination.mkdir(parents=True, exist_ok=True)
                if verbose:
                    print(f"Created destination directory: {destination}")
            except Exception as e:
                print(f"Error creating destination directory {destination}: {e}")
                sys.exit(1)

    copied_files = {}
    for src_path, dest_path in zip(image_absolute_paths, prepared_image_paths):
        src_file = Path(src_path)
        if not src_file.is_file():
            print(f"Image not found: {src_file}")
            continue

        # Ensure the destination path starts with /.attachments/
        if not dest_path.startswith('/.attachments/'):
            print(f"Invalid destination image path: {dest_path}. It should start with '/.attachments/'. Skipping.")
            continue

        # Remove the leading '/.attachments/' to map correctly
        prefix = '/.attachments/'
        if dest_path.startswith(prefix):
            relative_dest_path = dest_path[len(prefix):]
        else:
            print(f"Destination path does not start with '{prefix}': {dest_path}. Skipping.")
            continue

        destination_file = destination / Path(relative_dest_path)

        # Ensure parent directories exist
        if not destination_file.parent.exists():
            if dry_run:
                if verbose:
                    print(f"[Dry-Run] Would create directory: {destination_file.parent}")
            else:
                try:
                    destination_file.parent.mkdir(parents=True, exist_ok=True)
                    if verbose:
                        print(f"Created directory: {destination_file.parent}")
                except Exception as e:
                    print(f"Error creating directory {destination_file.parent}: {e}")
                    continue

        if destination_file.exists():
            if overwrite:
                action = 'overwrite'
            elif interactive:
                # Prompt user for action
                while True:
                    user_input = input(f"File '{destination_file}' already exists. Overwrite? (y/n): ").strip().lower()
                    if user_input == 'y':
                        action = 'overwrite'
                        break
                    elif user_input == 'n':
                        action = 'skip'
                        break
                    else:
                        print("Please enter 'y' or 'n'.")
            else:
                # Default action: skip
                action = 'skip'

            if action == 'overwrite':
                if dry_run:
                    if verbose:
                        print(f"[Dry-Run] Would overwrite: {destination_file}")
                else:
                    try:
                        shutil.copy(src_file, destination_file)
                        copied_files[str(src_file)] = destination_file
                        if verbose:
                            print(f"Overwritten: {destination_file}")
                    except Exception as e:
                        print(f"Failed to overwrite {destination_file}: {e}")
            elif action == 'skip':
                if verbose:
                    print(f"Skipped existing file: {destination_file}")
                continue
        else:
            if dry_run:
                if verbose:
                    print(f"[Dry-Run] Would copy: {src_file} to {destination_file}")
            else:
                try:
                    shutil.copy(src_file, destination_file)
                    copied_files[str(src_file)] = destination_file
                    if verbose:
                        print(f"Copied: {destination_file}")
                except Exception as e:
                    print(f"Failed to copy {src_file} to {destination_file}: {e}")

    return copied_files


def update_markdown_file(dest_md_path, prepared_image_paths, verbose=False, dry_run=False):
    """
    Update image paths in the destination Markdown file with prepared image paths.
    Args:
        dest_md_path (Path): Path to the destination Markdown file.
        prepared_image_paths (list): List of prepared image paths for destination Markdown.
        verbose (bool): If True, provide detailed output.
        dry_run (bool): If True, simulate the update operation.
    Returns:
        None
    """
    if not dest_md_path.is_file():
        print(f"Destination Markdown file does not exist: {dest_md_path}")
        sys.exit(1)

    try:
        dest_content = read_markdown_file(dest_md_path)
    except Exception as e:
        print(f"Error reading destination Markdown file {dest_md_path}: {e}")
        sys.exit(1)

    # Define regex to find image paths starting with ../../../.attachments/
    # This regex captures the alt text and the image path
    pattern = re.compile(r'!\[([^\]]*)\]\((\.\./){3}\.attachments/([^)]+)\)')

    # Find all matches
    matches = list(pattern.finditer(dest_content))
    if not matches:
        print("No matching image paths found in the destination Markdown file.")
        return

    if len(matches) != len(prepared_image_paths):
        print("Warning: The number of image paths in the destination Markdown file does not match the number of prepared image paths.")
        print("Ensure that the order of image paths in the source and destination Markdown files is consistent.")
        # Proceeding with replacing as many as possible
        min_len = min(len(matches), len(prepared_image_paths))
        matches = matches[:min_len]
        prepared_image_paths = prepared_image_paths[:min_len]

    # Create a generator for the new image paths
    new_paths_generator = iter(prepared_image_paths)

    # Replacement function
    def replacement(match):
        try:
            new_path = next(new_paths_generator)
            alt_text = match.group(1)
            return f"![{alt_text}]({new_path})"
        except StopIteration:
            return match.group(0)  # Return original if no replacement available

    # Perform substitution
    updated_content, num_subs = pattern.subn(replacement, dest_content)

    if verbose and num_subs > 0:
        print(f"Updated {num_subs} image path(s) in destination Markdown file.")

    if dry_run:
        if verbose:
            print(f"[Dry-Run] Would update destination Markdown file: {dest_md_path}")
    else:
        try:
            with dest_md_path.open('w', encoding='utf-8') as file:
                file.write(updated_content)
            if verbose:
                print(f"Updated destination Markdown file: {dest_md_path}")
        except Exception as e:
            print(f"Error writing to destination Markdown file {dest_md_path}: {e}")
            sys.exit(1)


def main():
    # Step 1: Parse command-line arguments
    args = parse_arguments()
    source_md = Path(args.source_md).resolve()
    dest_md = Path(args.dest_md).resolve()
    destination = Path(args.destination).resolve()
    root_dir = Path(args.root).resolve()
    verbose = args.verbose
    dry_run = args.dry_run
    overwrite = args.overwrite
    interactive = args.interactive

    # Validate source Markdown file
    if not source_md.is_file():
        print(f"Source Markdown file does not exist: {source_md}")
        sys.exit(1)

    # Validate root directory
    if not root_dir.is_dir():
        print(f"Root directory does not exist or is not a directory: {root_dir}")
        sys.exit(1)

    # Step 2: Read source Markdown file
    source_content = read_markdown_file(source_md)

    # Step 3: Extract image paths from source Markdown file
    image_paths = extract_image_paths(source_content)
    if not image_paths:
        print("No images with path starting with '/.attachments/' found in the source Markdown file.")
        sys.exit(0)

    print(f"Found {len(image_paths)} image(s) starting with '/.attachments/' in the source Markdown file.")

    # Step 4: Prepare destination image paths by removing nested .attachments directories
    prepared_image_paths = prepare_destination_image_paths(image_paths)

    # Step 5: Resolve image paths to absolute paths based on root_dir
    # These are the actual files to be copied
    absolute_image_paths = resolve_image_paths(image_paths, root_dir)

    # Step 6: Copy images to destination using the prepared image paths
    copied_files = copy_images(
        image_absolute_paths=absolute_image_paths,
        prepared_image_paths=prepared_image_paths,
        destination=destination,
        root_dir=root_dir,
        dry_run=dry_run,
        verbose=verbose,
        overwrite=overwrite,
        interactive=interactive
    )

    # Step 7: Update image paths in destination Markdown file
    update_markdown_file(
        dest_md_path=dest_md,
        prepared_image_paths=prepared_image_paths,
        verbose=verbose,
        dry_run=dry_run
    )

    # Summary
    print("\nSummary:")
    print(f"Total images found: {len(image_paths)}")
    if dry_run:
        print("Dry-Run Mode: No files were actually copied or updated.")
    else:
        print(f"Total images copied: {len(copied_files)}")
    if copied_files and not dry_run:
        print("Copied files:")
        for file in copied_files.values():
            print(f" - {file}")
    if not dry_run:
        print(f"Destination Markdown file updated: {dest_md}")


if __name__ == "__main__":
    main()
