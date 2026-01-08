from huggingface_hub import list_repo_files

def list_files(repo_id):
    print(f"\n--- {repo_id} ---")
    try:
        files = list_repo_files(repo_id, repo_type="dataset")
        filtered = [f for f in files if "jp" in f.lower() or "japanese" in f.lower()]
        if not filtered:
            print("No 'jp'/'japanese' files found. Showing first 10 files:")
            print('\n'.join(files[:10]))
        else:
            print(f"Found {len(filtered)} matching files. First 20:")
            print('\n'.join(filtered[:20]))
    except Exception as e:
        print(f"Error: {e}")

list_files("simon3000/genshin-voice")
list_files("AI-Hobbyist/Genshin_Datasets")
list_files("Genius-Society/hoyoTTS")
