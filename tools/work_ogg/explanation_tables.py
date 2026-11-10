"""Typed master text tables. Expl contains counted uint16 lists, never C strings."""
import struct

def u16(b, p=0):
    return struct.unpack_from('<H', b, p)[0]

def u32(b, p=0):
    return struct.unpack_from('<I', b, p)[0]

def explanation_records(table):
    assert table[:4] == b'Expl'
    size, count = struct.unpack_from('<II', table, 4)
    assert 12 + count * 4 <= size <= len(table)
    result = []
    for i in range(count):
        at = u32(table, 12 + i * 4)
        assert at % 2 == 0 and 12 + count * 4 <= at < size
        n = u16(table, at)
        assert at + 2 + n * 2 <= size
        result.append(bytes(table[at:at + 2 + n * 2]))
    return result

def pack_explanations(records):
    prefix = 12 + len(records) * 4
    pool = bytearray()
    positions = {}
    offsets = []
    for value in records:
        assert len(value) == 2 + u16(value) * 2
        if value not in positions:
            positions[value] = prefix + len(pool)
            pool.extend(value)
        offsets.append(positions[value])
    out = bytearray(b'Expl' + struct.pack('<II', 0, len(records)))
    out.extend(struct.pack('<%dI' % len(offsets), *offsets))
    out.extend(pool)
    out.extend(bytes(-len(out) % 4))
    struct.pack_into('<I', out, 4, len(out))
    assert explanation_records(out) == records
    return bytes(out)

def text_records(table):
    assert table[:4] in (b'Strg', b'Sent'), 'Only actual text tables may use NUL termination'
    size, count = struct.unpack_from('<II', table, 4)
    assert 12 + count * 4 <= size <= len(table)
    return [bytes(table[u32(table, 12 + i * 4):table.index(0, u32(table, 12 + i * 4)) + 1]) for i in range(count)]

def compact_text(table):
    values = text_records(table)
    prefix = 12 + len(values) * 4
    pool = bytearray()
    positions = {}
    for value in sorted(set(values), key=lambda v: (-len(v), v)):
        at = pool.find(value)
        if at < 0:
            at = len(pool)
            pool.extend(value)
        positions[value] = prefix + at
    out = bytearray(table[:4] + struct.pack('<II', 0, len(values)))
    out.extend(struct.pack('<%dI' % len(values), *(positions[v] for v in values)))
    out.extend(pool)
    out.extend(bytes(-len(out) % 4))
    struct.pack_into('<I', out, 4, len(out))
    assert text_records(out) == values
    return bytes(out)

def table_records(table):
    return explanation_records(table) if table[:4] == b'Expl' else text_records(table)
