import http.server
import socketserver
import os
from urllib.parse import unquote
import markdown
import argparse
import sys
import logging
import html
from urllib import request
from io import BytesIO
import chardet


def parse_arguments():
    """
    Parse command-line arguments for directory and port.
    """
    parser = argparse.ArgumentParser(
        description="Simple HTTP Server that renders Markdown files as HTML."
    )
    parser.add_argument(
        '-d', '--directory',
        default=os.getcwd(),
        help='Directory to serve (default: current directory)'
    )
    parser.add_argument(
        '-p', '--port',
        type=int,
        default=8000,
        help='Port to listen on (default: 8000)'
    )
    return parser.parse_args()


def main():
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelno)s - %(message)s'
    )

    args = parse_arguments()

    DIRECTORY = os.path.abspath(os.path.normpath(args.directory.rstrip('"')))
    PORT = args.port

    if not os.path.isdir(DIRECTORY):
        logging.error(f"The directory '{DIRECTORY}' does not exist.")
        sys.exit(1)

    os.chdir(DIRECTORY)
    logging.info(f"Serving directory '{DIRECTORY}' at http://localhost:{PORT}")

    class MarkdownRequestHandler(http.server.SimpleHTTPRequestHandler):
        """
        Custom request handler that renders Markdown files as HTML.
        """

        def do_GET(self):
            """Serve GET requests, render Markdown or handle other files."""
            # Decode URL to handle spaces and special characters
            self.path = unquote(self.path)

            # If the path is root or ends with '/', attempt to serve 'index.md'
            if self.path == "/" or self.path.endswith("/"):
                index_md = os.path.join(DIRECTORY, "index.md")
                if os.path.isfile(index_md):
                    self.path = "/index.md"

            # If the requested file is a Markdown file
            if self.path.endswith(".md"):
                md_path = os.path.join(DIRECTORY, self.path.lstrip("/"))
                if os.path.isfile(md_path):
                    try:
                        with open(md_path, "rb") as f:
                            raw = f.read()
                            detected = chardet.detect(raw)
                            encoding = detected['encoding'] or 'utf-8'
                            md_content = raw.decode(encoding, errors='replace')
                            html_content = markdown.markdown(md_content, extensions=['fenced_code', 'tables'])
                            self.send_html(html_content, md_path)
                    except Exception as e:
                        logging.error(f"Error reading file '{self.path}': {e}")
                        self.send_error(500, "Unable to process the Markdown file.")
                    return
            else:
                super().do_GET()

        def send_html(self, html_content, file_name):
            """Send an HTML response."""
            full_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>{file_name}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; padding: 20px; }}
                    pre {{ background-color: #f4f4f4; padding: 10px; overflow-x: auto; }}
                </style>
            </head>
            <body>
                {html_content}
            </body>
            </html>
            """
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(full_html.encode("utf-8"))

    Handler = MarkdownRequestHandler

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            logging.info("Shutting down server.")
            httpd.server_close()


if __name__ == "__main__":
    main()
