import spidev, sys

spi = spidev.SpiDev()
spi.open(0,0)
#sys.stdin.reconfigure(encoding='latin-1')
#sys.stdout.reconfigure(encoding='latin-1')

#20MHz
spi.max_speed_hz = 20*1000*1000
#spi.mode = 0b00

READ_ID = 0x9f
READ_RS = 0x05
CHIP_ERASE = 0x60
PAGE_READ = 0x3
PAGE_WRITE = 0x2
WRITE_ENABLE = 0x6
WRITE_DISABLE = 0x4
W25Q128_MID = 0xEF
W25Q128_DID = 0x4018
FLASH_PAGE_SIZE = 256
FLASH_TOTAL_SIZE = 16 * 1024 * 1024

def __init__(bus, dev, speed):
    try:
        print("Device:/dev/spidev{}.{}, speed:{}".format(bus, dev, speed))
    except IOError:
        raise("Did not find SPI device:/dev/spidev{}.{}".format(bus, dev))
def __del__():
    spi.close()

def probe():
    try:
        data = spi.xfer([READ_ID, 0, 0, 0])
        return data[1], data[2] << 8 | data[3]
    except IndexError:
        return 0, 0

def erase():
    spi.xfer([WRITE_ENABLE])
    spi.xfer([CHIP_ERASE])
    while get_rs() & 0x1:
        pass

def get_rs():
    return spi.xfer([READ_RS, 0])[1]

def read_page(page):
    address = page * FLASH_PAGE_SIZE
    cmd = [PAGE_READ, (address >> 16) & 0xff, (address >> 8) & 0xff, address & 0xff]
    return bytearray(spi.xfer(cmd + [0] * FLASH_PAGE_SIZE)[4:])

def read_chip():
    data = bytearray()
    for page in range(FLASH_TOTAL_SIZE / FLASH_PAGE_SIZE):
        data += read_page(page)
    return data

def write_page(page, data):
    address = page * FLASH_PAGE_SIZE
    cmd = [PAGE_WRITE, (address >> 16) & 0xff, (address >> 8) & 0xff, address & 0xff]
    spi.xfer([WRITE_ENABLE])
    spi.xfer(cmd + data)
    while get_rs() & 0x1:
        pass

def write_chip(data, verify=False):
    if len(data) != FLASH_TOTAL_SIZE:
        print("Data size error!")
        return False
    erase()
    data = list(data)
    for page in range(FLASH_TOTAL_SIZE / FLASH_PAGE_SIZE):
        start = page * FLASH_PAGE_SIZE
        write_buffer = map(ord, data[start: start + FLASH_PAGE_SIZE])
        write_page(page, write_buffer)
        if verify and bytearray(write_buffer) != read_page(page):
            print("Verify error, page:{}".format(page))
            return False
    return True

if __name__ == "__main__":
    mid, device_id = probe()
    print("Manufacturer ID:0x{0:X}, Device ID:0x{1:X}".format(mid, device_id))
    if mid != W25Q128_MID or device_id != W25Q128_DID:
        print("SPI Flash is not Winbond W25Q128")
        sys.exit()
    with open("16allones", "rb") as fp:
        write_chip(fp.read())
    with open("16onesverify", "wb") as fp:
        fp.write(read_chip())
