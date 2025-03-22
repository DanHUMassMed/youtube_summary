#!/usr/bin/env python3
import os
import argparse
from app.lex_podcast_summary import LexPodcastSummary
from app.youtube_transcribe import extract_video_id

def main():
    parser = argparse.ArgumentParser(description='Lex podcast URL and working directory.')

    parser.add_argument('podcast_url', type=str, help='URL of the podcast')
    parser.add_argument('work_dir', nargs='?', default=None, type=str,
                        help='Directory to save podcast files (default is current directory)')

    args = parser.parse_args()

    print(f'Podcast URL: {args.podcast_url}')
    print(f'Working Directory: {args.work_dir}')
    
    # Let's check if we can extract the video id from this URL?
    try:
        video_id = extract_video_id(args.podcast_url)
    except Exception:
        print("Error: Can not parse the provided URL")
        return

    if args.work_dir:
        file_name = 'checkpoints.json'
        file_path = os.path.join(args.work_dir, file_name)
        if os.path.isdir(args.work_dir):
            if os.path.isfile(file_path):
                lex_podcast_summary = LexPodcastSummary(args.podcast_url, results_dir=args.work_dir)
            else:
                print(f"Error: '{args.work_dir}'directory must has a checkpoint.json file.")
                return
        else:
            print(f"Error: The directory '{args.work_dir}' does not exist.")
            return
    
        lex_podcast_summary = LexPodcastSummary(args.podcast_url, results_dir=args.work_dir)
    else:
        lex_podcast_summary = LexPodcastSummary(args.podcast_url)
            
    
    config_params = {
        'model_name': 'qwen2.5:32b',
        'temperature': 0.0,
        'num_cxt': 32 * 1024,
        'raw_text_chunk_size': 32 * 1024,
        'text_chunk_overlay_size': 100,
    }

    lex_podcast_summary.config(**config_params)
    lex_podcast_summary.create_summary_report()
    

if __name__ == '__main__':
    main()