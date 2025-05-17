# PhomemoA4

A Python script for printing to the Phomemo M83 A4 thermal printer via Bluetooth.

Compatible with both **Windows** and **Linux**.

---

## Requirements: miniLZO

The [miniLZO](https://www.oberhumer.com/opensource/lzo/) compression library is required.
A sample binary for Windows is included. It was compiled with MinGW GCC but runs from the standard Windows command prompt.

---

## Technical Details

For more information, please see this article:
👉 [Qiita: Detailed Explanation](https://qiita.com/cure_honey/items/1cef2b11291bafbe9d76)

---

## Usage with Bluetooth Socket: `M834.py`

```bash
python -m M834 1280 filename.jpg
# Usage: python -m M834 [printer_width_in_dots] [image_file]
```

---

## Usage without Bluetooth Socket (using rfcomm): `M834_rfcomm.py`

If your Python interpreter does not support the Bluetooth socket module, you can use `M834_rfcomm.py` instead.

1. **In one terminal**, start the Bluetooth RFCOMM connection:

```bash
sudo rfcomm -r connect 0 00:15:D8:63:AD:34 1
# Format: sudo rfcomm -r connect [rfcomm_number] [MAC_address] [channel]
# Note: The -r option is required to allow transmission of 0x0A bytes
```

2. **In another terminal**, set device permissions and run the script:

```bash
sudo chmod 666 /dev/rfcomm0
# or use /dev/rfcomm1 if you connected to rfcomm1

python -m M834_rfcomm 1280 filename.jpg
```
