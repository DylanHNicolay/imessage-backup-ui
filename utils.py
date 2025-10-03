from pathlib import Path

def convert_date(date: int) -> int:
    """ Convert an epoch timestamp from iPhone to a standard UNIX timestamp. """
    # Apple starts epoch at 2001-01-01
    epoch = 978307200

    if date > epoch * 1000**2:
        # After iOS11, epoch needs to be converted from nanoseconds to seconds and adjusted 31 years
        return date // 1000**3 + epoch
    else:
        # Before iOS11, epoch is already in seconds
        return date + epoch

def read_file(file) -> str:
        with open(file, 'r') as f:
            output = f.read()
        return output

def get_archive_format(filename: Path) -> str:
    """
    Get the archive format from the file extension.
    Supported formats: zip, tar, gztar, bztar, xztar
    """
    extension = filename.suffix.lower()
    
    formats = {
        '.zip': 'zip',
        '.tar': 'tar',
        '.tgz': 'gztar',
        '.tar.gz': 'gztar',
        '.tbz': 'bztar',
        '.tar.bz2': 'bztar',
        '.txz': 'xztar',
        '.tar.xz': 'xztar',
    }
    
    if extension not in formats:
        raise ValueError(f"Unsupported archive format: {extension}. Supported formats are: {', '.join(formats.keys())}")
    
    return formats[extension]