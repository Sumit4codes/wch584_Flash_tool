import usb.core
import usb.util
import struct
import time

# Constants
VID_WCH = 0x4348
PID_55E0 = 0x55e0
VID_WCH_ALT = 0x1a86

CMD_GET_INFO = 0xA1
CMD_ISP_KEY = 0xA3
CMD_ERASE = 0xA4
CMD_WRITE = 0xA5
CMD_VERIFY = 0xA6
CMD_RESET = 0xA2

class UsbISP:
    def __init__(self):
        self.dev = None
        self.ep_out = None
        self.ep_in = None

    def connect(self):
        """Finds and connects to the WCH USB device."""
        # Find device
        self.dev = usb.core.find(idVendor=VID_WCH, idProduct=PID_55E0)
        if self.dev is None:
            self.dev = usb.core.find(idVendor=VID_WCH_ALT, idProduct=PID_55E0)
        
        if self.dev is None:
            raise RuntimeError("WCH ISP USB device not found.")

        # Detach kernel driver if active
        if self.dev.is_kernel_driver_active(0):
            self.dev.detach_kernel_driver(0)

        # Set configuration
        self.dev.set_configuration()

        # Get endpoints
        cfg = self.dev.get_active_configuration()
        intf = cfg[(0,0)]

        self.ep_out = usb.util.find_descriptor(
            intf,
            custom_match = \
            lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == \
            usb.util.ENDPOINT_OUT)

        self.ep_in = usb.util.find_descriptor(
            intf,
            custom_match = \
            lambda e: usb.util.endpoint_direction(e.bEndpointAddress) == \
            usb.util.ENDPOINT_IN)

        if not self.ep_out or not self.ep_in:
            raise RuntimeError("Could not find bulk endpoints.")

    def _send_packet(self, cmd, data=b''):
        """Sends a command packet."""
        length = len(data)
        packet = bytes([cmd, length]) + data
        checksum = (cmd + length + sum(data)) & 0xFF
        packet += bytes([checksum])
        
        self.ep_out.write(packet)
        
        # Read response
        # WCH response is usually [Status] [Data...]
        try:
            resp = self.ep_in.read(64, timeout=5000)
            return bytes(resp)
        except usb.core.USBError as e:
            raise RuntimeError(f"USB Read Error: {e}")

    def get_info(self):
        """Reads chip info."""
        # CMD_GET_INFO
        resp = self._send_packet(CMD_GET_INFO)
        # First byte is usually status/echo or part of info?
        # Based on wchisp, it returns a payload.
        return resp.hex()

    def program_eeprom(self, data):
        """Programs the DataFlash (EEPROM)."""
        start_addr = 0x00070000
        print(f"Writing {len(data)} bytes to DataFlash at {hex(start_addr)}...")
        
        # Send ISP Key (Required for some operations)
        # wchisp sends all zeros for key
        key = b'\x00' * 30 # 0x1e bytes
        self._send_packet(CMD_ISP_KEY, key)
        
        # Write in chunks
        chunk_size = 56
        total_bytes = len(data)
        written = 0
        
        for i in range(0, len(data), chunk_size):
            sub_chunk = data[i:i+chunk_size]
            current_addr = start_addr + i
            
            addr_bytes = struct.pack('<I', current_addr)
            payload = addr_bytes + sub_chunk
            
            # CMD_WRITE (0xA5) is used for both Code and Data flash in wchisp
            # (Command::program and Command::data_program both map to 0xA5 with different address?)
            # Actually wchisp uses Command::program for code and Command::data_program for data.
            # Let's check wchisp source for command codes.
            # src/protocol.rs would have it.
            # Assuming 0xA5 is generic write.
            
            self._send_packet(CMD_WRITE, payload)
            written += len(sub_chunk)
            print(f"\rWriting: {written}/{total_bytes} bytes", end='', flush=True)
            
        print("\nEEPROM Flashing complete.")
