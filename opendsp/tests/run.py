#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-2-Clause
"""Run native compiler regressions."""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess

HERE = Path(__file__).resolve().parent
CC = os.environ.get('TEAK_CC', 'clang')
LD = os.environ.get('TEAK_LD', 'ld.lld')
TEAKRA = Path(os.environ.get('TEAKRA', 'teakra')).resolve()
OPUS = Path(os.environ.get('OPUS_SOURCE', 'opus')).resolve()
TREMOR = Path(os.environ.get('TREMOR_SOURCE', str(OPUS.parent/'tremor'))).resolve()
OGG = Path(os.environ.get('OGG_SOURCE', str(OPUS.parent/'libogg'))).resolve()

BUILD = Path(os.environ.get('TEAK_TEST_BUILD', str(HERE/'build'))).resolve()
VALUES = [-32768, -32767, -1024, -1, 0, 1, 1024, 32766, 32767]


def command(args, name, cwd=None):
    result = subprocess.run(list(map(str, args)), capture_output=True, text=True, cwd=cwd)
    (BUILD / name).write_text('COMMAND: ' + ' '.join(map(str, args)) + '\n' + result.stdout + result.stderr)
    if result.returncode:
        raise RuntimeError(f'{name}: exit {result.returncode}; see {BUILD / name}')
    return result.stdout


def comparisons(simple=False):
    source = '''
__attribute__((noinline)) u16 compare(s16 a, s16 b) {
    return (a < b) | ((a <= b) << 1) | ((a > b) << 2) |
           ((a >= b) << 3) | ((a == b) << 4) | ((a != b) << 5);
}
__attribute__((noinline)) u16 compare_unsigned(u16 a, u16 b) {
    return (a < b) | ((a <= b) << 1) | ((a > b) << 2) |
           ((a >= b) << 3) | ((a == b) << 4) | ((a != b) << 5);
}
__attribute__((noinline)) s16 minimum(s16 a, s16 b) { return a < b ? a : b; }
__attribute__((noinline)) s16 maximum(s16 a, s16 b) { return a > b ? a : b; }
__attribute__((noinline)) s16 sign(s16 a) { return a < 0 ? -1 : a > 0; }
'''
    if simple:
        source = '\n'.join(f'__attribute__((noinline)) u16 cmp_{i}(s16 a,s16 b) {{ return a {op} b; }}' for i, op in enumerate(['<','<=','>','>=','==','!=']))
    body, expected = [], []
    def cmp(a, b):
        return sum(int(value) << bit for bit, value in enumerate([a < b, a <= b, a > b, a >= b, a == b, a != b]))
    for a in VALUES:
        body.append(f'out[n++] = sign(input[{VALUES.index(a)}]);')
        expected.append(-1 if a < 0 else int(a > 0))
        for b in VALUES:
            args = f'input[{VALUES.index(a)}], input[{VALUES.index(b)}]'
            if simple:
                body.extend(f'out[n++] = cmp_{i}({args});' for i in range(6))
                expected.extend([a < b, a <= b, a > b, a >= b, a == b, a != b])
                continue
            body += [f'out[n++] = compare({args});', f'out[n++] = compare_unsigned({args});',
                     f'out[n++] = minimum({args});', f'out[n++] = maximum({args});']
            expected += [cmp(a, b), cmp(a & 65535, b & 65535), min(a, b), max(a, b)]
    if simple:
        source += '\n__attribute__((noinline)) s16 sign(s16 a) { return a < 0 ? -1 : a > 0; }\n'
    return source, body, expected


def sort_case():
    source = '''
void silk_insertion_sort_increasing_all_values_int16(s16 *, int);
'''
    body, expected = [], []
    for values in [VALUES, list(reversed(VALUES)), [1000]*9, [30000-i*1900 for i in range(9)]]:
        offset = len(expected)
        body.extend(f'out[{offset+i}] = {v};' for i, v in enumerate(values))
        body.append(f'silk_insertion_sort_increasing_all_values_int16((s16 *)out+{offset}, 9);')
        expected += sorted(values)
    return source, body, expected


def nlsf_case():
    source = 'void silk_NLSF_stabilize(s16 *, const s16 *, int);\ns16 nlsf[16], delta[17];\n'
    body, expected = [], []
    body.extend(f'delta[{i}]={32+(i & 3)};' for i in range(17))
    for c in range(8):
        values=[]
        for i in range(16):
            v = 200+i*1900 if c==0 else 30000-i*1900 if c==1 else 1000 if c==2 else 32760-i*4 if c==3 else -100+i*8 if c==4 else (i*3779+c*791)&32767
            values.append(v)
        body.extend(f'nlsf[{i}]={v}; out[n++] = nlsf[{i}];' for i,v in enumerate(values))
        body.append('silk_NLSF_stabilize(nlsf, delta, 16);')
        body.extend(f'out[n++] = nlsf[{i}];' for i in range(16))
        expected.extend([0]*32)
    return source, body, expected


def clz_case():
    values16 = {0, 0xffff}
    values32 = {0, 0xffffffff}
    values40 = {0, 0xffffffffff}
    for width, values in [(16, values16), (32, values32), (40, values40)]:
        mask = (1 << width)-1
        for bit in range(width):
            values.update([(1 << bit)-1, 1 << bit, ((1 << bit)+1) & mask])
        state = 0x1f123bb5
        for _ in range(128):
            state = (state*6364136223846793005+1442695040888963407) & mask
            values.add(state)
    source = '''
__attribute__((noinline)) u16 leading_zeroes(u16 low_word, u16 high_word) {
    u32 value = ((u32)high_word << 16) | low_word;
    return value ? __builtin_clz(value) : 32;
}
u16 leading_zeroes40(u16, u16, u16);
u16 leading_zeroes16(u16);
'''
    inputs, body, expected = [], [], []
    for width, values in [(16, values16), (32, values32), (40, values40)]:
        for value in sorted(values):
            index = len(inputs)
            inputs.extend([(value >> shift) & 65535 for shift in [0, 16, 32]])
            argument_count = 1 if width == 16 else 2 if width == 32 else 3
            arguments = ','.join(f'bit_inputs[{index+i}]' for i in range(argument_count))
            function = 'leading_zeroes' if width == 32 else f'leading_zeroes{width}'
            body.append(f'out[n++] = {function}({arguments});')
            expected.append(width-value.bit_length())
    source += '\nvolatile u16 bit_inputs[] = {' + ','.join(map(str, inputs)) + '};\n'
    return source, body, expected


