; SPDX-License-Identifier: BSD-2-Clause
target datalayout = "E-m:e-P1-p0:16:16:16-p1:32:32:32-i1:16:16-i8:16:16-i16:16:16-i32:32:32-a:0:32-n16:40"
target triple = "teak"
%record = type {i16,i32}
@pointer_values = global [9 x i16] [i16 4660,i16 9029,i16 13398,i16 17767,i16 22136,i16 26505,i16 30874,i16 35243,i16 39612],align 2
@pointer_anchor = alias i16,i16* getelementptr ([9 x i16],[9 x i16]* @pointer_values,i16 0,i16 4)
@pointer_table = constant [6 x i16*] [
i16* getelementptr ([9 x i16],[9 x i16]* @pointer_values,i16 0,i16 0),
i16* getelementptr ([9 x i16],[9 x i16]* @pointer_values,i16 0,i16 1),
i16* getelementptr ([9 x i16],[9 x i16]* @pointer_values,i16 0,i16 3),
i16* getelementptr ([9 x i16],[9 x i16]* @pointer_values,i16 0,i16 8),
i16* getelementptr (i16,i16* @pointer_anchor,i16 -1),
i16* getelementptr (i16,i16* @pointer_anchor,i16 -4)],align 2
@pointer_records = global [2 x %record] [%record {i16 9029,i32 305419896},%record {i16 13398,i32 2309737967}],align 4
@record_table = constant [2 x i32*] [
i32* getelementptr ([2 x %record],[2 x %record]* @pointer_records,i16 0,i16 0,i32 1),
i32* getelementptr ([2 x %record],[2 x %record]* @pointer_records,i16 0,i16 1,i32 1)],align 2
