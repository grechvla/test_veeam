import os
import shutil
import time
import hashlib
import argparse
import logging


# MD5 hash of file
def get_file_md5(filepath):
    hash_md5 = hashlib.md5()
    with open(filepath, 'rb') as f:
        for part in iter(lambda: f.read(4096), b""):
            hash_md5.update(part)
    return hash_md5.hexdigest()


# Synchronize the replica folder with the source folder.
def sync_folders(source, replica):
    for rootdir, dirs, files in os.walk(source):
        # Calculate the relative path for the current directory
        relative_path = os.path.relpath(rootdir, source)
        replica_dir = os.path.join(replica, relative_path)

        # Check for existence of replica directory
        if not os.path.exists(replica_dir):
            os.makedirs(replica_dir)
            logging.info(f"Created directory: {replica_dir}")

        # Copy files

        for file_name in files:
            source_file = os.path.join(rootdir, file_name)
            replica_file = os.path.join(replica_dir, file_name)

            # Check if the file needs to be copied
            if not os.path.exists(replica_file) or get_file_md5(source_file) != get_file_md5(replica_file):
                try:
                    shutil.copy2(source_file, replica_file)  # copy with metadata
                    logging.info(f"Copied file from {source_file} to {replica_file}")
                except Exception as e:
                    logging.error(f"Error copying file from {source_file} to {replica_file}: {e}")

    # Delete files and directories that no longer exist in the source folder
    for rootdir, dirs, files in os.walk(replica, topdown=False):
        relative_path = os.path.relpath(rootdir, replica)
        source_dir = os.path.join(source, relative_path)

        for file_name in files:
            replica_file = os.path.join(rootdir, file_name)
            source_file = os.path.join(source_dir, file_name)

            if not os.path.exists(source_file):
                try:
                    os.remove(replica_file)
                    logging.info(f"Deleted file: {replica_file}")
                except Exception as e:
                    logging.error(f"Error deleting file {replica_file}: {e}")

        if not os.path.exists(source_dir):
            try:
                shutil.rmtree(rootdir)
                logging.info(f"Deleted directory: {rootdir}")
            except Exception as e:
                logging.error(f"Error deleting empty directory {rootdir}: {e}")


# Check if any paths do not exist
def unexist_path(paths, exclude=['interval', 'logfile']):
    for name, path in paths.items():
        if not os.path.exists(path) and name not in exclude:
            return True, path
    return False, None


def main():
    parser = argparse.ArgumentParser(description='Synchronize two folders.')
    parser.add_argument('source', help='Path to the source folder')
    parser.add_argument('replica', help='Path to the replica folder')
    parser.add_argument('interval', type=int, help='Synchronization interval in seconds')
    parser.add_argument('logfile', help='Path to the log file')

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%d/%m/%Y %I:%M:%S',
        level=logging.INFO,
        handlers=[logging.FileHandler(filename=args.logfile, mode='a+', encoding='utf-8'), logging.StreamHandler()],
    )
    is_status, name_path = unexist_path(vars(args))
    if is_status:
        logging.info(f"Path: {name_path} does not exist")
        return

    while True:
        try:
            sync_folders(args.source, args.replica)
            logging.info(f"Synchronization complete - Waiting {args.interval} seconds...")
            time.sleep(args.interval)
        except KeyboardInterrupt:
            logging.info("Program stopped")
            break
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            break

if __name__ == "__main__":
    main()