def silk_math_case():
    source = '''
void silk_sum_sqr_shift(s32 *, int *, const s16 *, int);
void silk_bwexpander_32(s32 *, int, s32);
s32 silk_lin2log(s32);
s16 samples[128];
s32 coefficients[16], energy;
int scaling;
'''
    body, expected = [], []
    coefficients = [-2147483648, -2147483647, -1073741824, -65536, -32768, -1,
                    0, 1, 32767, 65535, 65536, 1073741823, 2147483647, 768123, -10234567, 23987654]
    for case, length in enumerate([1, 2, 3, 8, 17, 63, 127, 128]):
        values = [VALUES[(index+case) % len(VALUES)] for index in range(length)]
        body.extend(f'samples[{index}]={value};' for index, value in enumerate(values))
        body.append(f'silk_sum_sqr_shift(&energy, &scaling, samples, {length});')
        body.extend(['out[n++]=energy;', 'out[n++]=(u32)energy >> 16;', 'out[n++]=scaling;'])
        expected.extend([0]*3)
        body.extend(f'coefficients[{index}]={value};' for index, value in enumerate(coefficients))
        body.append(f'silk_bwexpander_32(coefficients, 16, {[0, 1, 16384, 32767, 32768, 65534, 65535, 65536][case]});')
        for index in range(16):
            body.extend([f'out[n++]=coefficients[{index}];', f'out[n++]=(u32)coefficients[{index}] >> 16;'])
            expected.extend([0]*2)
    for value in [0, 1, 2, 3, 15, 16, 17, 32767, 32768, 65535, 65536, 1073741823, 2147483647]:
        body.append(f'out[n++]=silk_lin2log({value});')
        expected.append(0)
    return source, body, expected


def multiply_pairs():
    values = [0, 1, 2, 0x7fff, 0x8000, 0xffff, 0x10000, 0x7fffffff,
              0x80000000, 0xffffffff, 0x100000000, 0x7fffffffff,
              0x8000000000, 0xffffffffff]
    pairs = [(left, right) for left in values for right in values]
    state = 0x17abc985
    for _ in range(96):
        state = (state*6364136223846793005+1442695040888963407) & 0xffffffffff
        left = state
        state = (state*6364136223846793005+1442695040888963407) & 0xffffffffff
        pairs.append((left, state))
    return pairs


def multiply_case():
    source = '''
__attribute__((noinline)) u32 multiply32(u32 left, u32 right) { return left*right; }
__attribute__((noinline)) u16 multiply16(u16 left, u16 right) { return left*right; }
u16 multiply40(const u16 *, const u16 *, u16);
u16 multiply_signed40(const u16 *, const u16 *, u16);
'''
    inputs, body, expected = [], [], []
    for left, right in multiply_pairs():
        index = len(inputs)
        inputs.extend([(value >> shift) & 65535 for value in [left, right] for shift in [0, 16, 32]])
        body.append(f'out[n++] = multiply16(multiply_inputs[{index}], multiply_inputs[{index+3}]);')
        expected.append((left*right) & 65535)
        body.append(f'product = multiply32(((u32)multiply_inputs[{index+1}] << 16) | multiply_inputs[{index}], '
                    f'((u32)multiply_inputs[{index+4}] << 16) | multiply_inputs[{index+3}]);')
        body.extend(['out[n++] = product;', 'out[n++] = product >> 16;'])
        expected.extend([((left & 0xffffffff)*(right & 0xffffffff) >> shift) & 65535 for shift in [0, 16]])
        for shift in [0, 16, 32]:
            body.append(f'out[n++] = multiply40((const u16 *)multiply_inputs+{index}, '
                        f'(const u16 *)multiply_inputs+{index+3}, {shift});')
            expected.append((((left*right) & 0xffffffffff) >> shift) & 65535)
            body.append(f'out[n++] = multiply_signed40((const u16 *)multiply_inputs+{index}, '
                        f'(const u16 *)multiply_inputs+{index+3}, {shift});')
            signed_left=((left & 65535) ^ 0x8000)-0x8000
            expected.append((((signed_left*right) & 0xffffffffff) >> shift) & 65535)
    source += '\nvolatile u16 multiply_inputs[] = {' + ','.join(map(str, inputs)) + '};\n'
    body.insert(0, 'u32 product;')
    return source, body, expected


