import os
import glob
import struct
import re


def unescape(s):
    """Unescape .po file string escape sequences"""
    s = s.replace('\\n', '\n')
    s = s.replace('\\t', '\t')
    s = s.replace('\\\\', '\\')
    s = s.replace('\\"', '"')
    return s


def parse_po(po_path):
    """Parse a .po file and return list of (msgid, msgstr) tuples"""
    entries = []
    current_msgid = []
    current_msgstr = []
    current_msgid_plural = []
    current_msgstr_plural = {}
    state = None  # 'msgid', 'msgstr', 'msgid_plural', 'msgstr_plural'
    plural_idx = 0

    def flush():
        if current_msgid is not None and state in ('msgstr', 'msgstr_plural'):
            mid = unescape(''.join(current_msgid))
            if current_msgid_plural:
                mid_plural = unescape(''.join(current_msgid_plural))
                # For plural forms, join msgid and msgid_plural with \0
                mid = mid + '\x00' + mid_plural
                # Join all msgstr[n] with \x00
                mstr_parts = []
                for i in sorted(current_msgstr_plural.keys()):
                    mstr_parts.append(unescape(''.join(current_msgstr_plural[i])))
                mstr = '\x00'.join(mstr_parts)
            else:
                mstr = unescape(''.join(current_msgstr))
            entries.append((mid, mstr))

    with open(po_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n').rstrip('\r')
            
            # Skip comments
            if line.startswith('#'):
                continue
            
            # Empty line = end of entry
            if not line.strip():
                flush()
                current_msgid = []
                current_msgstr = []
                current_msgid_plural = []
                current_msgstr_plural = {}
                state = None
                continue
            
            if line.startswith('msgid_plural '):
                val = line[len('msgid_plural '):].strip().strip('"')
                current_msgid_plural = [val]
                state = 'msgid_plural'
            elif line.startswith('msgid '):
                val = line[len('msgid '):].strip().strip('"')
                current_msgid = [val]
                current_msgstr = []
                current_msgid_plural = []
                current_msgstr_plural = {}
                state = 'msgid'
            elif line.startswith('msgstr['):
                m = re.match(r'msgstr\[(\d+)\]\s+"(.*)"', line)
                if m:
                    idx = int(m.group(1))
                    val = m.group(2)
                    current_msgstr_plural[idx] = [val]
                    plural_idx = idx
                    state = 'msgstr_plural'
            elif line.startswith('msgstr '):
                val = line[len('msgstr '):].strip().strip('"')
                current_msgstr = [val]
                state = 'msgstr'
            elif line.startswith('"') and line.endswith('"'):
                val = line[1:-1]
                if state == 'msgid':
                    current_msgid.append(val)
                elif state == 'msgid_plural':
                    current_msgid_plural.append(val)
                elif state == 'msgstr':
                    current_msgstr.append(val)
                elif state == 'msgstr_plural':
                    current_msgstr_plural[plural_idx].append(val)

    # Flush last entry
    flush()
    return entries


def write_mo(entries, mo_path):
    """Write a list of (msgid, msgstr) entries to a .mo file"""
    # Sort by msgid (required by MO format for binary search)
    entries.sort(key=lambda x: x[0].encode('utf-8'))

    n = len(entries)
    # Header: magic, revision, nstrings, offset_orig, offset_trans, size_hash, offset_hash
    header_len = 7 * 4
    offset_orig = header_len
    offset_trans = offset_orig + n * 8

    offsets_orig = []
    offsets_trans = []
    ids_data = b''
    strs_data = b''

    data_start = offset_trans + n * 8

    for msgid, msgstr in entries:
        msgid_bytes = msgid.encode('utf-8')
        msgstr_bytes = msgstr.encode('utf-8')
        offsets_orig.append((len(msgid_bytes), data_start + len(ids_data)))
        ids_data += msgid_bytes + b'\x00'
        offsets_trans.append((len(msgstr_bytes), data_start + len(ids_data) + len(strs_data)))

    # Recalculate trans offsets with proper base
    offsets_trans = []
    trans_base = data_start + len(ids_data)
    strs_data = b''
    for msgid, msgstr in entries:
        msgstr_bytes = msgstr.encode('utf-8')
        offsets_trans.append((len(msgstr_bytes), trans_base + len(strs_data)))
        strs_data += msgstr_bytes + b'\x00'

    with open(mo_path, 'wb') as f:
        # Magic number
        f.write(struct.pack('I', 0x950412de))
        # Revision
        f.write(struct.pack('I', 0))
        # Number of strings
        f.write(struct.pack('I', n))
        # Offset of original strings table
        f.write(struct.pack('I', offset_orig))
        # Offset of translated strings table
        f.write(struct.pack('I', offset_trans))
        # Size of hash table (0 = no hash)
        f.write(struct.pack('I', 0))
        # Offset of hash table
        f.write(struct.pack('I', 0))

        # Original strings table
        for length, offset in offsets_orig:
            f.write(struct.pack('II', length, offset))
        # Translated strings table
        for length, offset in offsets_trans:
            f.write(struct.pack('II', length, offset))

        # String data
        f.write(ids_data)
        f.write(strs_data)


if __name__ == '__main__':
    po_files = glob.glob("locales/*/LC_MESSAGES/unobot.po")
    for po in po_files:
        mo = po.replace(".po", ".mo")
        print(f"Compiling {po} -> {mo}")
        entries = parse_po(po)
        write_mo(entries, mo)
    print(f"Done! Compiled {len(po_files)} locale files.")
