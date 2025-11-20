# WCH584 Flasher Tool

A command-line interface (CLI) tool for flashing WCH CH584 microcontrollers. This tool supports both USB and UART flashing methods, with a specific focus on reliable DataFlash (EEPROM) programming.

## Features

*   **USB Flashing**:
    *   Wraps the robust `wchisp` tool for firmware flashing.
    *   **Native USB Driver** for DataFlash (EEPROM) operations, enforcing strict 32KB size limits for safety.
*   **UART Flashing**:
    *   Native Python implementation of the WCH ISP protocol.
    *   Supports Firmware and DataFlash (EEPROM) writing.
*   **DataFlash (EEPROM) Support**:
    *   Strict enforcement of **32KB (32,768 bytes)** file size to match CH584 specifications.
    *   Prevents accidental overwrites of Bootloader/InfoFlash regions.
*   **Cross-Platform**: Written in Python, runs on Linux, Windows, and macOS.

## Installation

### Prerequisites
*   Python 3.6+
*   `wchisp` (Optional, for USB firmware flashing): [Install wchisp](https://github.com/ch32-rs/wchisp)

### Install from Source
1.  Clone the repository:
    ```bash
    git clone https://github.com/Sumit4codes/wch584_Flash_tool.git
    cd wch584_Flash_tool
    ```

2.  Install dependencies:
    ```bash
    pip install .
    ```
    Or for development:
    ```bash
    pip install -e .
    ```

## Usage

The tool provides a main command `ch584-flash` with several subcommands.

### 1. Flash Firmware (CodeFlash)

**USB Mode:**
```bash
ch584-flash flash firmware.hex --method usb
```

**UART Mode:**
Requires a USB-to-UART adapter connected to the ISP pins (usually UART1).
```bash
ch584-flash flash firmware.hex --method uart --port /dev/ttyUSB0
```

### 2. Flash DataFlash (EEPROM)

**Note:** The tool strictly enforces a **32KB** file size for EEPROM writes.

**USB Mode (Native Driver):**
```bash
ch584-flash eeprom write data_32k.bin --method usb
```

**UART Mode:**
```bash
ch584-flash eeprom write data_32k.bin --method uart --port /dev/ttyUSB0
```

### 3. Get Device Info

```bash
ch584-flash info --method usb
ch584-flash info --method uart --port /dev/ttyUSB0
```

## Project Structure

*   `ch584_tool/`: Main package directory.
    *   `cli.py`: CLI entry point using `click`.
    *   `usb_isp.py`: Native USB ISP driver implementation (using `pyusb`).
    *   `uart_isp.py`: Native UART ISP driver implementation (using `pyserial`).
    *   `usb_wrapper.py`: Wrapper for external `wchisp` tool.
    *   `hex_parser.py`: Intel Hex file parser.

## License

MIT License