def high_product_case():
    source = '''
u16 high_unsigned40(const u16 *,const u16 *,u16);
u16 high_signed40(const u16 *,const u16 *,u16);
u16 divide_unsigned40(const u16 *,u16);
u16 divide_signed40(const u16 *,u16);
u16 wide_constant40(u16,u16);
'''
    inputs,body,expected=[],[],[]
    mask=(1<<40)-1
    def signed(value):
        return (value^(1<<39))-(1<<39)
    for left,right in multiply_pairs():
        index=len(inputs)
        inputs.extend((value>>shift)&65535 for value in [left,right] for shift in [0,16,32])
        signed_left=signed(left)
        quotient=abs(signed_left)//5
        if signed_left<0:
            quotient=-quotient
        values=[(left*right)>>40,(signed_left*signed(right))>>40,left//5,quotient]
        for function,value in zip(['high_unsigned40','high_signed40','divide_unsigned40','divide_signed40'],values):
            for shift in [0,16,32]:
                arguments=f'(const u16 *)high_inputs+{index},'
                if function.startswith('high_'):
                    arguments+=f'(const u16 *)high_inputs+{index+3},'
                body.append(f'out[n++]={function}({arguments}{shift});')
                expected.append(((value&mask)>>shift)&65535)
    source+='volatile u16 high_inputs[]={'+','.join(map(str,inputs))+'};\n'
    constants=sorted({left for left,right in multiply_pairs()})
    for index,value in enumerate(constants):
        for shift in [0,16,32]:
            body.append(f'out[n++]=wide_constant40({index},{shift});')
            expected.append((value>>shift)&65535)
    return source,body,expected


def callback_case():
    source='''
typedef u32 (*callback_function)(u32,u32,u32,u32,u32,u32);
struct callback_record {u16 guard; callback_function function; u16 end;};
_Static_assert(sizeof(callback_function)==4,"Program pointer width");
_Static_assert(sizeof(u16 *)==2,"Data pointer width");
_Static_assert(sizeof(struct callback_record)==12,"Callback record size");
_Static_assert(__builtin_offsetof(struct callback_record,function)==4,"Callback offset");
__attribute__((noinline,section(".callbacks_far"))) u32 callback_first(u32 first,u32 second,u32 third,u32 fourth,u32 fifth,u32 sixth) {
    return (first+second)^third^((fourth+fifth)<<3)^(sixth>>5);
}
static __attribute__((noinline,section(".callbacks_far"))) u32 callback_second(u32 first,u32 second,u32 third,u32 fourth,u32 fifth,u32 sixth) {
    return (first^second)+(third-fourth)+fifth*17u+sixth;
}
u32 callback_nested(u32,u32,u32,u32,u32,u32);
callback_function volatile callbacks[]={callback_first,callback_second,callback_nested};
struct callback_record volatile callback_records[]={
    {0x1234,callback_first,0x2345},{0x3456,callback_second,0x4567},
    {0x5678,callback_nested,0x6789}
};
__attribute__((noinline)) callback_function select_callback(u16 index) {
    if (index==0) return callback_first;
    if (index==1) return callback_second;
    return callback_nested;
}
__attribute__((noinline)) u32 callback_nested(u32 first,u32 second,u32 third,u32 fourth,u32 fifth,u32 sixth) {
    callback_function function=callbacks[0];
    return function(sixth,fifth,fourth,third,second,first)+first*13u;
}
__attribute__((noinline)) u32 invoke_callback(callback_function function,u32 first,u32 second,u32 third,u32 fourth,u32 fifth,u32 sixth) {
    volatile u16 guards[3]={0x1234,0x2345,0x3456};
    u32 result=function(first,second,third,fourth,fifth,sixth);
    return result^guards[0]^guards[1]^guards[2];
}
'''
    values=[0,1,0x7fff,0x8000,0xffff,0x7fffffff,0x80000000,0xffffffff,0x12345678]
    source+='volatile u32 callback_inputs[]={'+','.join(str(value)+'u' for value in values)+'};\n'
    body,expected=['u32 result;'],[]
    mask=0xffffffff
    def first(a,b,c,d,e,f):
        return ((a+b)&mask)^c^(((d+e)<<3)&mask)^(f>>5)
    def second(a,b,c,d,e,f):
        return ((a^b)+c-d+e*17+f)&mask
    def nested(a,b,c,d,e,f):
        return (first(f,e,d,c,b,a)+a*13)&mask
    for case in range(len(values)):
        indices=[(case+offset*3)%len(values) for offset in range(6)]
        arguments=','.join(f'callback_inputs[{index}]' for index in indices)
        for table in ['callbacks','callback_records','returned']:
            for index,function in enumerate([first,second,nested]):
                pointer=f'select_callback({index})' if table=='returned' else f'{table}[{index}]'+('.function' if table=='callback_records' else '')
                body.extend([f'result=invoke_callback({pointer},{arguments});','out[n++]=result;','out[n++]=result >> 16;'])
                value=function(*(values[position] for position in indices))^0x1234^0x2345^0x3456
                expected.extend([value&65535,value>>16])
                if table=='callback_records':
                    body.extend([f'out[n++]=callback_records[{index}].guard;',f'out[n++]=callback_records[{index}].end;'])
                    expected.extend([[0x1234,0x2345],[0x3456,0x4567],[0x5678,0x6789]][index])
    return source,body,expected


def byte_memory_case():
    values=[(index*7919+0x9abcdeff)&0xffffffff for index in range(256)]
    source='''
typedef unsigned char u8;
typedef signed char s8;
__attribute__((noinline)) u16 read_byte(const u8 *input,u16 index) {return input[index];}
__attribute__((noinline)) s16 read_signed_byte(const s8 *input,u16 index) {return input[index];}
__attribute__((noinline)) u32 read_wide_byte(const u8 *input,u16 index) {return input[index];}
__attribute__((noinline)) s32 read_wide_signed_byte(const s8 *input,u16 index) {return input[index];}
__attribute__((noinline)) void write_byte(u8 *output,u16 index,u32 value) {output[index]=value;}
__attribute__((noinline)) const u8 *read_text(void) {return (const u8 *)"Silk";}
u8 byte_output[258];
const u8 byte_text[]="Vorbis/Opus";
'''
    source+='const u8 byte_table[]={'+','.join(map(str,range(256)))+'};\n'
    source+='const u8 repeated_bytes[]={'+','.join(['127']*17)+'};\n'
    source+='volatile u32 byte_inputs[]={'+','.join(str(value)+'u' for value in values)+'};\n'
    body,expected=['u32 result;'],[]
    for value in range(256):
        body.extend([f'out[n++]=read_byte(byte_table,{value});',f'out[n++]=read_signed_byte((const s8 *)byte_table,{value});',
                     f'result=read_wide_byte(byte_table,{value});','out[n++]=result;','out[n++]=result >> 16;',
                     f'result=read_wide_signed_byte((const s8 *)byte_table,{value});','out[n++]=result;','out[n++]=result >> 16;'])
        signed=(value^128)-128
        expected.extend([value,signed&65535,value,0,signed&65535,(signed>>16)&65535])
    body.extend(['write_byte(byte_output,0,0x12);','write_byte(byte_output,257,0x34);'])
    body.extend(f'write_byte(byte_output,{index+1},byte_inputs[{index}]);' for index in range(256))
    body.extend(f'out[n++]=read_byte(byte_output,{index});' for index in range(258))
    expected.extend([0x12,*[value&255 for value in values],0x34])
    for table,values in [('repeated_bytes',[127]*17),('byte_text',list(b'Vorbis/Opus\0')),('read_text()',list(b'Silk\0'))]:
        body.extend(f'out[n++]=read_byte({table},{index});' for index in range(len(values)))
        expected.extend(values)
    return source,body,expected


def word_memory_case():
    source = """
__attribute__((noinline)) u32 sum_unsigned_words(const u16 *input,u16 count) {
    u32 result=0;
    while(count--) result+=*input++;
    return result;
}
__attribute__((noinline)) s32 sum_signed_words(const s16 *input,u16 count) {
    s32 result=0;
    while(count--) result+=*input++;
    return result;
}
__attribute__((noinline)) void copy_low_words(u16 *output,const u32 *input,u16 count) {
    while(count--) *output++=*input++;
}
u16 word_values[32],word_results[34];
u32 wide_values[32];
"""
    body,expected=['u32 result;'],[]
    for count in [0,1,2,3,7,16,31,32]:
        values=[(index*19317+count*8191)&65535 for index in range(32)]
        body.extend(f'word_values[{index}]={value}; wide_values[{index}]={((index*7919+0x1234)<<16|value)&0xffffffff}u;' for index,value in enumerate(values))
        body.extend([f'result=sum_unsigned_words(word_values,{count});','out[n++]=result;','out[n++]=result >> 16;',f'result=sum_signed_words((const s16 *)word_values,{count});','out[n++]=result;','out[n++]=result >> 16;'])
        unsigned=sum(values[:count]);signed=sum(((value^0x8000)-0x8000) for value in values[:count])&0xffffffff
        expected.extend([unsigned&65535,unsigned>>16,signed&65535,signed>>16])
        body.extend(f'word_results[{index}]=0x7878;' for index in range(34))
        body.extend(['word_results[0]=0x1234;',f'word_results[{count+1}]=0x2345;',f'copy_low_words(word_results+1,wide_values,{count});'])
        body.extend(f'out[n++]=word_results[{index}];' for index in range(count+2))
        expected.extend([0x1234,*values[:count],0x2345])
    return source,body,expected


def interpolate_case():
    source = """
void silk_interpolate(s16 *,const s16 *,const s16 *,int,int);
s16 interpolate_first[16],interpolate_second[16],interpolate_output[18];
"""
    body,expected=[],[]
    for length in [0,1,2,3,7,10,12,16]:
        for coefficient in range(5):
            for index in range(length):
                first=VALUES[(index+coefficient)%len(VALUES)]
                second=VALUES[(length-index+coefficient)%len(VALUES)]
                body.append(f'interpolate_first[{index}]={first}; interpolate_second[{index}]={second};')
            body.extend(f'interpolate_output[{index}]=0x7878;' for index in range(18))
            body.extend(['interpolate_output[0]=0x1234;',f'interpolate_output[{length+1}]=0x2345;',f'silk_interpolate(interpolate_output+1,interpolate_first,interpolate_second,{coefficient},{length});'])
            body.extend(f'out[n++]=interpolate_output[{index}];' for index in range(length+2))
            expected.extend([0]*(length+2))
    return source,body,expected


def calls_case():
    source = """
__attribute__((noinline)) u32 call_words(u32 first,u32 second,u32 third,u32 fourth,u32 fifth,u32 sixth) {
    return (first+fifth)^((second^sixth)<<3)^((third-fourth)>>7);
}
__attribute__((noinline)) u16 call_shorts(u16 first,u16 second,u16 third,u16 fourth,u16 fifth,u16 sixth,u16 seventh) {
    return first+3*second+5*third+7*fourth+11*fifth+13*sixth+17*seventh;
}
__attribute__((noinline)) u32 call_mixed(u16 first,u32 second,s16 third,u16 fourth,u32 fifth,s16 sixth) {
    return ((u32)first<<16)^second^((u32)(s32)third*17u)^((u32)fourth<<1)^fifth^(u32)(s32)sixth;
}
__attribute__((noinline)) u32 call_nested(u32 first,u32 second,u32 third,u32 fourth,u32 fifth,u32 sixth) {
    volatile u16 guards[3]={0x1234,0x2345,0x3456};
    u32 result=call_words(sixth,fifth,fourth,third,second,first);
    result^=call_mixed(first,second,third,fourth,fifth,sixth);
    return result+guards[0]+guards[1]+guards[2];
}
"""
    values=[0,1,0x7fff,0x8000,0xffff,0x7fffffff,0x80000000,0xffffffff,0x12345678]
    source+='volatile u32 call_inputs[]={'+','.join(str(value)+'u' for value in values)+'};\n'
    body,expected=['u32 result;'],[]
    mask=0xffffffff
    def words(first,second,third,fourth,fifth,sixth):
        return ((first+fifth)&mask)^(((second^sixth)<<3)&mask)^(((third-fourth)&mask)>>7)
    def signed_word(value):
        return ((value&65535)^0x8000)-0x8000
    def mixed(first,second,third,fourth,fifth,sixth):
        return ((first&65535)<<16)^second^((signed_word(third)*17)&mask)^((fourth&65535)<<1)^fifth^(signed_word(sixth)&mask)
    for first_index in range(len(values)):
        for second_index in range(len(values)):
            indices=[first_index,second_index]+[(first_index+offset*second_index+offset)%len(values) for offset in range(1,6)]
            arguments=[values[index] for index in indices]
            expression=','.join(f'call_inputs[{index}]' for index in indices[:6])
            results=[words(*arguments[:6]),mixed(*arguments[:6]),(words(*reversed(arguments[:6]))^mixed(*arguments[:6]))+0x1234+0x2345+0x3456]
            for function,value in zip(['call_words','call_mixed','call_nested'],results):
                body.extend([f'result={function}({expression});','out[n++]=result;','out[n++]=result >> 16;'])
                expected.extend([value&65535,(value>>16)&65535])
            body.append('out[n++]=call_shorts('+','.join(f'call_inputs[{index}]' for index in indices)+');')
            expected.append(sum((value&65535)*coefficient for value,coefficient in zip(arguments,[1,3,5,7,11,13,17]))&65535)
    source+='u16 call40(const u16 *,u16);\n'
    wide_values=[0,1,0x7fffffff,0x80000000,0xffffffff,0x7fffffffff,0x8000000000,0xffffffffff]
    state=0x17abc985
    for _ in range(16):
        state=(state*6364136223846793005+1442695040888963407)&0xffffffffff
        wide_values.append(state)
    packed=[]
    for index in range(len(wide_values)):
        arguments=[wide_values[(index+offset*7)%len(wide_values)] for offset in range(6)]
        first,second,third,fourth,fifth,sixth=arguments
        value=((first+fifth)^(second<<13)^(sixth>>17)^(third-fourth))&0xffffffffff
        start=len(packed)
        packed.extend((argument>>shift)&65535 for argument in arguments for shift in [0,16,32])
        for shift in [0,16,32]:
            body.append(f'out[n++]=call40((const u16 *)stack40_inputs+{start},{shift});')
            expected.append((value>>shift)&65535)
    source+='volatile u16 stack40_inputs[]={'+','.join(map(str,packed))+'};\n'
    return source,body,expected


def fft_case(size=60, vector=None):
    source = '''
#include "kiss_fft.h"
extern const opus_int16 eband5ms[];
extern const unsigned char band_allocation[];
#include "static_modes_fixed.h"
kiss_fft_cpx fft_input[FFT_LENGTH], fft_output[FFT_LENGTH];
'''
    source=source.replace('FFT_LENGTH',str(size))
    state='fft_state48000_960_'+str({480:0,240:1,120:2,60:3}[size])
    body, expected = [], []
    for case in (range(5) if vector is None else [vector]):
        for index in range(size):
            real = (1 << 20) if case == 0 and index == 0 else 0 if case == 0 else (
                (32767 if index & 1 else -32768) if case == 1 else
                ((index*7919+case*131071) % 2097152)-1048576)
            imaginary = 0 if case < 2 else ((index*17957+case*65537) % 1048576)-524288
            body.append(f'fft_input[{index}].r={real}; fft_input[{index}].i={imaginary};')
        body.append(f'opus_fft_c(&{state}, fft_input, fft_output);')
        for index in range(size):
            for component in ['r', 'i']:
                body.extend([f'out[n++]=fft_output[{index}].{component};',
                             f'out[n++]=(u32)fft_output[{index}].{component} >> 16;'])
                expected.extend([0, 0])
    return source, body, expected


def mdct_case(size, stride, vector, frames):
    length = size+60
    source = '''
#include "mdct.h"
extern const opus_int16 eband5ms[];
extern const unsigned char band_allocation[];
#include "static_modes_fixed.h"
static const mdct_lookup mdct_state = {
    1920,3,{&fft_state48000_960_0,&fft_state48000_960_1,
    &fft_state48000_960_2,&fft_state48000_960_3},mdct_twiddles960
};
'''
    source += f'kiss_fft_scalar mdct_input[{size*stride+2}], mdct_output[{length+4}]={{0}};\n'
    body = ['u32 sample;']
    body.extend(f'mdct_output[{index}]={((index*19317+7919)%2097152)-1048576};' for index in range(1,length+1))
    body.extend(['mdct_output[0]=0x12345678;',f'mdct_output[{length+1}]=0x23456789;',
                 'mdct_input[0]=0x3456789a;',f'mdct_input[{size*stride+1}]=0x456789ab;'])
    for frame in range(frames):
        if frame:
            body.extend(f'mdct_output[{index+1}]=mdct_output[{size+index+1}];' for index in range(60))
        for index in range(size*stride):
            if index % stride:
                value = ((index*17957+frame*65537)%1048576)-524288
            else:
                position = index//stride
                if vector == 0:
                    value = (1<<20) if position == frame else 0
                elif vector == 1:
                    value = 32767 if (position+frame)&1 else -32768
                elif vector == 5:
                    value = 0
                elif vector == 6:
                    value = 0x3fffffff if (position+frame)&1 else -0x3fffffff
                elif vector == 7:
                    value = ((position+frame)%7)-3
                else:
                    value = ((position*7919+vector*131071+frame*193939)%2097152)-1048576
            body.append(f'mdct_input[{index+1}]={value};')
        shift = {120:3,240:2,480:1,960:0}[size]
        body.append(f'clt_mdct_backward_c(&mdct_state,mdct_input+1,mdct_output+1,window120,120,{shift},{stride},0);')
    body.extend([f'mdct_output[{length+2}]=mdct_input[0];',f'mdct_output[{length+3}]=mdct_input[{size*stride+1}];'])
    for index in range(length+4):
        body.extend([f'sample=(u32)mdct_output[{index}];','out[n++]=sample;','out[n++]=sample >> 16;'])
    return source,body,[0]*(2*(length+4))


def vorbis_mdct_case(size, vector):
    source = '#include "mdct.h"\n' + f's32 vorbis_output[{size+2}]={{0}};\n'
    values = ['0', '(index == 0 ? 1048576 : 0)',
              '(index & 1 ? 1048576 : -1048576)',
              '((index*7919+393213)%2097152)-1048576', '(index&7)-3']
    body = ['u16 index;', 'u32 sample;', 'vorbis_output[0]=0x12345678;',
            f'vorbis_output[{size+1}]=0x23456789;',
            f'for(index=0;index<{size};++index) vorbis_output[index+1]=0x13579bdf;',
            f'for(index=0;index<{size//2};++index) vorbis_output[index+1]={values[vector]};',
            f'mdct_backward({size},vorbis_output+1,vorbis_output+1);',
            f'for(index=0;index<{size+2};++index) {{',
            'sample=(u32)vorbis_output[index];',
            'out[n++]=sample;', 'out[n++]=sample >> 16;', '}']
    return source,body,[0]*(2*(size+2))


def table_words_case():
    source,body,expected=pointers_case()
    source=source.replace('u16 pointer_values[9] = {0x1234,0x2345,0x3456,0x4567,0x5678,0x6789,0x789a,0x89ab,0x9abc};','extern u16 pointer_values[9];')
    source=source.replace('u16 *const pointer_table[] = {pointer_values, pointer_values+1, pointer_values+3, pointer_values+8};','extern u16 *const pointer_table[];')
    source=source.replace('struct pointer_record pointer_records[] = {{0x2345,0x12345678u},{0x3456,0x89abcdefu}};','extern struct pointer_record pointer_records[];')
    source=source.replace('u32 *const record_table[] = {&pointer_records[0].value, &pointer_records[1].value};','extern u32 *const record_table[];')
    body.extend(['out[n++]=read_pointer(4);','out[n++]=read_pointer(5);'])
    expected.extend([0x4567,0x1234])
    source += '\nextern const u16 *const internal_table[];\n__attribute__((noinline)) u16 read_internal(u16 index) {return *internal_table[index];}\n'
    body.extend(f'out[n++]=read_internal({index});' for index in range(4))
    expected.extend([0x1357,0x2468,0x579b,0x2468])
    return source,body,expected


def pointers_case():
    source = """
u16 pointer_values[9] = {0x1234,0x2345,0x3456,0x4567,0x5678,0x6789,0x789a,0x89ab,0x9abc};
u16 *const pointer_table[] = {pointer_values, pointer_values+1, pointer_values+3, pointer_values+8};
struct pointer_record { u16 guard; u32 value; };
struct pointer_record pointer_records[] = {{0x2345,0x12345678u},{0x3456,0x89abcdefu}};
u32 *const record_table[] = {&pointer_records[0].value, &pointer_records[1].value};
__attribute__((noinline)) u16 read_pointer(u16 index) { return *pointer_table[index]; }
__attribute__((noinline)) u32 read_record(u16 index) { return *record_table[index]; }
__attribute__((noinline)) void write_pointer(u16 index, u16 value) { *pointer_table[index]=value; }
"""
    body = [f'out[n++]=read_pointer({index});' for index in range(4)]
    expected = [0x1234,0x2345,0x4567,0x9abc]
    for index, value in enumerate([0x12345678,0x89abcdef]):
        body.extend([f'product=read_record({index});','out[n++]=product;','out[n++]=product >> 16;'])
        expected.extend([value & 65535,value >> 16])
    body.insert(0,'u32 product;')
    body.extend(['write_pointer(1,0x1357);','write_pointer(3,0x2468);'])
    body.extend(f'out[n++]=pointer_values[{index}];' for index in range(9))
    expected.extend([0x1234,0x1357,0x3456,0x4567,0x5678,0x6789,0x789a,0x89ab,0x2468])
    return source, body, expected


def fft_math_case():
    source = """
#include "arch.h"
__attribute__((noinline)) s32 fft_product(s16 coefficient, s32 sample) { return MULT16_32_Q15(coefficient,sample); }
__attribute__((noinline)) s32 fft_scale(s16 coefficient, s32 sample) { return MULT16_32_Q16(coefficient,sample); }
"""
    coefficients=[-32768,-32767,-31164,-28378,-26510,-19261,-16384,-1,0,1,16384,23170,32767]
    samples=[-2147483648,-1048576,-65537,-65536,-32768,-17477,-1,0,1,17476,32767,65535,65536,1048575,2147483647]
    source += 'volatile s16 coefficients[]={' + ','.join(map(str,coefficients)) + '};\n'
    source += 'volatile s32 samples[]={' + ','.join(map(str,samples)) + '};\n'
    body,expected=['s32 product;'],[]
    for i,coefficient in enumerate(coefficients):
        for j,sample in enumerate(samples):
            for function,shift in [('fft_product',15),('fft_scale',16)]:
                body.extend([f'product={function}(coefficients[{i}],samples[{j}]);','out[n++]=product;','out[n++]=(u32)product >> 16;'])
                value=((coefficient*sample) >> shift) & 0xffffffff
                expected.extend([value & 65535,value >> 16])
    return source,body,expected


def bulk_case():
    source = '''
__attribute__((noinline)) u16 local_initializer(u16 index) {
    volatile u16 local_values[3] = {0x1234, 0x2345, 0x3456};
    return local_values[index];
}
'''
    body = [f'out[n++]=local_initializer({index});' for index in range(3)]
    expected = [0x1234, 0x2345, 0x3456]
    source += '\nu16 word_source[16], word_destination[16];\n'
    for count in [1, 2, 3, 4, 7, 8, 12]:
        source += f'__attribute__((noinline)) void copy{count}(u16 *destination, const u16 *input) {{ __builtin_memcpy(destination, input, {count*2}); }}\n'
        values = [(index*19317+count*8191) & 65535 for index in range(16)]
        body.extend(f'word_source[{index}]={value}; word_destination[{index}]=0x7878;' for index, value in enumerate(values))
        body.append(f'copy{count}(word_destination+2, word_source+1);')
        body.extend(f'out[n++]=word_destination[{index}];' for index in range(16))
        expected.extend([0x7878]*2+values[1:count+1]+[0x7878]*(14-count))
    source += '''
__attribute__((noinline)) void fill7(u16 *destination) { __builtin_memset(destination, 0xa5, 14); }
__attribute__((noinline)) void move7(u16 *destination, const u16 *input) { __builtin_memmove(destination, input, 14); }
'''
    body.extend(f'word_destination[{index}]=0x7878;' for index in range(16))
    body.append('fill7(word_destination+2);')
    body.extend(f'out[n++]=word_destination[{index}];' for index in range(16))
    expected.extend([0x7878]*2+[0xa5a5]*7+[0x7878]*7)
    for offset in [1, -1]:
        values = [(index*7919+1023) & 65535 for index in range(16)]
        body.extend(f'word_destination[{index}]={value};' for index, value in enumerate(values))
        destination, origin = (3, 2) if offset > 0 else (2, 3)
        body.append(f'move7(word_destination+{destination}, word_destination+{origin});')
        body.extend(f'out[n++]=word_destination[{index}];' for index in range(16))
        values[destination:destination+7] = values[origin:origin+7]
        expected.extend(values)
    return source, body, expected


def stack_case():
    source = '''
__attribute__((noinline)) void change_short(s16 *value) { *value += 5; }
__attribute__((noinline)) void change_word(u32 *value) { *value ^= 0x13579bdfu; }
__attribute__((noinline)) s16 local_short(s16 value) {
    s16 local_value = value;
    change_short(&local_value);
    return local_value;
}
__attribute__((noinline)) s16 local_array(s16 value) {
    s16 local_values[7];
    u16 index;
    for (index=0; index<7; ++index) local_values[index] = value+index;
    change_short(&local_values[3]);
    return local_values[0]+local_values[3]+local_values[6];
}
__attribute__((noinline)) u32 local_word(u16 low_word, u16 high_word) {
    u32 local_value = ((u32)high_word << 16) | low_word;
    change_word(&local_value);
    return local_value;
}
__attribute__((noinline)) void local_mixed(u16 *result, u16 low_word, u16 high_word) {
    volatile s16 guards[3];
    u32 local_values[2];
    guards[0] = 0x1234;
    guards[1] = 0x2345;
    guards[2] = 0x3456;
    local_values[0] = ((u32)high_word << 16) | low_word;
    local_values[1] = ~local_values[0];
    change_word(&local_values[1]);
    change_short((s16 *)&guards[1]);
    result[0] = guards[0];
    result[1] = guards[1];
    result[2] = guards[2];
    result[3] = local_values[0];
    result[4] = local_values[0] >> 16;
    result[5] = local_values[1];
    result[6] = local_values[1] >> 16;
}
'''
    body, expected = ['u32 product;'], []
    for index, value in enumerate(VALUES):
        body.extend([f'out[n++] = local_short(input[{index}]);',
                     f'out[n++] = local_array(input[{index}]);'])
        expected.extend([value+5, 3*value+14])
        for high_index, high_word in enumerate(VALUES):
            body.append(f'product = local_word(input[{index}],input[{high_index}]);')
            body.extend(['out[n++] = product;', 'out[n++] = product >> 16;'])
            value32 = (((high_word & 65535) << 16) | (value & 65535)) ^ 0x13579bdf
            expected.extend([value32 & 65535, value32 >> 16])
            body.append(f'local_mixed(out+n, input[{index}],input[{high_index}]); n+=7;')
            original = ((high_word & 65535) << 16) | (value & 65535)
            changed = ((~original) & 0xffffffff) ^ 0x13579bdf
            expected.extend([0x1234, 0x234a, 0x3456, original & 65535,
                             original >> 16, changed & 65535, changed >> 16])
    return source, body, expected


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--opt', default='-O2')
    parser.add_argument('--label')
    parser.add_argument('--case', choices=['comparisons', 'simple', 'sort', 'nlsf', 'silk_math', 'clz', 'multiply', 'stack', 'bulk', 'fft', 'pointers', 'fft_math', 'table_words', 'calls', 'interpolate', 'word_memory', 'mdct', 'high_product', 'callback', 'byte_memory', 'vorbis_mdct'], default='comparisons')
    parser.add_argument('--max-steps',type=int,default=3000000)
    parser.add_argument('--vorbis-size',type=int,choices=[64,128,256,512,1024,2048,4096,8192],default=64)
    parser.add_argument('--vorbis-vector',type=int,choices=range(5),default=0)
    parser.add_argument('--fft-size',type=int,choices=[60,120,240,480],default=60)
    parser.add_argument('--fft-vector',type=int,choices=range(5),default=0)
    parser.add_argument('--mdct-size',type=int,choices=[120,240,480,960],default=120)
    parser.add_argument('--mdct-stride',type=int,choices=[1,2,4,8],default=1)
    parser.add_argument('--mdct-vector',type=int,choices=range(8),default=0)
    parser.add_argument('--mdct-frames',type=int,choices=[1,2],default=2)
    args = parser.parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)
    factories = {'nlsf': nlsf_case, 'sort': sort_case, 'clz': clz_case, 'silk_math': silk_math_case, 'multiply': multiply_case, 'stack': stack_case, 'bulk': bulk_case, 'fft': fft_case, 'pointers': pointers_case, 'fft_math': fft_math_case, 'table_words': table_words_case, 'calls': calls_case, 'interpolate': interpolate_case, 'word_memory': word_memory_case, 'high_product': high_product_case}
    if args.max_steps < 1:
        parser.error('Step limit must be positive')
    if args.case == 'vorbis_mdct':
        functions,body,expected=vorbis_mdct_case(args.vorbis_size,args.vorbis_vector)
    elif args.case == 'byte_memory':
        functions,body,expected=byte_memory_case()
    elif args.case == 'callback':
        functions,body,expected=callback_case()
    elif args.case == 'mdct':
        if args.mdct_size*args.mdct_stride>960:
            parser.error('MDCT input exceeds test memory')
        functions,body,expected=mdct_case(args.mdct_size,args.mdct_stride,args.mdct_vector,args.mdct_frames)
    elif args.case == 'fft':
        functions, body, expected = fft_case(args.fft_size,args.fft_vector)
    elif args.case in factories:
        functions, body, expected = factories[args.case]()
    else:
        functions, body, expected = comparisons(args.case == 'simple')
    stem = args.case + (str(args.fft_size)+'v'+str(args.fft_vector) if args.case=='fft' else '') + args.opt.replace('-', '')
    if args.case == 'mdct':
        stem=f'mdct{args.mdct_size}s{args.mdct_stride}v{args.mdct_vector}f{args.mdct_frames}'+args.opt.replace('-','')
    if args.case == 'vorbis_mdct':
        stem=f'vorbis_mdct{args.vorbis_size}v{args.vorbis_vector}'+args.opt.replace('-','')
    out_declaration=f'u16 out[{len(expected)}];'
    if args.case == 'mdct':
        out_declaration=f'extern u16 out[{len(expected)}] __attribute__((alias("mdct_output")));'
    if args.case == 'vorbis_mdct':
        out_declaration=f'extern u16 out[{len(expected)}] __attribute__((alias("vorbis_output")));'
    mailbox=0x7000 if args.case=='vorbis_mdct' else 0x3000
    source = BUILD / (stem + '.c')
    source.write_text('#include "kernels.h"\n#ifdef HOST_REFERENCE\n#include <stdio.h>\n#endif\n' + functions + '\nvolatile s16 input[] = {' + ','.join(map(str, VALUES)) + '};\n' +
                      out_declaration+'\nint main(void) { u16 n=0;\n' + '\n'.join(body) +
                      f'\n#ifdef HOST_REFERENCE\nfwrite(out,2,{len(expected)},stdout);\n#else\n((volatile u16 *){mailbox})[2]=(u16)(unsigned)out;\n((volatile u16 *){mailbox})[3]={len(expected)};\n((volatile u16 *){mailbox})[0]=0x600d;\n#endif\nreturn 0; }}\n')
    flags = ['--target=teak', '-march=teak', args.opt, '-ffreestanding', '-fno-builtin', '-fno-strict-aliasing',
             '-ffunction-sections', '-fdata-sections', '-nostdlib', '-integrated-as', '-I'+str(HERE)]
    upstream_flags = ['-DFIXED_POINT', '-DOPUS_BUILD', '-DHAVE_STDINT_H', '-DHAVE_INTTYPES_H']
    includes = ['-I'+str(HERE/'include'), *['-I'+str(OPUS/p) for p in ['include','celt','silk','.']]]
    if args.case in ['fft','fft_math','mdct']:
        upstream_flags += ['-DNONTHREADSAFE_PSEUDOSTACK']
        flags += upstream_flags + includes
    vorbis_includes=['-I'+str(HERE/'config'),'-I'+str(OGG/'include'),'-I'+str(TREMOR)]
    if args.case == 'vorbis_mdct':
        flags += ['-fwrapv', '-DBYTE_ORDER=4321', '-DLITTLE_ENDIAN=1234',
                  '-DBIG_ENDIAN=4321', '-I'+str(HERE/'include'), *vorbis_includes]
    objects = []
    for path in [HERE / 'crt0.s', HERE.parent/'runtime/indirect.s', source]:
        obj = BUILD / (path.stem+'.o')
        command([CC, *flags, '-c', path, '-o', obj], path.stem+'.log')
        objects.append(obj)
    command([CC, *flags, '-S', source, '-o', BUILD / (stem+'.s')], stem+'-asm.log')
    if args.case in ['clz', 'multiply', 'table_words', 'calls', 'high_product']:
        ir_source = HERE/('high_product40.ll' if args.case == 'high_product' else 'calls40.ll' if args.case == 'calls' else 'pointers.ll' if args.case == 'table_words' else 'clz40.ll' if args.case == 'clz' else 'multiply40.ll')
        obj = BUILD/(ir_source.stem+'.o')
        command([CC, '--target=teak', '-O2', '-integrated-as', '-c', ir_source, '-o', obj], ir_source.stem+'.log')
        objects.append(obj)
    if args.case in ['sort', 'nlsf', 'silk_math', 'fft', 'interpolate','mdct']:
        units = ['kiss_fft','mdct'] if args.case == 'mdct' else ['interpolate'] if args.case == 'interpolate' else ['kiss_fft'] if args.case == 'fft' else ['sum_sqr_shift', 'bwexpander_32', 'lin2log'] if args.case == 'silk_math' else ['sort'] + (['NLSF_stabilize'] if args.case == 'nlsf' else [])
        directory = OPUS/('celt' if args.case in ['fft','mdct'] else 'silk')
        for name in units:
            obj = BUILD / (name+'.o')
            command([CC, *flags, *upstream_flags, *includes, '-c', directory/(name+'.c'), '-o', obj], name+'.log')
            objects.append(obj)
        if args.case in ['nlsf', 'silk_math', 'fft', 'interpolate','mdct']:
            host = BUILD/'host-reference'
            command(['cc', '-O2', '-fwrapv', '-DHOST_REFERENCE', '-I'+str(HERE), *upstream_flags,
                     *['-I'+str(OPUS/p) for p in ['include','celt','silk','.']], source,
                     *[directory/(name+'.c') for name in units], '-ffunction-sections', '-fdata-sections',
                     '-Wl,--gc-sections', '-lm', '-o', host], 'host.log')
            reference_bytes = subprocess.check_output([host])
    if args.case == 'vorbis_mdct':
        obj=BUILD/'vorbis_mdct.o'
        command([CC,*flags,'-c',TREMOR/'mdct.c','-o',obj],'vorbis_mdct.log')
        objects.append(obj)
        host=BUILD/'host-reference'
        command(['cc','-O2','-fwrapv','-fno-strict-aliasing','-DHOST_REFERENCE',
                 '-I'+str(HERE),*vorbis_includes,source,TREMOR/'mdct.c','-o',host],'host.log')
        reference_bytes=subprocess.check_output([host])
    elf, cdc = BUILD/(stem+'.elf'), BUILD/(stem+'.cdc')
    linker_script=HERE/'link.ld'
    if args.case=='callback':
        linker_script=BUILD/'callback.ld'
        linker_script.write_text((HERE/'link.ld').read_text().replace('    . = 0x10002000;',
            '    . = 0x20000;\n    .callbacks_far : { *(.callbacks_far) } :prog\n    . = 0x10002000;'))
    if args.case=='vorbis_mdct':
        linker_script=BUILD/'vorbis_mdct.ld'
        linker_script.write_text((HERE/'link.ld').read_text().replace('0x10006000','0x1000e000'))
    command([LD, '--gc-sections', '-T', linker_script, *objects, '-o', elf], 'link.log')
    runner = BUILD/'runner'
    if not runner.exists() or runner.stat().st_mtime < (HERE/'runner.cpp').stat().st_mtime:
        command(['g++', '-O2', '-std=c++17', '-I'+str(TEAKRA/'include'), HERE/'runner.cpp',
                 TEAKRA/'b/src/libteakra.a', '-o', runner], 'runner.log')
    reference = BUILD/(stem+'.pcm')
    reference.write_bytes(reference_bytes if args.case in ['nlsf', 'silk_math', 'fft', 'interpolate','mdct','vorbis_mdct'] else struct.pack('<'+'H'*len(expected), *[v & 65535 for v in expected]))
    result = subprocess.run([str(runner), str(elf), str(reference), str(BUILD/(stem+'-actual.pcm')),str(args.max_steps),str(mailbox)], capture_output=True, text=True)
    (BUILD/(stem+'-emulate.log')).write_text(result.stdout+result.stderr)
    if not result.stdout.strip():
        raise RuntimeError(f'Emulation failed; see {BUILD / (stem+"-emulate.log")}')
    if args.label:
        if not args.label.replace('-', '').replace('_', '').isalnum():
            raise SystemExit('Invalid label')
        evidence = json.loads(result.stdout)
        if args.case=='fft':
            evidence.update(fft_size=args.fft_size,fft_vector=args.fft_vector)
        if args.case=='mdct':
            evidence.update(mdct_size=args.mdct_size,mdct_stride=args.mdct_stride,mdct_vector=args.mdct_vector,mdct_frames=args.mdct_frames)
        if args.case=='vorbis_mdct':
            evidence.update(vorbis_size=args.vorbis_size,vorbis_vector=args.vorbis_vector)
        evidence.update(step_limit=args.max_steps,mailbox=mailbox)
        evidence.update(case=args.case, optimization=args.opt, diagnostics=result.stderr.splitlines(),
                        compiler=CC, physical_hardware=False)
        (BUILD/(args.label+'-'+stem+'.json')).write_text(json.dumps(evidence, indent=2)+'\n')
    print(result.stdout+result.stderr, end='')
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    main()
