"""从任意目录启动可携带原型；默认只允许本机访问，Ctrl+C 停止。"""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8872)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    with ThreadingHTTPServer(('127.0.0.1', args.port), partial(SimpleHTTPRequestHandler, directory=str(root))) as server:
        print(f'Preview: http://127.0.0.1:{server.server_port}/review.html?section=models', flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass

if __name__ == '__main__':
    main()
