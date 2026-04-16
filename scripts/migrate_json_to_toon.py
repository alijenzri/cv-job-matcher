import json
import os
import glob
try:
    import toon_python as toon
except ImportError:
    print("toon-python not installed. Please install it with: pip install toon-python")
    exit(1)

def migrate_json_to_toon(directory):
    print(f"Scanning {directory} for JSON files...")
    json_files = glob.glob(os.path.join(directory, "*.json"))
    
    if not json_files:
        print("No JSON files found.")
        return

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            toon_file = json_file.replace('.json', '.toon')
            print(f"Converting {json_file} -> {toon_file}")
            
            # Using toon.encode to convert python object to TOON string
            toon_data = toon.encode(data)
            
            with open(toon_file, 'w', encoding='utf-8') as f:
                f.write(toon_data)
                
            print(f"Successfully converted {json_file}")
            
        except Exception as e:
            print(f"Error converting {json_file}: {e}")

if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    kb_dir = os.path.join(base_dir, "data", "knowledge_base")
    migrate_json_to_toon(kb_dir)
