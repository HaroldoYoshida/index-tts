import os
import json
import random
from pathlib import Path
import argparse

def scan_and_map_emotions(data_dir, output_file, character_name="anbi"):
    """
    Scans the directory for audio files and maps them to emotions based on filenames.
    Structure: { "emotion_tag": ["path/to/file1.wav", "path/to/file2.wav"] }
    """
    print(f"🔍 Scanning {data_dir} for {character_name} assets...")
    
    # Emotion keywords to look for in filenames
    emotion_keywords = {
        "combat": ["Combat", "Attack", "Hit", "Damage", "Die"],
        "happy": ["Laugh", "Smile", "Happy", "Joy", "Excited"],
        "sad": ["Sad", "Cry", "Doubt", "Depressed", "Sigh"],
        "angry": ["Angry", "Shout", "Yell"],
        "fear": ["Scared", "Fear", "Suprised", "Surprised"], # Typo handling for 'Suprised'
        "embarrassed": ["Embarrassed", "Shy"],
        "eating": ["Eat", "Drink", "Chew"],
        "action": ["Run", "Jump", "Dash", "Evade"],
        "neutral": [] # Fallback
    }

    base_path = Path(data_dir)
    audio_files = list(base_path.glob("**/*.wav"))
    
    emotion_map = {k: [] for k in emotion_keywords.keys()}
    total_mapped = 0
    
    for audio_path in audio_files:
        filename = audio_path.name
        # Simple keyword matching
        matched = False
        for emotion, keywords in emotion_keywords.items():
            if emotion == "neutral": continue
            
            for kw in keywords:
                if kw.lower() in filename.lower():
                    # Release absolute path or relative? Let's use relative to project root for portability
                    # But for now, absolute is safer for the orchestrator on the same machine
                    emotion_map[emotion].append(str(audio_path.absolute()))
                    matched = True
                    break
            if matched: break
            
        if not matched:
            emotion_map["neutral"].append(str(audio_path.absolute()))
        
        total_mapped += 1

    # Filter empty categories
    final_map = {k: v for k, v in emotion_map.items() if v}
    
    # Save to JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({character_name: final_map}, f, indent=2, ensure_ascii=False)
        
    print(f"✅ Mapped {total_mapped} files to {output_file}")
    print("📊 Distribution:")
    for emo, files in final_map.items():
        print(f"   - {emo}: {len(files)} files")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data_dir", default="data/anbi_en", help="Directory containing character audio")
    parser.add_argument("--output", default="assets/character_emotions.json", help="Output JSON file")
    
    args = parser.parse_args()
    
    # Ensure output dict exists
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    scan_and_map_emotions(args.data_dir, args.output)
