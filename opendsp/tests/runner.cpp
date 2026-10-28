// SPDX-License-Identifier: BSD-2-Clause
#include <teakra/teakra.h>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <iterator>
#include <vector>

static std::vector<unsigned char> read(const char *path) {
    std::ifstream file(path, std::ios::binary);
    return {std::istreambuf_iterator<char>(file), {}};
}

int main(int argc, char **argv) {
    if (argc != 4) return 2;
    auto image = read(argv[1]), expected = read(argv[2]);
    if (image.size() < 52 || expected.size() % 2 || std::memcmp(image.data(), "\177ELF", 4)) return 2;
    auto get32 = [&](unsigned offset) {
        std::uint32_t value;
        std::memcpy(&value, image.data()+offset, 4);
        return value;
    };
    auto get16 = [&](unsigned offset) {
        std::uint16_t value;
        std::memcpy(&value, image.data()+offset, 2);
        return value;
    };
    Teakra::Teakra dsp{Teakra::UserConfig{}};
    dsp.Reset();
    for (unsigned i=0; i<get16(44); ++i) {
        unsigned ph=get32(28)+i*get16(42);
        if (ph+32>image.size()) return 2;
        if (get32(ph)!=1) continue;
        unsigned offset=get32(ph+4), address=get32(ph+8);
        unsigned bytes=get32(ph+16), memory=get32(ph+20);
        unsigned target=address>=0x10000000 ? 0x40000+address-0x10000000 : address;
        if (offset+bytes>image.size() || bytes>memory || target+memory>0x80000) return 2;
        std::memset(dsp.GetDspMemory()+target,0,memory);
        std::memcpy(dsp.GetDspMemory()+target,image.data()+offset,bytes);
    }
    auto words = reinterpret_cast<const std::uint16_t *>(dsp.GetDspMemory() + 0x40000);
    std::uint64_t steps = 0;
    while (words[0x3000] != 0x600d && steps < 3000000) {
        dsp.Run(1);
        ++steps;
    }
    unsigned errors = 0, count = expected.size()/2;
    bool completed = words[0x3000] == 0x600d;
    if (words[0x3003] != count) ++errors;
    if (words[0x3002] + count > 0x10000) return 2;
    std::ofstream actual(argv[3], std::ios::binary);
    for (unsigned i = 0; i < count; ++i) {
        unsigned want = expected[2*i] | (unsigned(expected[2*i+1]) << 8);
        unsigned got = words[words[0x3002] + i];
        actual.put(got & 255);
        actual.put(got >> 8);
        if (want != got) {
            if (errors < 24) std::fprintf(stderr, "word=%u got=%04x expected=%04x\n", i, got, want);
            ++errors;
        }
    }
    std::printf("{\"completed\":%s,\"comparisons\":%u,\"errors\":%u,\"steps\":%llu}\n",
                completed ? "true" : "false", count, errors, (unsigned long long)steps);
    return !completed || errors ? 1 : 0;
}
