import subprocess
import shutil

class UsbWrapper:
    def __init__(self):
        self.executable = shutil.which('wchisp')
        if not self.executable:
            raise RuntimeError("wchisp not found. Please install it first (e.g., cargo install wchisp).")

    def _run(self, args):
        cmd = [self.executable] + args
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"wchisp failed: {result.stderr}")
        return result.stdout

    def flash(self, firmware_path):
        """Flashes the firmware using wchisp."""
        print(f"Running: wchisp flash {firmware_path}")
        # wchisp flash <file>
        return self._run(['flash', firmware_path])

    def get_info(self):
        """Gets device info using wchisp."""
        return self._run(['info'])

    def eeprom_write(self, file_path):
        """Writes to EEPROM."""
        # Assuming 'eeprom write' command based on research
        return self._run(['eeprom', 'write', file_path])

    def eeprom_erase(self):
        """Erases EEPROM."""
        return self._run(['eeprom', 'erase'])

