import os
import hashlib
from collections import defaultdict

EXCLUDED_DIRS = {
    '.git', 'node_modules', '__pycache__', '.venv', 'venv', 
    '.pytest_cache', 'dist', 'build', '.aevum', '.vscode'
}

def get_sha256(filepath):
    h = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(65536):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        return f"ERR:{e}"

def scan_workspace(root_dir):
    files_by_hash = defaultdict(list)
    files_by_name = defaultdict(list)
    all_files = []

    for root, dirs, files in os.walk(root_dir):
        # Exclude directories
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS and not d.startswith('.git')]
        
        for f in files:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, root_dir).replace('\\', '/')
            size = os.path.getsize(full_path)
            file_hash = get_sha256(full_path)
            
            file_info = {
                'rel_path': rel_path,
                'basename': f,
                'size': size,
                'hash': file_hash
            }
            all_files.append(file_info)
            files_by_hash[file_hash].append(file_info)
            files_by_name[f.lower()].append(file_info)

    # Exact duplicates (same hash, more than 1 file)
    exact_duplicates = {h: flist for h, flist in files_by_hash.items() if len(flist) > 1 and not h.startswith('ERR')}

    # Name collisions / same basename across different folders
    name_collisions = {name: flist for name, flist in files_by_name.items() if len(flist) > 1}

    print(f"Total files inspected (excluding deps/caches): {len(all_files)}")
    print(f"Total exact duplicate groups (D1): {len(exact_duplicates)}")
    exact_dup_file_count = sum(len(flist) for flist in exact_duplicates.values())
    print(f"Total files involved in exact duplicates: {exact_dup_file_count}")
    print(f"Total same-basename collision groups: {len(name_collisions)}")

    return all_files, exact_duplicates, name_collisions

if __name__ == '__main__':
    workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
    print(f"Scanning workspace: {workspace_root}")
    all_files, exact_dups, name_collisions = scan_workspace(workspace_root)
    
    print("\n--- SAMPLE EXACT DUPLICATE GROUPS (D1) ---")
    for i, (h, flist) in enumerate(list(exact_dups.items())[:15]):
        print(f"\nGroup {i+1} [Hash: {h[:12]}..., Size: {flist[0]['size']} bytes]:")
        for f in flist:
            print(f"  - {f['rel_path']}")
