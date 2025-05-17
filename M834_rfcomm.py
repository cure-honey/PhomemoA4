import ctypes

# static global variables for miniLZO compression Library call
lzo = ctypes.cdll.LoadLibrary('./minilzo.so')
wk = ctypes.create_string_buffer(16384 * 8)  # 16384 * 64bit pointers

# subroutine for sending miniLZO compressed Bitmap data
def send_lzo(bmp_data, sock):
    buff = ctypes.create_string_buffer(bmp_data, len(bmp_data))
    ni = ctypes.c_int(len(buff))
    no_max = len(buff) + len(buff) // 16 + 64 + 3
    out = ctypes.create_string_buffer(no_max)
    no = ctypes.c_int(len(out))
    iret = lzo.lzo1x_1_compress(ctypes.byref(buff), ni, ctypes.byref(out), ctypes.byref(no), ctypes.byref(wk))
    sock.write(no.value.to_bytes(3, byteorder="little") + out[:no.value])

# subroutine for printer information
def print_info(sock):
    US = b"\x1F"
    sock.write(US + b"\x11\x38")
    tmp38 = sock.read(3)
    print(tmp38[2])
    sock.write(US + b"\x11\x07")
    version = sock.read(5)
    print(version[2], version[3], version[4])
    sock.write(US + b"\x11\x63")
    sock.write(US + b"\x11\x5e")
    sock.write(US + b"\x11\x09")
    sock.write(US + b"\x11\x56")
    serial_number = sock.read(17)
    print(serial_number[3:])
    sock.write(US + b"\x11\x51")
    sock.write(US + b"\x11\x08")
    energy = sock.read(3)
    print(energy[2])
    sock.write(US + b"\x11\x0e")
    timer = sock.read(3)
    print(timer[2])
    sock.write(US + b"\x11\x12")
    tmp12 = sock.read(3)
    print(tmp12[2])
    sock.write(US + b"\x11\x11")
    tmp11 = sock.read(3)
    print(tmp11[2])
    sock.write(US + b"\x11\x71\x01")

def main():
    import sys
    from PIL import Image

    RFCOMM_DEVICE = "/dev/rfcomm0"
    ESC = b"\x1B"
    GS = b"\x1D"
    US = b"\x1F"

    RESET = ESC + b"@"
    BMP = GS + b"v" + b"0" + b"\x00"
    ENRGY = US + b"\x11" + b"\x08"

    args = sys.argv
    width = 2480
    fn = None

    if len(args) == 2:
        fn = args[1]
    else:
        width = int(args[1])
        fn = args[2]

    print("Connecting via RFCOMM_DEVICE...")

    try:
        with open(RFCOMM_DEVICE, "rb+", buffering=0) as s:
            print_info(s)

            s.write(RESET)
            s.write(US + b"\x11\x02" + b"\x03")
            s.write(US + b"\x11\x37" + b"\x64")
            s.write(US + b"\x11\x0b")
            s.write(US + b"\x11\x35\x01")
            s.write(US + b"\x11\x3c\x00")

            image = Image.open(fn)
            if image.width <= image.height:
                image = image.transpose(Image.ROTATE_90)

            IMAGE_WIDTH_BITS = int(width)
            IMAGE_WIDTH_BYTES = IMAGE_WIDTH_BITS // 8
            image = image.resize(size=(IMAGE_WIDTH_BITS, int(image.height * IMAGE_WIDTH_BITS / image.width)))
            image = image.convert(mode="1")

            print("Data sending...")
            s.write(BMP +
                    IMAGE_WIDTH_BYTES.to_bytes(2, byteorder="little") +
                    image.height.to_bytes(2, byteorder="little"))

            nsize = 4096
            image_bytes = bytearray()
            for iy in range(image.height):
                for ix in range(int(image.width / 8)):
                    byte = 0
                    for bit in range(8):
                        if (image.getpixel((ix * 8 + bit, iy)) == 0):
                            byte |= 1 << (7 - bit)
                    image_bytes.append(byte)
                    if len(image_bytes) == nsize:
                        send_lzo(bytes(image_bytes), s)
                        image_bytes.clear()
            if image_bytes:
                send_lzo(bytes(image_bytes), s)

            s.write(ENRGY)
            a = s.read(3)
            print("Energy", int(a[2]), "%")

    except FileNotFoundError:
        print(f"Error: {RFCOMM_DEVICE} not found.")
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    main()
