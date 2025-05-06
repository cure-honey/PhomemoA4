import ctypes
# static global variables for miniLZO compression Library call
lzo = ctypes.cdll.LoadLibrary('./minilzo.so')
wk = ctypes.create_string_buffer(16384 * 8)  # 16384 * 64bit pointers
#
# subroutine for sending miniLZO compressed Bitmap data
def send_lzo(bmp_data, sock):
    """
    Compress `bmp_data` with miniLZO and send:
      <3-byte little-endian length><compressed payload>
    Works for any input length.
    """
    buff = ctypes.create_string_buffer(bmp_data, len(bmp_data)) 
    ni = ctypes.c_int(len(buff))
    no_max = len(buff) + len(buff) // 16 + 64 + 3
    out = ctypes.create_string_buffer(no_max)
    no = ctypes.c_int(len(out))
    iret = lzo.lzo1x_1_compress(ctypes.byref(buff), ni, ctypes.byref(
        out), ctypes.byref(no), ctypes.byref(wk))
    # send to printer ; compressed data length + compressed data
    sock.send(no.value.to_bytes(3, byteorder="little") + out[:no.value])
#=============================================================================

# subroutine for printer information
def print_info(socket):
    """
    Print printer info
    """
    US  = b"\x1F"
    socket.send(US + b"\x11\x38") # ?
    tmp38 = socket.recv(3)
    print(tmp38[2])
    socket.send(US + b"\x11\x07") # firmware version
    version = socket.recv(5)
    print(version[2], version[3], version[4])
    socket.send(US + b"\x11\x63")
    socket.send(US + b"\x11\x5e")
    socket.send(US + b"\x11\x09")
    socket.send(US + b"\x11\x56") # serial no.
    serial_number = socket.recv(17)
    print(serial_number[3:])
    socket.send(US + b"\x11\x51") 
    socket.send(US + b"\x11\x08") # energy
    energy = socket.recv(3)
    print(energy[2])
    socket.send(US + b"\x11\x0e") # timer
    timer = socket.recv(3)
    print(timer[2]) # 256*i+9 (sec) ?
    socket.send(US + b"\x11\x12") # paperstate for A4 ?
    tmp12 = socket.recv(3)
    print(tmp12[2])
    socket.send(US + b"\x11\x11") # paperstate
    tmp11 = socket.recv(3)
    print(tmp11[2])
    socket.send(US + b"\x11\x71\x01") # ?
#=============================================================================

def main():
    import sys
    import socket
    from PIL import Image    

    M834 = ("24:12:D8:63:AD:34", 1) #  (MAC address, channel 1)    

    ESC = b"\x1B"
    GS  = b"\x1D"
    US  = b"\x1F"    

    RESET = ESC + b"@"
    BMP   = GS  + b"v" + b"0" + b"\x00"
    ENRGY = US  + b"\x11" + b"\x08"     

    args = sys.argv
    width = 2480 # default  A4 2480 118dots/cm;  1280/912/576 dots 
    print("Connecting...")
    s = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
    if len(args) == 2:
        fn = args[1]
        s.connect(M834)
    else:
        width = args[1]
        fn = args[2]
        s.connect(M834)    

    # info ======== not essential for printing =================
    print_info(s)
    #===========================================================    

    # ESC/POS reset
    s.send(RESET)
    # set concentration
    s.send(US + b"\x11\x02" + b"\x03" ) # concenttration 01, 03, 04
    # set concentration coefficiennt
    s.send(US + b"\x11\x37" + b"\x64" ) # standard 64, M04S 96
    # Phomemo printer reset ? 
    s.send(US + b"\x11\x0b")     # ?
    s.send(US + b"\x11\x35\x01") # phomemo A4 reset ?
    s.send(US + b"\x11\x3c\x00") # ?    

    # PIL 
    # read input file
    image = Image.open(fn)
    if image.width <= image.height:
        image = image.transpose(Image.ROTATE_90)    

    # width M348 2480 dots, M02S 576 dots, M04S 1280/912/576 dots 
    IMAGE_WIDTH_BITS = int(width) # must be multiple of 8
    IMAGE_WIDTH_BYTES = IMAGE_WIDTH_BITS // 8 
    image = image.resize( size=(IMAGE_WIDTH_BITS, int(image.height * IMAGE_WIDTH_BITS / image.width)) )    
    # black&white printer: dithering
    image = image.convert(mode="1")    

    # Print Bitmap 
    print("Data sending...")
    # Header
    s.send(BMP  # these 3 parameters ought to be sent simultaneously  
         + IMAGE_WIDTH_BYTES.to_bytes(2, byteorder="little")
         + image.height.to_bytes(2, byteorder="little"))    
    # Bitmap Body
    nsize = 4096 # data must be sent in 4096byte chunk except the last one
    image_bytes = bytearray()
    for iy in range(image.height):
        for ix in range(int(image.width / 8)):
            byte = 0
            for bit in range(8):
                if (image.getpixel( (ix * 8 + bit, iy) )  == 0 ):
                    byte |= 1 << (7 - bit)
            image_bytes.append(byte)
            # if data accumrates to 4096 then send 
            if (len(image_bytes) == nsize):
                send_lzo(bytes(image_bytes), s)
                image_bytes.clear()
    # send remaining data of less than 4096 bytes
    send_lzo(bytes(image_bytes), s)
    # feed line
    #s.send(ESC + b"\x64\x02")
    #s.send(ESC + b"\x64\x02")
    #
    # wait till print ends 
    s.send(ENRGY) # get battery energy
    a = s.recv(3)
    print("Energy ", int(a[2]), "%")
    # close bluetooth connection 
    s.close()

if __name__ == "__main__":
    main()