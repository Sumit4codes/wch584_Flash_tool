# DataFlash (EEPROM) Flashing Details

This document explains the technical implementation of DataFlash (EEPROM) programming for the WCH CH584 in this tool. Unlike the generic `wchisp` tool, this project uses a custom, native Python implementation to ensure strict compliance with the CH584's specific memory layout and size requirements.

## 1. Memory Map & Addressing

The WCH CH584 microcontroller has distinct memory regions for Code (Firmware) and Data (EEPROM).

| Region | Size | Start Address | End Address | Description |
| :--- | :--- | :--- | :--- | :--- |
| **CodeFlash** | 448KB | `0x00000000` | `0x0006FFFF` | Stores the main application firmware. |
| **DataFlash** | **32KB** | **`0x00070000`** | `0x00077FFF` | Non-volatile storage for user data (EEPROM). |
| **Bootloader** | 24KB | `0x00078000` | `0x0007DFFF` | System bootloader (DO NOT TOUCH). |
| **InfoFlash** | 8KB | `0x0007E000` | `0x0007FFFF` | Configuration and chip info. |

### Why Custom Implementation?
The standard `wchisp` tool treats the CH584 as having a larger writable region (often 96KB) which overlaps with the Bootloader and InfoFlash. Writing a full 96KB file could corrupt the bootloader, bricking the device.

**This tool strictly targets the 32KB DataFlash region starting at `0x00070000`.**

## 2. The Protocol (WCH ISP)

The tool communicates with the chip using the WCH ISP (In-System Programming) protocol. This protocol is consistent across USB and UART interfaces.

### Command Structure
The core command used for writing is `CMD_WRITE` (`0xA5`).

**Packet Format:**
```
[CMD] [LEN] [ADDRESS] [DATA] [CHECKSUM]
```

*   **CMD**: `0xA5` (Write Command)
*   **LEN**: Length of the data payload (excluding header).
*   **ADDRESS**: 4-byte Little Endian address (e.g., `00 00 07 00` for `0x00070000`).
*   **DATA**: The actual bytes to write (max ~56 bytes per packet).
*   **CHECKSUM**: `(CMD + LEN + Sum(DATA)) & 0xFF`

## 3. Flashing Process (Step-by-Step)

When you run `ch584-flash eeprom write data.bin`, the following occurs:

### Step 1: Validation
The tool first checks the file size.
```python
if os.path.getsize(file) != 32768:
    raise Error("File size must be exactly 32KB")
```
This ensures you are providing exactly enough data to fill the DataFlash, no more, no less.

### Step 2: Connection
*   **USB Mode**: Uses `pyusb` to find the device (VID: `0x4348`, PID: `0x55e0`) and claims the interface.
*   **UART Mode**: Uses `pyserial` to open the COM port at 115200 baud.

### Step 3: ISP Key (Unlock)
For USB mode, the chip requires an "ISP Key" to unlock write operations. The tool sends a specific sequence (usually 30 bytes of `0x00`) using command `0xA3`.

### Step 4: Chunking and Writing
The 32KB file is too large to send in one packet. The tool splits it into **56-byte chunks**.

**Loop Logic:**
1.  **Calculate Address**: `Current Address = Base Address (0x00070000) + Offset`
2.  **Prepare Packet**:
    *   Pack the 32-bit address into 4 bytes (Little Endian).
    *   Append the 56 bytes of data.
3.  **Send Command**: Transmit `0xA5` + `Payload`.
4.  **Wait**: The tool waits for the USB/UART transfer to complete.

### Code Reference (`usb_isp.py`)

```python
def program_eeprom(self, data):
    start_addr = 0x00070000  # <--- HARDCODED TARGET
    
    chunk_size = 56
    for i in range(0, len(data), chunk_size):
        sub_chunk = data[i:i+chunk_size]
        current_addr = start_addr + i
        
        # Create Payload: [Address (4 bytes)] + [Data (56 bytes)]
        addr_bytes = struct.pack('<I', current_addr)
        payload = addr_bytes + sub_chunk
        
        # Send Write Command (0xA5)
        self._send_packet(CMD_WRITE, payload)
```

## 4. Safety Mechanisms

1.  **Size Enforcement**: By rejecting files != 32KB, we prevent underflow (leaving garbage) or overflow (writing into Bootloader).
2.  **Hardcoded Address**: The start address `0x00070000` is hardcoded in the Python driver, ensuring writes always begin at the correct DataFlash offset.
3.  **Native Driver**: By bypassing `wchisp` for this specific operation, we avoid any "auto-padding" or "smart" features that might misunderstand the CH584's specific memory layout.
