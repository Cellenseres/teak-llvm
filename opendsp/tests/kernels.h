/* SPDX-License-Identifier: BSD-2-Clause */
#pragma once
typedef unsigned short u16;
typedef signed short s16;
typedef unsigned int u32;
typedef signed int s32;
void vorbis_coupling_words(u16 *m, u16 *a, u16 count);
void opus_inner_product(const s16 *x, const s16 *y, u16 count, u16 *result);
