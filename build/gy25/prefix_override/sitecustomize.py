import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/ni3nayka/Документы/GitHub/IRS-1_sber_hack_2026/install/gy25'
