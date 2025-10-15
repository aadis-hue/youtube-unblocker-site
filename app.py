from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
import os
import tempfile
from urllib.parse import urlparse

app = Flask(__name__)

class VideoDownloader:
    def __init__(self):
        self.temp_dir = tempfile.gettempdir()
    
    def get_video_info(self, url):
        """Extract video information without downloading"""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                formats = []
                for f in info['formats']:
                    if f.get('filesize') or f.get('filesize_approx'):
                        format_info = {
                            'format_id': f['format_id'],
                            'ext': f['ext'],
                            'quality': f.get('format_note', 'N/A'),
                            'filesize': f.get('filesize', f.get('filesize_approx', 0)),
                            'resolution': f.get('height', 'N/A')
                        }
                        formats.append(format_info)
                
                video_data = {
                    'title': info['title'],
                    'thumbnail': info['thumbnail'],
                    'duration': info['duration'],
                    'formats': formats,
                    'streaming_url': info['url'] if 'url' in info else None
                }
                return video_data
        except Exception as e:
            return {'error': str(e)}
    
    def download_video(self, url, format_id='best'):
        """Download video in specified format"""
        ydl_opts = {
            'outtmpl': os.path.join(self.temp_dir, '%(title)s.%(ext)s'),
            'format': format_id,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                filename = ydl.prepare_filename(info)
                return filename
        except Exception as e:
            return None

downloader = VideoDownloader()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/info', methods=['POST'])
def get_video_info():
    url = request.json.get('url')
    if not url:
        return jsonify({'error': 'No URL provided'})
    
    info = downloader.get_video_info(url)
    return jsonify(info)

@app.route('/api/download', methods=['POST'])
def download_video():
    url = request.json.get('url')
    format_id = request.json.get('format', 'best')
    
    if not url:
        return jsonify({'error': 'No URL provided'})
    
    filename = downloader.download_video(url, format_id)
    if filename and os.path.exists(filename):
        return send_file(filename, as_attachment=True)
    else:
        return jsonify({'error': 'Download failed'})

if __name__ == '__main__':
    app.run(debug=True)
