import os
import zipfile

def create_zip():
    project_dir = os.path.dirname(os.path.abspath(__file__))
    zip_filename = os.path.abspath(os.path.join(project_dir, "..", "it-service-request-system.zip"))

    exclude_dirs = {'.git', '__pycache__', '.pytest_cache', '.venv', 'venv', '.idea', '.vscode'}
    exclude_files = {'.DS_Store', 'it_service_system.db'}

    print(f"Packaging project into: {zip_filename}")
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(project_dir):
            dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.endswith('.egg-info')]
            for file in files:
                if file in exclude_files or file.endswith('.pyc') or file.endswith('.pyo'):
                    continue
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, os.path.join(project_dir, ".."))
                zipf.write(full_path, rel_path)
                print(f"  + Added {rel_path}")

    print(f"\nSuccessfully created ZIP archive: {zip_filename} ({os.path.getsize(zip_filename):,} bytes)")

if __name__ == "__main__":
    create_zip()
