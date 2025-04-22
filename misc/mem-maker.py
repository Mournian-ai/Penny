import json

def create_jsonl_from_textfile(input_txt_path, output_jsonl_path):
    """Convert a text file into a clean JSONL file."""
    try:
        with open(input_txt_path, "r", encoding="utf-8") as infile:
            raw_lines = infile.readlines()

        cleaned_lines = []
        for line in raw_lines:
            line = line.strip()  # Remove leading/trailing whitespace
            if not line:
                continue  # Skip blank lines
            # Remove leading/trailing quotes
            if line.startswith('"') and line.endswith('"'):
                line = line[1:-1]
            # Final cleanup
            line = line.strip()
            if line:
                cleaned_lines.append(line)

        if not cleaned_lines:
            print("❌ No valid memories found. Check your input file!")
            return

        with open(output_jsonl_path, "w", encoding="utf-8") as outfile:
            for memory in cleaned_lines:
                memory_item = {
                    "memory": memory,
                    "category": "likes_dislikes",
                    "source": "seed_data"
                }
                json_line = json.dumps(memory_item)
                outfile.write(json_line + "\n")

        print(f"✅ Successfully created {output_jsonl_path} with {len(cleaned_lines)} memories.")

    except Exception as e:
        print(f"❌ Error creating JSONL: {e}")

if __name__ == "__main__":
    input_file = "memories.txt"         # <<< your memory list
    output_file = "memories.jsonl"       # <<< clean output
    create_jsonl_from_textfile(input_file, output_file)
