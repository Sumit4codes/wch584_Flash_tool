from intelhex import IntelHex

def parse_hex(file_path):
    """
    Parses an Intel Hex file and returns a dictionary of address: data chunks.
    """
    ih = IntelHex(file_path)
    segments = ih.segments()
    data_map = {}
    
    for start, end in segments:
        # Read data for this segment
        # end is exclusive in intelhex segments
        size = end - start
        data = ih.tobinarray(start=start, size=size)
        data_map[start] = data
        
    return data_map
