import json
import os

def convert_txt_to_jsonl(input_file, output_file, language="en", speaker="anbi"):
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for idx, line in enumerate(lines):
            parts = line.strip().split('|')
            if len(parts) >= 2:
                audio_path = parts[0]
                text = parts[1]
                
                # Check if audio exists (optional, but good for sanity)
                # For now, just generate the entry
                
                entry = {
                    "id": f"{speaker}_{language}_{idx:05d}",
                    "text": text,
                    "audio": audio_path,
                    "speaker": speaker,
                    "language": language
                }
                f.write(json.dumps(entry, ensure_ascii=False) + '\n')

if __name__ == "__main__":
    convert_txt_to_jsonl("filelists/train_anbi_en.txt", "filelists/train_anbi_en.jsonl")
