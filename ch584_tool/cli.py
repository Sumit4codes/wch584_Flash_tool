import click
import sys
from .hex_parser import parse_hex
from .uart_isp import UartISP
from .usb_wrapper import UsbWrapper

@click.group()
def main():
    """WCH584 Flasher Tool"""
    pass

@main.command()
@click.argument('firmware', type=click.Path(exists=True))
@click.option('--method', type=click.Choice(['usb', 'uart']), default='usb', help='Flashing method')
@click.option('--port', help='Serial port for UART mode')
@click.option('--baud', default=115200, help='Baud rate for UART mode')
def flash(firmware, method, port, baud):
    """Flash firmware to the device."""
    click.echo(f"Flashing {firmware} using {method}...")
    
    try:
        if method == 'uart':
            if not port:
                click.echo("Error: --port is required for UART mode.", err=True)
                sys.exit(1)
            isp = UartISP(port, baud)
            isp.connect()
            data = parse_hex(firmware)
            isp.program(data)
            click.echo("Flashing complete.")
        else:
            wrapper = UsbWrapper()
            wrapper.flash(firmware)
            
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@main.command()
@click.option('--method', type=click.Choice(['usb', 'uart']), default='usb', help='Connection method')
@click.option('--port', help='Serial port for UART mode')
def info(method, port):
    """Get device information."""
    try:
        if method == 'uart':
            if not port:
                click.echo("Error: --port is required for UART mode.", err=True)
                sys.exit(1)
            isp = UartISP(port)
            isp.connect()
            info = isp.get_info()
            click.echo(f"Device Info: {info}")
        else:
            wrapper = UsbWrapper()
            click.echo(wrapper.get_info())
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

@main.group()
def eeprom():
    """Manage DataFlash (EEPROM)."""
    pass

@eeprom.command(name='write')
@click.argument('file', type=click.Path(exists=True))
@click.option('--method', type=click.Choice(['usb', 'uart']), default='usb', help='Connection method')
@click.option('--port', help='Serial port for UART mode')
def eeprom_write(file, method, port):
    """Write to EEPROM. File must be exactly 32KB."""
    import os
    
    # Enforce 32KB size limit
    size = os.path.getsize(file)
    if size != 32768:
        click.echo(f"Error: File size must be exactly 32KB (32768 bytes). Current size: {size} bytes.", err=True)
        sys.exit(1)

    if method == 'uart':
        if not port:
            click.echo("Error: --port is required for UART mode.", err=True)
            sys.exit(1)
        try:
            isp = UartISP(port)
            isp.connect()
            with open(file, 'rb') as f:
                data = f.read()
            isp.program_eeprom(data)
            click.echo("Done.")
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)
    else:
        # USB Mode
        try:
            from .usb_isp import UsbISP
            isp = UsbISP()
            click.echo("Connecting to USB device...")
            isp.connect()
            
            with open(file, 'rb') as f:
                data = f.read()
                
            click.echo(f"Writing {len(data)} bytes to EEPROM via USB...")
            isp.program_eeprom(data)
            click.echo("Done.")
            
        except ImportError:
            click.echo("Error: pyusb not installed. Please install it.", err=True)
            sys.exit(1)
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)

@eeprom.command(name='erase')
@click.option('--method', type=click.Choice(['usb', 'uart']), default='usb', help='Connection method')
def eeprom_erase(method):
    """Erase EEPROM."""
    if method == 'uart':
        click.echo("Error: EEPROM erasing via UART is not yet supported.", err=True)
        sys.exit(1)
        
    try:
        wrapper = UsbWrapper()
        click.echo("Erasing EEPROM...")
        wrapper.eeprom_erase()
        click.echo("Done.")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
