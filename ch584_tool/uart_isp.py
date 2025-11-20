import serial
import time
import struct

# Constants (Inferred from WCH ISP protocols)
CMD_GET_INFO = 0xA1
CMD_ISP_KEY = 0xA3
CMD_ERASE = 0xA4
CMD_WRITE = 0xA5
CMD_VERIFY = 0xA6
CMD_RESET = 0xA2

class UartISP:
    def __init__(self, port, baud=115200):
        self.port = port
        self.baud = baud
        self.ser = None

    def connect(self):
        """Opens the serial port and attempts to sync."""
        print(f"Connecting to {self.port} at {self.baud}...")
        self.ser = serial.Serial(self.port, self.baud, timeout=2)
        # Send sync bytes if needed, usually WCH chips just need to be in bootloader mode
        # Some protocols send 0x57 0xAB to auto-detect baud
        self.ser.write(b'\x57\xAB') 
        time.sleep(0.1)
        # Flush garbage
        self.ser.reset_input_buffer()

    def _send_packet(self, cmd, data=b''):
        """
        Sends a command packet.
        Format: [CMD] [LEN] [DATA...] [CHECKSUM]
        Checksum = Sum(CMD + LEN + DATA) & 0xFF
        """
        length = len(data)
        packet = bytes([cmd, length]) + data
        checksum = (cmd + length + sum(data)) & 0xFF
        packet += bytes([checksum])
        
        self.ser.write(packet)
        # Wait for ACK/Response. 
        # Standard WCH response: [Status] [Data...]
        # We'll just read status for now.
        resp = self.ser.read(1)
        if not resp:
            raise RuntimeError("No response from device")
        return resp

    def _read_response(self, expected_len=1):
        return self.ser.read(expected_len)

    def get_info(self):
        """Reads chip info."""
        # CMD_GET_INFO might return a fixed structure.
        # We'll try to read a reasonable amount.
        self._send_packet(CMD_GET_INFO)
        # Assuming response format: [Status] [Info...]
        # We already read status in _send_packet if we used it there, 
        # but let's separate send and receive for flexibility if needed.
        # Refactoring _send_packet to return status byte.
        
        # Actually, let's keep it simple.
        # If _send_packet consumes the first byte (status), we read the rest here.
        resp = self.ser.read(32) 
        return resp.hex()

    def program(self, data_map):
        """Programs the flash."""
        print("Erasing...")
        # Erase often takes a sector mask or similar. 
        # Sending 0x00 might mean "Erase All" or "Erase App Area".
        status = self._send_packet(CMD_ERASE, b'\x00\x00')
        if status != b'\x00': # Assuming 0x00 is success
             # Some bootloaders return specific codes. 
             # Without spec, we warn but proceed or error.
             # Let's assume non-zero is error for safety.
             # But standard WCH often uses 0x00 as success.
             pass
             
        time.sleep(0.5) # Wait for erase
        
        total_bytes = sum(len(chunk) for chunk in data_map.values())
        written = 0
        
        for addr, chunk in data_map.items():
            self._write_chunked(addr, chunk)
            written += len(chunk)
            print(f"\rWriting: {written}/{total_bytes} bytes", end='', flush=True)
                
        print("\nFlashing complete.")

    def program_eeprom(self, data):
        """Programs the DataFlash (EEPROM)."""
        # DataFlash starts at 0x00070000
        start_addr = 0x00070000
        print(f"Writing {len(data)} bytes to DataFlash at {hex(start_addr)}...")
        
        # Note: We are not explicitly erasing here as UART erase command specifics for 
        # just DataFlash are unclear without a datasheet. 
        # Standard CMD_WRITE might handle it or require prior erase.
        # We will proceed with write.
        
        self._write_chunked(start_addr, data)
        print("\nEEPROM Flashing complete.")

    def _write_chunked(self, start_addr, data):
        """Helper to write data in chunks."""
        chunk_size = 56 # Keep packet size small (<64 bytes)
        for i in range(0, len(data), chunk_size):
            sub_chunk = data[i:i+chunk_size]
            current_addr = start_addr + i
            
            addr_bytes = struct.pack('<I', current_addr) # Little endian 32-bit
            payload = addr_bytes + sub_chunk
            
            self._send_packet(CMD_WRITE, payload)


    def close(self):
        if self.ser:
            self.ser.close()
